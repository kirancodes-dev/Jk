from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, revoke_token, decode_access_token
)
from backend.app.models.models import (
    User, Citizen, Student, University, Faculty, IndustryPartner, UserRole, RevokedToken
)
from backend.app.schemas.schemas import (
    Token, LoginRequest, UserCreate, UserOut, ForgotPasswordRequest, ResetPasswordRequest,
    RefreshTokenRequest, LogoutRequest, VerifyOTPRequest
)
from backend.app.routers.deps import get_current_user
from backend.app.services.email_service import email_service

# Track failed login attempts: {email: {"count": int, "locked_until": datetime}}
_failed_attempts: Dict[str, Dict] = {}

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    clean_email = payload.email.lower().strip()
    now = datetime.now(timezone.utc)
    attempt_record = _failed_attempts.get(clean_email)
    if attempt_record and attempt_record.get("locked_until") and now < attempt_record["locked_until"]:
        remaining_secs = int((attempt_record["locked_until"] - now).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to repeated failed login attempts. Please try again in {remaining_secs} seconds."
        )

    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        if not attempt_record:
            _failed_attempts[clean_email] = {"count": 1, "locked_until": None}
        else:
            attempt_record["count"] += 1
            if attempt_record["count"] >= 5:
                attempt_record["locked_until"] = now + timedelta(minutes=10)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Successful password check - clear failed attempts
    _failed_attempts.pop(clean_email, None)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    # 1. Role validation: prevent frontend role tampering
    if payload.role is not None and user.role != payload.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unauthorized role: Your account is registered as {user.role.value}, not {payload.role.value}."
        )

    # 2. Resolve user's university affiliation
    user_univ_id = None
    user_univ_name = None

    if user.role == UserRole.UNIVERSITY:
        univ = db.query(University).filter(University.user_id == user.id).first()
        if univ:
            user_univ_id = univ.id
            user_univ_name = univ.institution_name
    elif user.role == UserRole.FACULTY_MENTOR:
        fac = db.query(Faculty).filter(Faculty.user_id == user.id).first()
        if fac:
            user_univ_id = fac.university_id
            if fac.university:
                user_univ_name = fac.university.institution_name
            else:
                u = db.query(University).filter(University.id == fac.university_id).first()
                if u:
                    user_univ_name = u.institution_name
    elif user.role == UserRole.STUDENT:
        stu = db.query(Student).filter(Student.user_id == user.id).first()
        if stu:
            user_univ_id = stu.university_id
            if stu.university:
                user_univ_name = stu.university.institution_name
            else:
                u = db.query(University).filter(University.id == stu.university_id).first()
                if u:
                    user_univ_name = u.institution_name

    # 3. University affiliation validation: prevent cross-university or invalid university login
    if payload.university_id is not None:
        if user.role not in [UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.STUDENT]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {user.role.value} accounts cannot authenticate under a university organization."
            )
        if user_univ_id != payload.university_id:
            target_univ = db.query(University).filter(University.id == payload.university_id).first()
            target_name = target_univ.institution_name if target_univ else f"University #{payload.university_id}"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"University mismatch: Account is not affiliated with {target_name}."
            )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=user.id,
        role=user.role.value,
        expires_delta=access_token_expires,
        university_id=user_univ_id
    )
    refresh_token = create_refresh_token(subject=user.id, role=user.role.value)
    return Token(
        access_token=token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        university_id=user_univ_id,
        university_name=user_univ_name
    )

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email_clean = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
        
    user = User(
        email=email_clean,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        role=payload.role,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create role-specific profile
    if payload.role == UserRole.CITIZEN:
        db.add(Citizen(
            user_id=user.id,
            district_name=payload.district_name or "Ranchi",
            address=f"{payload.district_name}, Jharkhand"
        ))
    elif payload.role == UserRole.STUDENT:
        # Default to first university if not provided
        first_univ = db.query(University).first()
        univ_id = first_univ.id if first_univ else 1
        db.add(Student(
            user_id=user.id,
            university_id=univ_id,
            skills=payload.skills or "Python, Flutter, Problem Solving"
        ))
    elif payload.role == UserRole.FACULTY_MENTOR:
        first_univ = db.query(University).first()
        univ_id = first_univ.id if first_univ else 1
        db.add(Faculty(
            user_id=user.id,
            university_id=univ_id,
            designation="Assistant Professor",
            expertise=payload.expertise or "Engineering & Technology"
        ))
    elif payload.role == UserRole.INDUSTRY:
        db.add(IndustryPartner(
            user_id=user.id,
            company_name=payload.company_name or payload.full_name,
            industry_domain="Technology & CSR"
        ))
    elif payload.role == UserRole.UNIVERSITY:
        db.add(University(
            user_id=user.id,
            institution_name=payload.institution_name or payload.full_name,
            district_name=payload.district_name or "Ranchi"
        ))
    db.commit()
    
    token = create_access_token(
        subject=user.id,
        role=user.role.value,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(subject=user.id, role=user.role.value)
    return Token(
        access_token=token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email
    )

@router.post("/refresh", response_model=Token)
def refresh_token_endpoint(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Rotate refresh token: validates existing refresh token and issues new access + refresh token pair."""
    token_data = decode_access_token(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = token_data.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Revoke used refresh token (rotation)
    revoke_token(payload.refresh_token)
    old_jti = token_data.get("jti")
    if old_jti:
        db.add(RevokedToken(
            jti=old_jti,
            expires_at=datetime.fromtimestamp(token_data.get("exp", 0), tz=timezone.utc)
        ))
        db.commit()

    # Determine university if applicable
    user_univ_id = None
    user_univ_name = None
    if user.role == UserRole.UNIVERSITY and user.university_profile:
        user_univ_id = user.university_profile.id
        user_univ_name = user.university_profile.institution_name
    elif user.role == UserRole.FACULTY_MENTOR and user.faculty_profile:
        user_univ_id = user.faculty_profile.university_id
        user_univ_name = user.faculty_profile.university.institution_name if user.faculty_profile.university else None
    elif user.role == UserRole.STUDENT and user.student_profile:
        user_univ_id = user.student_profile.university_id
        user_univ_name = user.student_profile.university.institution_name if user.student_profile.university else None

    new_access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        university_id=user_univ_id
    )
    new_refresh_token = create_refresh_token(subject=user.id, role=user.role.value)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        university_id=user_univ_id,
        university_name=user_univ_name
    )

@router.post("/logout")
def logout(
    request: Request,
    payload: Optional[LogoutRequest] = None,
    db: Session = Depends(get_db)
):
    """Revoke JWT access/refresh token to terminate session."""
    token_to_revoke = None
    if payload and payload.token:
        token_to_revoke = payload.token
    else:
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            token_to_revoke = authorization.split(" ")[1]

    if token_to_revoke:
        revoke_token(token_to_revoke)
        payload_data = decode_access_token(token_to_revoke)
        if payload_data and payload_data.get("jti"):
            db.add(RevokedToken(
                jti=payload_data["jti"],
                expires_at=datetime.fromtimestamp(payload_data.get("exp", 0), tz=timezone.utc)
            ))
            db.commit()

    return {"status": "success", "message": "Successfully logged out. Token revoked."}

@router.post("/verify-otp")
def verify_otp(
    payload: Optional[VerifyOTPRequest] = None,
    email: Optional[str] = None,
    otp: Optional[str] = None
):
    target_email = payload.email if payload else email
    target_otp = payload.otp if payload else otp
    if not target_email or not target_otp:
        raise HTTPException(status_code=400, detail="Email and OTP are required")
    if email_service.verify_otp(target_email, target_otp):
        return {"status": "success", "message": "OTP verified successfully"}
    raise HTTPException(status_code=400, detail="Invalid or expired OTP code. Please try again.")

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    clean_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    
    # Generate real 6-digit OTP
    otp = email_service.generate_otp(clean_email)
    user_name = user.full_name if user else None
    
    # Dispatch real email via Gmail SMTP
    sent = email_service.send_otp_email(clean_email, otp, user_name)
    
    if not user:
        # Avoid user enumeration for security
        return {"status": "success", "message": "If the email is registered, a 6-digit OTP has been sent."}

    return {
        "status": "success",
        "message": f"A secure 6-digit OTP has been sent to {clean_email}.",
        "email_sent": sent
    }

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    clean_email = payload.email.lower().strip()
    if not email_service.verify_otp(clean_email, payload.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code. Please request a new code.")

    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "success", "message": "Password reset successfully. You can now log in with your new password."}

@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

