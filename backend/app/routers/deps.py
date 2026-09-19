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
