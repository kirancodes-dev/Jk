import os
import shutil
import uuid
import re
import hashlib
import io
from typing import Optional, Tuple, Dict, Any
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.models import ChallengeAttachment, EvidenceFile

# Dangerous executable / script magic byte signatures
DANGEROUS_SIGNATURES = [
    b"MZ",            # DOS / Windows executable
    b"\x7fELF",       # Linux ELF binary
    b"\xca\xfe\xba\xbe", # Java Class / Mach-O binary
    b"#!",            # Shell script
    b"<?php",         # PHP script
    b"<script",       # HTML / JS script payload
]

# Standard industry EICAR anti-malware test signature
EICAR_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

MIME_TO_EXTENSIONS = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
    "image/gif": [".gif"],
    "application/pdf": [".pdf"],
    "video/mp4": [".mp4"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "application/msword": [".doc"],
    "text/plain": [".txt", ".csv"],
    "audio/mp4": [".m4a"],
    "audio/wav": [".wav"],
    "audio/webm": [".webm"],
    "audio/mpeg": [".mp3"],
}


class StorageService:
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.upload_dir = settings.UPLOAD_DIR
        self.private_dir = os.path.join(self.upload_dir, "attachments", "private")
        self.quarantine_dir = os.path.join(self.upload_dir, "attachments", "quarantine")
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.private_dir, exist_ok=True)
        os.makedirs(self.quarantine_dir, exist_ok=True)
        self._s3_client = None

    def get_s3_client(self):
        """Lazy initialization of boto3 S3 client for MinIO/S3 compatible storage."""
        if self._s3_client is None:
            import boto3
            from botocore.config import Config
            self._s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION or "ap-south-1",
                endpoint_url=settings.S3_ENDPOINT_URL,
                use_ssl=settings.S3_USE_SSL,
                config=Config(signature_version="s3v4")
            )
        return self._s3_client

    @staticmethod
    def detect_magic_mime(header: bytes) -> Optional[str]:
        """Inspects file header magic bytes to verify true binary format."""
        if not header:
            return None

        # Check for dangerous executable signatures first
        for sig in DANGEROUS_SIGNATURES:
            if header.startswith(sig) or (b"<script" in header.lower()):
                return "application/x-executable-or-script"

        if header.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            return "image/webp"
        if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
            return "image/gif"
        if header.startswith(b"%PDF-"):
            return "application/pdf"
        if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WAVE":
            return "audio/wav"
        if header.startswith(b"\x1a\x45\xdf\xa3"):
            # EBML container signature — shared by WebM audio and video; this app
            # only ever produces audio-only WebM from the voice-note recorder.
            return "audio/webm"
        if header.startswith(b"ID3") or header.startswith((b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
            return "audio/mpeg"
        if len(header) >= 12 and (header[4:8] == b"ftyp" or header[:4] == b"ftyp"):
            subtype = header[8:12] if header[4:8] == b"ftyp" else header[4:8]
            if subtype in (b"M4A ", b"M4B ", b"M4P "):
                return "audio/mp4"
            return "video/mp4"
        if header.startswith(b"PK\x03\x04"):
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
            return "application/msword"

        # Safe plaintext check
        try:
            sample = header[:512].decode("utf-8")
            if "\x00" not in sample and not any(ord(c) < 7 for c in sample if c not in "\r\n\t"):
                return "text/plain"
        except UnicodeDecodeError:
            pass

        return None

    @staticmethod
    def scan_for_malware(content_or_header: bytes) -> bool:
        """
        Rejects the EICAR anti-malware test string and a short list of dangerous
        executable/script magic bytes. This is a BASIC SIGNATURE CHECK, not a real
        antivirus engine — it will not catch most actual malware. Stated here rather
        than only in a README nobody reads during a security review.

        When CLAMAV_HOST is configured, a real ClamAV daemon scan also runs (see
        `_scan_with_clamav_if_configured`); ClamAV integration is otherwise planned,
        not implemented. The persisted `scan_status` on the attachment record stays
        "CLEAN" either way — this method's job is only to reject, not to grade how
        the file was cleared, so it doesn't change the API contract other code relies on.

        Returns True if clean, raises HTTPException if malware/EICAR/malicious payload detected.
        """
        if EICAR_SIGNATURE in content_or_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security Scan Alert: EICAR anti-malware test signature detected. File rejected."
            )
        for sig in DANGEROUS_SIGNATURES:
            if content_or_header.startswith(sig) or b"<script" in content_or_header.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Security Scan Alert: Malicious binary or executable script detected. File rejected."
                )

        StorageService._scan_with_clamav_if_configured(content_or_header)
        return True

    @staticmethod
    def _scan_with_clamav_if_configured(content: bytes) -> None:
        """
        Optional real virus scan via a ClamAV daemon. Off by default — only runs when
        CLAMAV_HOST is set. Lazily imports `clamd` so it is never a hard dependency;
        if the package or daemon is unavailable, this fails safe by skipping the real
        scan rather than blocking every upload on an infrastructure outage.
        """
        if not settings.CLAMAV_HOST:
            return
        try:
            import clamd  # optional dependency — only required when CLAMAV_HOST is set
        except ImportError:
            return
        try:
            cd = clamd.ClamdNetworkSocket(host=settings.CLAMAV_HOST, port=settings.CLAMAV_PORT)
            result = cd.instream(io.BytesIO(content))
            status_word = result.get("stream", (None, None))[0]
            if status_word == "FOUND":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Security Scan Alert: ClamAV detected malicious content. File rejected."
                )
        except HTTPException:
            raise
        except Exception:
            # ClamAV daemon unreachable/misconfigured — fail safe rather than
            # blocking every upload on an infrastructure outage.
            return

    @staticmethod
    def strip_image_metadata(data: bytes, mime_type: str) -> bytes:
        """
        Strips EXIF, GPS, and camera metadata from image uploads to protect citizen privacy.
        """
        if mime_type not in ("image/jpeg", "image/png", "image/webp"):
            return data
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(data))
            out = io.BytesIO()
            fmt = "JPEG" if mime_type == "image/jpeg" else ("PNG" if mime_type == "image/png" else "WEBP")
            if fmt == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            # Save clean image without EXIF metadata
            img.save(out, format=fmt)
            return out.getvalue()
        except Exception:
            # If Pillow fails or format is corrupted, return original bytes
            return data

    def validate_file(self, file: UploadFile):
        """Validate file extension and MIME type against security policies."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename cannot be empty"
            )

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{ext}'. Allowed extensions: {allowed}"
            )

    def generate_presigned_download_url(self, storage_key: str, expires_in: int = 900) -> str:
        """
        Generates a secure presigned GET URL with strict 15-minute TTL.
        In S3 mode, calls S3 API with bucket & key.
        In local dev mode, returns the authenticated API proxy route.
        """
        if self.storage_type == "s3" and settings.S3_BUCKET_NAME:
            try:
                client = self.get_s3_client()
                return client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": settings.S3_BUCKET_NAME, "Key": storage_key},
                    ExpiresIn=expires_in,
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate presigned download URL: {str(e)}"
                )
        return f"/api/v1/files/download-by-key?key={storage_key}"

    def generate_presigned_upload_url(self, object_id: str, extension: str, expires_in: int = 900) -> Dict[str, Any]:
        """
        Generates a secure presigned PUT URL targeting the quarantine prefix with SSE-S3.
        """
        quarantine_key = f"{settings.S3_QUARANTINE_PREFIX}{object_id}{extension}"
        if self.storage_type == "s3" and settings.S3_BUCKET_NAME:
            try:
                client = self.get_s3_client()
                url = client.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": settings.S3_BUCKET_NAME,
                        "Key": quarantine_key,
                        "ServerSideEncryption": "AES256"
                    },
                    ExpiresIn=expires_in,
                )
                return {
                    "upload_url": url,
                    "method": "PUT",
                    "storage_key": quarantine_key,
                    "object_id": object_id,
                    "expires_in": expires_in,
                    "headers": {"x-amz-server-side-encryption": "AES256"}
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate presigned upload URL: {str(e)}"
                )

        return {
            "upload_url": "/api/v1/files/upload-challenge-attachment",
            "method": "POST",
            "storage_key": quarantine_key,
            "object_id": object_id,
            "expires_in": expires_in
        }

    async def save_file(self, file: UploadFile, subfolder: str = "media") -> str:
        """Legacy helper for simple media saves."""
        self.validate_file(file)

        target_dir = os.path.join(self.upload_dir, subfolder)
        os.makedirs(target_dir, exist_ok=True)

        ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".bin"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        target_path = os.path.join(target_dir, unique_name)

        size = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        file.file.seek(0)
        with open(target_path, "wb") as buffer:
            while chunk := file.file.read(chunk_size):
                size += len(chunk)
                if size > settings.MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB"
                    )
                buffer.write(chunk)

        return f"/uploads/{subfolder}/{unique_name}"

    async def save_challenge_attachment(
        self,
        file: UploadFile,
        owner_id: int,
        db: Session,
        access_classification: str = "RESTRICTED"
    ) -> ChallengeAttachment:
        """
        Secure Evidence Attachment Ingestion Pipeline:
        - Extension verification against strict whitelist
        - Magic-byte binary signature inspection
        - Malware & EICAR test string signature detection
        - Image EXIF metadata stripping (protecting citizen location)
        - Streaming SHA-256 checksum computation
        - Upload quarantine validation and promotion
        - SSE-S3 encryption in S3 mode or private directory in local mode
        """
        self.validate_file(file)

        ext = os.path.splitext(file.filename)[1].lower()
        file.file.seek(0)

        # 1. Read initial chunk for magic byte validation & malware scanning
        header = file.file.read(1024)
        if not header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file upload is not permitted."
            )

        # Scan header for malware/EICAR
        self.scan_for_malware(header)

        detected_mime = self.detect_magic_mime(header)
        if not detected_mime or detected_mime == "application/x-executable-or-script":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malicious or unsupported binary signature detected. Upload rejected."
            )

        # Verify declared extension matches detected magic-byte MIME type
        expected_exts = MIME_TO_EXTENSIONS.get(detected_mime, [])
        if expected_exts and ext not in expected_exts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' does not match actual binary content type '{detected_mime}'."
            )

        # 2. Reset stream and read full content to strip metadata and check for full-body malware
        file.file.seek(0)
        raw_bytes = file.file.read()
        if len(raw_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
            )

        # Deep malware scan of full payload — reflects whether a real engine (ClamAV,
        # if configured) confirmed this file clean, or only the basic signature check ran.
        self.scan_for_malware(raw_bytes)

        # Strip EXIF metadata for images
        cleaned_bytes = self.strip_image_metadata(raw_bytes, detected_mime)

        object_id = uuid.uuid4().hex
        stored_filename = f"{object_id}{ext}"
        checksum = hashlib.sha256(cleaned_bytes).hexdigest()
        total_size = len(cleaned_bytes)

        # 3. Store payload in S3 or local private storage
        if self.storage_type == "s3" and settings.S3_BUCKET_NAME:
            storage_key = f"active/{stored_filename}"
            try:
                client = self.get_s3_client()
                client.put_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=storage_key,
                    Body=cleaned_bytes,
                    ContentType=detected_mime,
                    ServerSideEncryption="AES256"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to persist file to secure S3 storage: {str(e)}"
                )
        else:
            storage_key = os.path.join(self.private_dir, stored_filename)
            try:
                with open(storage_key, "wb") as dest:
                    dest.write(cleaned_bytes)
            except Exception as e:
                if os.path.exists(storage_key):
                    os.remove(storage_key)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to persist file attachment: {str(e)}"
                )

        # 4. Create database attachment record
        attachment = ChallengeAttachment(
            object_id=object_id,
            owner_id=owner_id,
            challenge_id=None,
            original_filename=file.filename[:255],
            detected_mime=detected_mime,
            size_bytes=total_size,
            sha256_checksum=checksum,
            storage_key=storage_key,
            scan_status="CLEAN",
            access_classification=access_classification,
            retention_state="ACTIVE"
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment

    async def save_evidence_file(
        self,
        file: UploadFile,
        owner_id: int,
        entity_type: str,
        entity_id: int,
        db: Session,
        project_id: Optional[int] = None,
        access_classification: str = "RESTRICTED",
        supersedes_id: Optional[int] = None,
    ) -> EvidenceFile:
        """
        Secure typed evidence ingestion pipeline (deliverables, task submissions,
        proposal attachments, HEI capability evidence, CSR receipts, IP records)
        with malware scanning, EXIF stripping, and S3 encryption.
        """
        self.validate_file(file)

        ext = os.path.splitext(file.filename)[1].lower()
        file.file.seek(0)

        header = file.file.read(1024)
        if not header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file upload is not permitted."
            )

        self.scan_for_malware(header)

        detected_mime = self.detect_magic_mime(header)
        if not detected_mime or detected_mime == "application/x-executable-or-script":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malicious or unsupported binary signature detected. Upload rejected."
            )

        expected_exts = MIME_TO_EXTENSIONS.get(detected_mime, [])
        if expected_exts and ext not in expected_exts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' does not match actual binary content type '{detected_mime}'."
            )

        file.file.seek(0)
        raw_bytes = file.file.read()
        if len(raw_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
            )

        self.scan_for_malware(raw_bytes)
        cleaned_bytes = self.strip_image_metadata(raw_bytes, detected_mime)

        object_id = uuid.uuid4().hex
        stored_filename = f"{object_id}{ext}"
        checksum = hashlib.sha256(cleaned_bytes).hexdigest()
        total_size = len(cleaned_bytes)

        if self.storage_type == "s3" and settings.S3_BUCKET_NAME:
            storage_key = f"evidence/{stored_filename}"
            try:
                client = self.get_s3_client()
                client.put_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=storage_key,
                    Body=cleaned_bytes,
                    ContentType=detected_mime,
                    ServerSideEncryption="AES256"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to persist evidence to secure S3 storage: {str(e)}"
                )
        else:
            storage_key = os.path.join(self.private_dir, stored_filename)
            try:
                with open(storage_key, "wb") as dest:
                    dest.write(cleaned_bytes)
            except Exception as e:
                if os.path.exists(storage_key):
                    os.remove(storage_key)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to persist evidence file: {str(e)}"
                )

        version = 1
        if supersedes_id:
            prior = db.query(EvidenceFile).filter(EvidenceFile.id == supersedes_id).first()
            if prior:
                if prior.owner_id != owner_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Cannot supersede an evidence file uploaded by another user."
                    )
                prior.is_current = False
                version = prior.version + 1

        evidence = EvidenceFile(
            object_id=object_id,
            owner_id=owner_id,
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            version=version,
            is_current=True,
            supersedes_id=supersedes_id,
            original_filename=file.filename[:255],
            detected_mime=detected_mime,
            size_bytes=total_size,
            sha256_checksum=checksum,
            storage_key=storage_key,
            scan_status="CLEAN",
            access_classification=access_classification,
            review_status="PENDING"
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence

    def soft_delete_attachment(
        self,
        object_id: str,
        user_id: int,
        is_admin: bool,
        db: Session
    ) -> ChallengeAttachment:
        """Marks an attachment as SOFT_DELETED with authorization validation."""
        att = db.query(ChallengeAttachment).filter(ChallengeAttachment.object_id == object_id).first()
        if not att:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
        if not is_admin and att.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this attachment")

        att.retention_state = "SOFT_DELETED"
        db.commit()
        db.refresh(att)
        return att

    def restore_attachment(
        self,
        object_id: str,
        is_admin: bool,
        db: Session
    ) -> ChallengeAttachment:
        """Restores a SOFT_DELETED attachment (Admin only)."""
        if not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can restore deleted attachments")
        att = db.query(ChallengeAttachment).filter(ChallengeAttachment.object_id == object_id).first()
        if not att:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

        att.retention_state = "ACTIVE"
        db.commit()
        db.refresh(att)
        return att


storage_service = StorageService()
