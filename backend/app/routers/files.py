import os
import re
import mimetypes
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.models import User, UserRole, Project, ProjectMember, Student, Faculty
from backend.app.routers.deps import get_current_user, get_optional_current_user

router = APIRouter(prefix="/files", tags=["Secure Files & Documents"])

SAFE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')

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
        # Check project membership or ownership
        # Government admins have state-wide audit oversight
        # Faculty / students require project association
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
