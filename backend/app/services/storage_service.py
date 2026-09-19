import os
import shutil
import uuid
import re
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from backend.app.core.config import settings

class StorageService:
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir, exist_ok=True)

    def validate_file(self, file: UploadFile):
        """Validate file extension and MIME type against security policies."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename cannot be empty"
            )

        # Sanitize extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{ext}'. Allowed extensions: {allowed}"
            )

        # Validate MIME type if provided
        if file.content_type and file.content_type not in settings.ALLOWED_MIME_TYPES:
            # Allow common binary/generic if extension matches, else enforce
            if file.content_type not in ["application/octet-stream", "binary/octet-stream"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Disallowed MIME type '{file.content_type}'."
                )

    async def save_file(self, file: UploadFile, subfolder: str = "media") -> str:
        # 1. Security validation
        self.validate_file(file)

        target_dir = os.path.join(self.upload_dir, subfolder)
        os.makedirs(target_dir, exist_ok=True)

        ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".bin"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        target_path = os.path.join(target_dir, unique_name)

        # 2. Check file size during streaming
        size = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        file.file.seek(0)
        if self.storage_type == "s3" and settings.AWS_ACCESS_KEY_ID:
            try:
                import boto3
                s3 = boto3.client(
                    "s3",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                s3.upload_fileobj(file.file, settings.S3_BUCKET_NAME, f"{subfolder}/{unique_name}")
                return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{subfolder}/{unique_name}"
            except Exception:
                # Graceful fallback to local storage
                file.file.seek(0)

        # Local storage with size enforcement
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

storage_service = StorageService()
