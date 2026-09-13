from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.models.models import User, Citizen, Student, University, Faculty, IndustryPartner, UserRole
from backend.app.schemas.schemas import (
    Token, LoginRequest, UserCreate, UserOut, ForgotPasswordRequest, ResetPasswordRequest
)
from backend.app.routers.deps import get_current_user
from backend.app.services.email_service import email_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=user.id,
        role=user.role.value,
        expires_delta=access_token_expires
    )
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email
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
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email
    )

@router.post("/verify-otp")
def verify_otp(email: str, otp: str):
    if email_service.verify_otp(email, otp):
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
