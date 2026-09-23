import os
import re
import mimetypes
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.models import (
    User, UserRole, Project, ProjectMember, Student, Faculty, University,
    ChallengeAttachment, Challenge, EvidenceFile
)
from backend.app.routers.deps import get_current_user, get_optional_current_user, verify_project_membership
from backend.app.services.storage_service import storage_service

router = APIRouter(prefix="/files", tags=["Secure Files & Documents"])

SAFE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')


@router.get("/attachments/{object_id}")
def get_secure_attachment(
    object_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Secure challenge evidence attachment access with object-level authorization:
    - Author / uploader access
    - Statewide government admin oversight
    - Scoped jurisdiction review for local government officers & PRIs
    - Rejection of unauthorized users attempting to access private citizen evidence
    """
    attachment = db.query(ChallengeAttachment).filter(ChallengeAttachment.object_id == object_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence attachment not found."
        )

    if attachment.retention_state == "SOFT_DELETED" and current_user.role != UserRole.GOVERNMENT_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence attachment has been deleted or archived."
        )

    # Authorization Check
    has_access = False
    if attachment.owner_id == current_user.id or current_user.role == UserRole.GOVERNMENT_ADMIN:
        has_access = True
    elif attachment.challenge_id:
        ch = db.query(Challenge).filter(Challenge.id == attachment.challenge_id).first()
        if ch and current_user.role in (UserRole.GOVERNMENT_OFFICER, UserRole.PRI, UserRole.ULB):
            if current_user.admin_tier == "STATE" or (
                current_user.district_name and ch.location and 
                current_user.district_name.lower() == ch.location.district_name.lower()
            ):
                has_access = True
        elif ch and attachment.access_classification == "PUBLIC":
            has_access = True

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have authorization to view this private evidence attachment."
        )

    if not os.path.isfile(attachment.storage_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical attachment file missing on server."
        )

    return FileResponse(
        attachment.storage_key,
        media_type=attachment.detected_mime,
        filename=attachment.original_filename,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=3600",
            "X-Checksum-SHA256": attachment.sha256_checksum
        }
    )


@router.get("/evidence/{object_id}")
def get_evidence_file(
    object_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Secure typed evidence access (milestone deliverables, task submissions, proposal
    attachments, HEI capability evidence, CSR receipts, IP records).
    Enforces project-team object-level authorization so a team member on one project
    cannot read another project's evidence.
    """
    evidence = db.query(EvidenceFile).filter(EvidenceFile.object_id == object_id).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found.")

    has_access = evidence.owner_id == current_user.id or current_user.role == UserRole.GOVERNMENT_ADMIN
    if not has_access and evidence.project_id:
        try:
            verify_project_membership(project_id=evidence.project_id, current_user=current_user, db=db)
            has_access = True
        except HTTPException:
            has_access = False
    elif not has_access and not evidence.project_id:
        # University-level capability evidence: visible to government reviewers and the owning HEI
        if current_user.role in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER):
            has_access = True
        elif current_user.role == UserRole.UNIVERSITY:
            univ = db.query(University).filter(University.user_id == current_user.id).first()
            if univ and evidence.entity_type == "UNIVERSITY_CAPABILITY" and evidence.entity_id == univ.id:
                has_access = True

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have authorization to view this evidence file."
        )

    if not os.path.isfile(evidence.storage_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical evidence file missing on server.")

    return FileResponse(
        evidence.storage_key,
        media_type=evidence.detected_mime,
        filename=evidence.original_filename,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=3600",
            "X-Checksum-SHA256": evidence.sha256_checksum,
            "X-Evidence-Version": str(evidence.version)
        }
    )


@router.get("/{subfolder}/{filename}")
def get_secure_file(
    subfolder: str,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Secure file streaming with authentication, strict path traversal defense,
    extension whitelisting, and object-level authorization for sensitive documents.
    """
    # 1. Path Traversal & Name Sanitization Check
    if not SAFE_NAME_PATTERN.match(filename) or not SAFE_NAME_PATTERN.match(subfolder):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file or folder name: Special path traversal characters are forbidden."
        )

    if ".." in subfolder or ".." in filename or "/" in filename or "\\" in filename or "\x00" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal attempt blocked."
        )

    # 2. Canonical Path Resolution
    upload_root = os.path.abspath(settings.UPLOAD_DIR)
    target_path = os.path.abspath(os.path.join(upload_root, subfolder, filename))

    # Verify that resolved path is strictly within upload directory
    if os.path.commonpath([upload_root, target_path]) != upload_root:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Path outside upload root."
        )

    if not os.path.isfile(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested file does not exist."
        )

    # 3. Extension Validation
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: File type not permitted."
        )

    # 4. Object-Level Access Control for Sensitive Documents
    is_sensitive = subfolder in ["submissions", "tasks", "evidence", "confidential", "internal"]
    if is_sensitive and current_user.role != UserRole.GOVERNMENT_ADMIN:
        has_access = False
        if current_user.role == UserRole.FACULTY_MENTOR:
            fac = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
            if fac:
                has_access = True
        elif current_user.role == UserRole.STUDENT:
            stu = db.query(Student).filter(Student.user_id == current_user.id).first()
            if stu:
                has_access = True
        elif current_user.role == UserRole.UNIVERSITY:
            has_access = True

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You do not have authorization to access this confidential document."
            )

    media_type, _ = mimetypes.guess_type(target_path)
    if not media_type:
        media_type = "application/octet-stream"

    return FileResponse(
        target_path,
        media_type=media_type,
        filename=filename,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=3600"
        }
    )


@router.delete("/attachments/{object_id}")
def soft_delete_attachment(
    object_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft-deletes an attachment (owner or government admin only)."""
    is_admin = current_user.role == UserRole.GOVERNMENT_ADMIN
    att = storage_service.soft_delete_attachment(
        object_id=object_id,
        user_id=current_user.id,
        is_admin=is_admin,
        db=db
    )
    return {
        "status": "success",
        "message": "Attachment soft-deleted successfully.",
        "object_id": att.object_id,
        "retention_state": att.retention_state
    }


@router.post("/attachments/{object_id}/restore")
def restore_attachment(
    object_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restores a soft-deleted attachment (government admin only)."""
    is_admin = current_user.role == UserRole.GOVERNMENT_ADMIN
    att = storage_service.restore_attachment(
        object_id=object_id,
        is_admin=is_admin,
        db=db
    )
    return {
        "status": "success",
        "message": "Attachment restored successfully.",
        "object_id": att.object_id,
        "retention_state": att.retention_state
    }


@router.get("/attachments/{object_id}/presigned-url")
def get_presigned_download_url(
    object_id: str,
    expires_in: int = Query(default=900, ge=60, le=3600),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates a secure authorized presigned download URL."""
    attachment = db.query(ChallengeAttachment).filter(ChallengeAttachment.object_id == object_id).first()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    if attachment.retention_state == "SOFT_DELETED" and current_user.role != UserRole.GOVERNMENT_ADMIN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment is deleted.")

    # Authorization Check
    has_access = False
    if attachment.owner_id == current_user.id or current_user.role == UserRole.GOVERNMENT_ADMIN:
        has_access = True
    elif attachment.challenge_id:
        ch = db.query(Challenge).filter(Challenge.id == attachment.challenge_id).first()
        if ch and current_user.role in (UserRole.GOVERNMENT_OFFICER, UserRole.PRI, UserRole.ULB):
            if current_user.admin_tier == "STATE" or (
                current_user.district_name and ch.location and
                current_user.district_name.lower() == ch.location.district_name.lower()
            ):
                has_access = True
        elif ch and attachment.access_classification == "PUBLIC":
            has_access = True

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have authorization to access this attachment."
        )

    url = storage_service.generate_presigned_download_url(
        storage_key=attachment.storage_key,
        expires_in=expires_in
    )
    return {
        "object_id": attachment.object_id,
        "filename": attachment.original_filename,
        "download_url": url,
        "expires_in": expires_in,
        "storage_type": settings.STORAGE_TYPE
    }


@router.post("/presigned-upload")
def get_presigned_upload_url(
    filename: str = Query(..., description="Original filename with extension"),
    current_user: User = Depends(get_current_user)
):
    """Generates an authorized presigned upload URL directly to the quarantine bucket with SSE-S3."""
    import uuid
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'."
        )

    object_id = uuid.uuid4().hex
    return storage_service.generate_presigned_upload_url(object_id=object_id, extension=ext)
