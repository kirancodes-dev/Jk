import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.security import (
    hash_sha256, create_access_token, create_refresh_token,
    decode_access_token
)
from backend.app.models.models import User, UserSession, RevokedToken, utc_now


class SessionService:
    @staticmethod
    def create_session(
        db: Session,
        user: User,
        refresh_token: str,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """Persists a new authenticated session with a hashed refresh token."""
        sid = session_id or uuid.uuid4().hex
        token_hash = hash_sha256(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        session_record = UserSession(
            user_id=user.id,
            session_id=sid,
            refresh_token_hash=token_hash,
            is_revoked=False,
            revoked_reason=None,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
            created_at=utc_now(),
            expires_at=expires_at,
            last_used_at=utc_now()
        )
        db.add(session_record)
        db.commit()
        db.refresh(session_record)
        return session_record

    @staticmethod
    def rotate_session(
        db: Session,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Validates refresh token against persistent database sessions.
        Enforces Refresh Token Rotation and Reuse Detection:
        If an already-rotated or revoked token is reused, all sessions in the token family
        are immediately invalidated as a security compromise mitigation.
        """
        payload = decode_access_token(refresh_token, verify_exp=False)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or malformed refresh token."
            )

        user_id_str = payload.get("sub")
        session_id = payload.get("session_id")
        token_jti = payload.get("jti")

        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject credentials."
            )

        user_id = int(user_id_str)
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found."
            )

        # Check if password change invalidated this token
        if user.password_changed_at and payload.get("iat"):
            try:
                iat_dt = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
                pwd_dt = user.password_changed_at
                if pwd_dt.tzinfo is None:
                    pwd_dt = pwd_dt.replace(tzinfo=timezone.utc)
                if iat_dt < pwd_dt.replace(microsecond=0):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Session invalidated due to recent password change. Please log in again."
                    )
            except (ValueError, OSError):
                pass

        token_hash = hash_sha256(refresh_token)

        # Look up session record
        session_record = None
        if session_id:
            session_record = db.query(UserSession).filter(UserSession.session_id == session_id).first()

        if not session_record:
            # Fallback lookup by token hash
            session_record = db.query(UserSession).filter(UserSession.refresh_token_hash == token_hash).first()

        if not session_record:
            # Check if token is in legacy RevokedToken table
            if token_jti:
                revoked_legacy = db.query(RevokedToken).filter(RevokedToken.jti == token_jti).first()
                if revoked_legacy:
                    # Token reuse detected!
                    SessionService.revoke_all_user_sessions(db, user.id, reason="REUSE_DETECTED_LEGACY")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token reuse detected. All sessions terminated for security. Please log in again."
                    )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found or expired. Please log in again."
            )

        # REUSE DETECTION: If session was already revoked/rotated
        if session_record.is_revoked:
            SessionService.revoke_all_user_sessions(db, user.id, reason="REUSE_DETECTED_FAMILY_COMPROMISED")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Security violation: Reused refresh token detected. All sessions have been terminated. Please log in again."
            )

        # Verify hash match
        if session_record.refresh_token_hash != token_hash:
            SessionService.revoke_all_user_sessions(db, user.id, reason="HASH_MISMATCH_SUSPECTED_TAMPERING")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session integrity error. Please log in again."
            )

        # Check expiration
        now_utc = datetime.now(timezone.utc)
        record_exp = session_record.expires_at
        if record_exp.tzinfo is None:
            record_exp = record_exp.replace(tzinfo=timezone.utc)

        if now_utc > record_exp:
            session_record.is_revoked = True
            session_record.revoked_reason = "EXPIRED"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh session has expired. Please log in again."
            )

        # Mark current session as rotated (single use completed)
        session_record.is_revoked = True
        session_record.revoked_reason = "ROTATED"
        session_record.last_used_at = utc_now()

        # Add JTI to RevokedToken for legacy blacklist compatibility
        if token_jti:
            db.add(RevokedToken(jti=token_jti, expires_at=record_exp))

        # Issue new rotated session
        new_session_id = uuid.uuid4().hex
        new_refresh_token = create_refresh_token(subject=user.id, role=user.role.value, session_id=new_session_id)
        new_token_hash = hash_sha256(new_refresh_token)
        new_expires_at = now_utc + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_session = UserSession(
            user_id=user.id,
            session_id=new_session_id,
            refresh_token_hash=new_token_hash,
            is_revoked=False,
            revoked_reason=None,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
            created_at=utc_now(),
            expires_at=new_expires_at,
            last_used_at=utc_now()
        )
        db.add(new_session)

        # Resolve university affiliation if applicable
        user_univ_id = None
        if user.university_profile:
            user_univ_id = user.university_profile.id
        elif user.faculty_profile:
            user_univ_id = user.faculty_profile.university_id
        elif user.student_profile:
            user_univ_id = user.student_profile.university_id

        new_access_token = create_access_token(
            subject=user.id,
            role=user.role.value,
            session_id=new_session_id,
            university_id=user_univ_id,
            tier=user.admin_tier,
            jurisdiction_name=user.jurisdiction_name,
            district_name=user.district_name,
            block_name=user.block_name,
            panchayat_name=user.panchayat_name
        )

        db.commit()
        return user, new_access_token, new_refresh_token

    @staticmethod
    def revoke_session(db: Session, session_id: str, reason: str = "LOGOUT") -> bool:
        """Revokes a specific session by its session ID."""
        session_record = db.query(UserSession).filter(UserSession.session_id == session_id).first()
        if session_record:
            session_record.is_revoked = True
            session_record.revoked_reason = reason
            session_record.last_used_at = utc_now()
            db.commit()
            return True
        return False

    @staticmethod
    def revoke_all_user_sessions(db: Session, user_id: int, reason: str = "LOGOUT_ALL") -> int:
        """Terminates all active sessions for a user across all devices/workers."""
        count = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_revoked == False
        ).update(
            {
                "is_revoked": True,
                "revoked_reason": reason,
                "last_used_at": utc_now()
            },
            synchronize_session=False
        )

        db.commit()
        return count

    @staticmethod
    def is_session_active(db: Session, session_id: str) -> bool:
        """Checks whether a session is valid and active in the database."""
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.is_revoked == False
        ).first()
        if not session:
            return False

        now_utc = datetime.now(timezone.utc)
        exp = session.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if now_utc > exp:
            session.is_revoked = True
            session.revoked_reason = "EXPIRED"
            db.commit()
            return False

        return True


session_service = SessionService()
