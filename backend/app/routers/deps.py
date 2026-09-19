from typing import List, Optional, Set
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token, is_token_revoked
from backend.app.models.models import User, UserRole, RevokedToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

# Standard role-to-permission mapping for strict RBAC
DEFAULT_ROLE_PERMISSIONS: dict[UserRole, Set[str]] = {
    UserRole.GOVERNMENT_ADMIN: {
        "*"  # Superuser all permissions
    },
    UserRole.CITIZEN: {
        "challenge:create", "challenge:read", "challenge:feedback", "profile:manage"
    },
    UserRole.UNIVERSITY: {
        "challenge:read", "challenge:adopt", "project:create", "project:manage",
        "milestone:approve", "team:manage", "profile:manage"
    },
    UserRole.FACULTY_MENTOR: {
        "challenge:read", "project:mentor", "milestone:submit", "milestone:approve",
        "task:assign", "deliverable:review", "profile:manage"
    },
    UserRole.STUDENT: {
        "challenge:read", "project:view", "milestone:submit", "task:complete",
        "deliverable:submit", "profile:manage"
    },
    UserRole.INDUSTRY: {
        "challenge:read", "project:view", "funding:propose", "collaboration:create",
        "mentorship:offer", "profile:manage"
    },
}

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired/revoked",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    jti = payload.get("jti")
    if jti:
        # Check in-memory fast revocation
        if is_token_revoked(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please log in again."
            )
        # Check DB persistent revocation if table exists
        try:
            revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
            if revoked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked. Please log in again."
                )
        except Exception:
            pass

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token credentials"
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with token not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    return user

def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user and user.is_active:
            return user
        return None
    except Exception:
        return None

def require_roles(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of [{', '.join([r.value for r in allowed_roles])}] role."
            )
        return current_user
    return role_checker

def require_permissions(required_permissions: List[str]):
    def permission_checker(current_user: User = Depends(get_current_user)):
        user_perms = DEFAULT_ROLE_PERMISSIONS.get(current_user.role, set())
        if "*" in user_perms:
            return current_user
        for req in required_permissions:
            if req not in user_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: Missing required permission '{req}'."
                )
        return current_user
    return permission_checker

def verify_project_membership(project_id: int, current_user: User, db: Session):
    """
    Enforces object-level authorization (IDOR prevention).
    Ensures that students, faculty, or universities can only access or modify
    projects they are officially assigned to.
    """
    from backend.app.models.models import Project, ProjectMember, Student, Faculty, University

    # Government administrators have state-wide oversight
    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        return True

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.UNIVERSITY:
        univ = db.query(University).filter(University.user_id == current_user.id).first()
        if univ and project.university_id == univ.id:
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: This project belongs to another academic institution."
        )

    if current_user.role == UserRole.FACULTY_MENTOR:
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if faculty and (project.faculty_mentor_id == faculty.id or project.university_id == faculty.university_id):
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not the assigned faculty mentor for this project."
        )

    if current_user.role == UserRole.STUDENT:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student:
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.student_id == student.id
            ).first()
            if is_member:
                return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not an assigned student team member for this project."
        )

    if current_user.role == UserRole.INDUSTRY:
        # Industry can view projects, but modifying milestones or tasks is restricted
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden: You do not have permission to access this project."
    )

def verify_challenge_ownership(challenge_id: int, current_user: User, db: Session):
    """
    Ensures that citizens can only modify or submit private feedback on challenges they created.
    """
    from backend.app.models.models import Challenge, Citizen

    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        return True

    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    citizen = db.query(Citizen).filter(Citizen.user_id == current_user.id).first()
    if citizen and challenge.citizen_id == citizen.id:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden: You are not the reporter of this challenge."
    )
