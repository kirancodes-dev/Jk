import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, revoke_token, decode_access_token,
    validate_password_strength
)
from backend.app.models.models import (
    User, Citizen, Student, University, Faculty, IndustryPartner, UserRole,
    AccountStatus, RevokedToken, UserSession, OrganizationProfile, PartnerType
)
from backend.app.schemas.schemas import (
    Token, LoginRequest, UserCreate, UserOut, ForgotPasswordRequest, ResetPasswordRequest,
    RefreshTokenRequest, LogoutRequest, VerifyOTPRequest
)
from backend.app.routers.deps import get_current_user
from backend.app.services.email_service import email_service
from backend.app.services.session_service import session_service
from backend.app.services.rate_limiter import rate_limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    client_ip = rate_limiter.get_client_ip(request)
    clean_email = payload.email.lower().strip()

    # Rate limiting: max 20 requests per IP per minute (relaxed in test/dev modes)
    max_reqs = 5000 if (settings.DEMO_MODE or settings.ENVIRONMENT in ("test", "development")) else 20
    rate_limiter.enforce(f"login:ip:{client_ip}", max_requests=max_reqs, window_seconds=60, action_name="login requests")

    # Check if account is temporarily locked out
    is_locked, remaining = rate_limiter.is_locked_out(f"login:acc:{clean_email}")
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to repeated failed login attempts. Please try again in {remaining} seconds."
        )

    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        is_locked_now, remaining_sec = rate_limiter.record_failure(f"login:acc:{clean_email}", max_failures=5, lockout_seconds=600)
        if is_locked_now:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account temporarily locked due to repeated failed login attempts. Please try again in {remaining_sec} seconds."
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Authentication succeeded: clear failure counter
    rate_limiter.clear_failure(f"login:acc:{clean_email}")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    if hasattr(user, "account_status") and str(user.account_status).upper() in ("SUSPENDED", "DEACTIVATED"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {str(user.account_status).lower()}."
        )

    # Role validation: prevent frontend role tampering
    if payload.role is not None and user.role != payload.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unauthorized role: Your account is registered as {user.role.value}, not {payload.role.value}."
        )

    # Resolve user's university affiliation
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

    # University affiliation validation
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

    session_id = uuid.uuid4().hex
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        session_id=session_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        university_id=user_univ_id,
        tier=user.admin_tier,
        jurisdiction_name=user.jurisdiction_name,
        district_name=user.district_name,
        block_name=user.block_name,
        panchayat_name=user.panchayat_name
    )
    refresh_token = create_refresh_token(subject=user.id, role=user.role.value, session_id=session_id)

    # Persist session record in database
    session_service.create_session(
        db=db,
        user=user,
        refresh_token=refresh_token,
        session_id=session_id,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent")
    )

    return Token(
        access_token=access_token,
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
def register(request: Request, payload: UserCreate, db: Session = Depends(get_db)):
    client_ip = rate_limiter.get_client_ip(request)
    # Rate limit registrations per IP
    rate_limiter.enforce(f"register:ip:{client_ip}", max_requests=10, window_seconds=3600, action_name="registrations")

    email_clean = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    # Password policy enforcement
    role_str = payload.role.value if hasattr(payload.role, "value") else str(payload.role)
    is_valid_pwd, pwd_error = validate_password_strength(payload.password, user_email=email_clean, role=role_str)
    if not is_valid_pwd:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=pwd_error)

    # Government officer/admin accounts are provisioned by an administrator only —
    # never self-registered, regardless of email domain.
    if payload.role in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Government officer and administrator accounts are provisioned by a department administrator and cannot be self-registered. Contact your nodal officer for account creation."
        )

    # Determine initial verification state
    # Citizens start active but institutional / government accounts require verification
    is_verified = (payload.role == UserRole.CITIZEN)
    acc_status = AccountStatus.ACTIVE if is_verified else AccountStatus.PENDING_VERIFICATION

    user = User(
        email=email_clean,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        role=payload.role,
        is_active=True,
        is_verified=is_verified,
        account_status=acc_status
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    user_univ_id = None
    user_univ_name = None

    # Create role-specific profile without demo fallbacks
    if payload.role == UserRole.CITIZEN:
        db.add(Citizen(
            user_id=user.id,
            district_name=payload.district_name or "Ranchi",
            address=f"{payload.district_name or 'Ranchi'}, Jharkhand"
        ))
    elif payload.role == UserRole.STUDENT:
        target_univ = None
        if payload.university_id:
            target_univ = db.query(University).filter(University.id == payload.university_id).first()
        if not target_univ:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student registration requires a valid university_id corresponding to an accredited institution."
            )
        user_univ_id = target_univ.id
        user_univ_name = target_univ.institution_name
        db.add(Student(
            user_id=user.id,
            university_id=target_univ.id,
            skills=payload.skills or "Python, Problem Solving"
        ))
    elif payload.role == UserRole.FACULTY_MENTOR:
        target_univ = None
        if payload.university_id:
            target_univ = db.query(University).filter(University.id == payload.university_id).first()
        if not target_univ:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Faculty registration requires a valid university_id corresponding to an accredited institution."
            )
        user_univ_id = target_univ.id
        user_univ_name = target_univ.institution_name
        db.add(Faculty(
            user_id=user.id,
            university_id=target_univ.id,
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
        univ = University(
            user_id=user.id,
            institution_name=payload.institution_name or payload.full_name,
            district_name=payload.district_name or "Ranchi"
        )
        db.add(univ)
        db.commit()
        db.refresh(univ)
        user_univ_id = univ.id
        user_univ_name = univ.institution_name
    elif payload.role in (UserRole.COMMUNITY_ORG, UserRole.PRI, UserRole.ULB):
        # Community organisations, Gram Panchayats (PRI) and Urban Local Bodies submit
        # challenges on behalf of their organisation and require government verification,
        # same as University/Industry — never auto-verified.
        org_name = payload.organisation_name or payload.full_name
        db.add(OrganizationProfile(
            user_id=user.id,
            legal_name=org_name,
            org_type=payload.role.value,
            reg_number=payload.registration_number,
            official_email=email_clean,
            district_name=payload.district_name or "Ranchi",
            contact_person=payload.full_name,
            phone_number=payload.phone_number,
            verification_status="PENDING"
        ))
        user.district_name = payload.district_name
        user.block_name = payload.block_name
        user.panchayat_name = payload.panchayat_name
    elif payload.role in (UserRole.RESEARCH_LAB, UserRole.INNOVATION_HUB):
        db.add(IndustryPartner(
            user_id=user.id,
            company_name=payload.organisation_name or payload.company_name or payload.full_name,
            industry_domain="Research & Innovation",
            partner_type=PartnerType.RESEARCH_LAB if payload.role == UserRole.RESEARCH_LAB else PartnerType.INNOVATION_HUB
        ))

    db.commit()

    session_id = uuid.uuid4().hex
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        session_id=session_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        university_id=user_univ_id
    )
    refresh_token = create_refresh_token(subject=user.id, role=user.role.value, session_id=session_id)

    session_service.create_session(
        db=db,
        user=user,
        refresh_token=refresh_token,
        session_id=session_id,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent")
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        university_id=user_univ_id,
        university_name=user_univ_name
    )


@router.post("/refresh", response_model=Token)
def refresh_token_endpoint(request: Request, payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Rotates refresh token with persistent database tracking and reuse detection.
    Guarantees cross-worker session invalidation and terminates compromised session families.
    """
    client_ip = rate_limiter.get_client_ip(request)
    user, new_access_token, new_refresh_token = session_service.rotate_session(
        db=db,
        refresh_token=payload.refresh_token,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent")
    )

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
    """Revokes session and JWT token to terminate current worker session across instances."""
    token_to_revoke = None
    if payload and payload.token:
        token_to_revoke = payload.token
    else:
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            token_to_revoke = authorization.split(" ")[1]

    if token_to_revoke:
        revoke_token(token_to_revoke)
        payload_data = decode_access_token(token_to_revoke, verify_exp=False)
        if payload_data:
            session_id = payload_data.get("session_id")
            if session_id:
                session_service.revoke_session(db, session_id, reason="USER_LOGOUT")
            jti = payload_data.get("jti")
            if jti:
                exp_dt = datetime.fromtimestamp(payload_data.get("exp", 0), tz=timezone.utc)
                db.add(RevokedToken(jti=jti, expires_at=exp_dt))
                db.commit()

    return {"status": "success", "message": "Successfully logged out. Session and token revoked."}


@router.post("/logout-all")
def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Terminates all active sessions for current user across all devices and worker processes."""
    revoked_count = session_service.revoke_all_user_sessions(db, current_user.id, reason="LOGOUT_ALL_DEVICES")
    return {
        "status": "success",
        "message": f"Successfully logged out from all devices. {revoked_count} active sessions terminated."
    }


@router.post("/verify-otp")
def verify_otp(
    request: Request,
    payload: Optional[VerifyOTPRequest] = None,
    email: Optional[str] = None,
    identifier: Optional[str] = None,
    otp: Optional[str] = None,
    db: Session = Depends(get_db)
):
    client_ip = rate_limiter.get_client_ip(request)
    target_ident = None
    target_otp = None
    if payload:
        target_ident = payload.identifier or payload.email
        target_otp = payload.otp
    else:
        target_ident = identifier or email
        target_otp = otp

    if not target_ident or not target_otp:
        raise HTTPException(status_code=400, detail="Identifier and OTP are required")

    rate_limiter.enforce(f"otp_verify:ip:{client_ip}", max_requests=20, window_seconds=60, action_name="OTP verification attempts")

    is_valid, err_msg = email_service.verify_otp_detailed(target_ident, target_otp, db=db, purpose="PASSWORD_RESET")
    if is_valid:
        return {"status": "success", "message": "OTP verified successfully"}
    raise HTTPException(status_code=400, detail=err_msg or "Invalid or expired OTP code. Please try again.")


@router.post("/forgot-password")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    client_ip = rate_limiter.get_client_ip(request)
    clean_email = payload.email.lower().strip()

    # Rate limit forgot password requests
    rate_limiter.enforce(f"forgot_pwd:ip:{client_ip}", max_requests=5, window_seconds=900, action_name="password reset requests")
    rate_limiter.enforce(f"forgot_pwd:acc:{clean_email}", max_requests=3, window_seconds=900, action_name="password reset requests")

    user = db.query(User).filter(User.email == clean_email).first()

    # Generate real 6-digit OTP stored hashed in DB
    otp = email_service.generate_otp(clean_email, db=db, purpose="PASSWORD_RESET", ip_address=client_ip)
    user_name = user.full_name if user else None

    # Dispatch real email via SMTP
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
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    client_ip = rate_limiter.get_client_ip(request)
    clean_email = payload.email.lower().strip()

    rate_limiter.enforce(f"reset_pwd:ip:{client_ip}", max_requests=5, window_seconds=300, action_name="password resets")

    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Enforce strong password policy
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    is_valid_pwd, pwd_error = validate_password_strength(payload.new_password, user_email=clean_email, role=role_str)
    if not is_valid_pwd:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pwd_error)

    # Verify OTP against DB hash
    if not email_service.verify_otp(clean_email, payload.otp, db=db, purpose="PASSWORD_RESET"):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code. Please request a new code.")

    # Update password and terminate all previous active sessions
    user.hashed_password = get_password_hash(payload.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    db.commit()

    session_service.revoke_all_user_sessions(db, user.id, reason="PASSWORD_RESET")

    return {
        "status": "success",
        "message": "Password reset successfully. All existing sessions revoked. You can now log in with your new password."
    }


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
