import re
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Set, Tuple
import jwt
import bcrypt
from backend.app.core.config import settings

# In-memory cache for revocation (DB is the single source of truth)
_revoked_tokens: Set[str] = set()

COMMON_WEAK_PASSWORDS = {
    "password", "password123", "admin123", "admin@123", "qwerty123",
    "12345678", "123456789", "jharkhand123", "secret123", "welcome123"
}

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def hash_sha256(data: str) -> str:
    """Computes SHA-256 digest for persistent session tokens and secrets."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def hash_otp(otp: str, salt: str = "jharkhand_sih_2026_otp_salt") -> str:
    """Computes a salted SHA-256 hash for secure database OTP storage."""
    combined = f"{salt}:{otp.strip()}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

def validate_password_strength(
    password: str,
    user_email: Optional[str] = None,
    role: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Enforces strong password policy:
    - Min 10 characters (12 for privileged government roles)
    - At least 1 uppercase letter, 1 lowercase letter, 1 digit, 1 special character
    - Rejects common dictionary words and email username matches
    """
    is_privileged = role in ("GOVERNMENT_ADMIN", "GOVERNMENT_OFFICER")
    min_len = 12 if is_privileged else 10

    if len(password) < min_len:
        return False, f"Password must be at least {min_len} characters long."

    if password.lower() in COMMON_WEAK_PASSWORDS:
        return False, "Password is too common and easily guessable. Please choose a stronger password."

    if user_email:
        email_prefix = user_email.split("@")[0].lower()
        if len(email_prefix) >= 3 and email_prefix in password.lower():
            return False, "Password cannot contain parts of your email address."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one numeric digit (0-9)."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]]", password):
        return False, "Password must contain at least one special character (e.g. !@#$%^&*)."

    return True, None

def create_access_token(
    subject: Any, 
    role: str, 
    expires_delta: Optional[timedelta] = None, 
    university_id: Optional[int] = None,
    permissions: Optional[list] = None,
    session_id: Optional[str] = None,
    tier: Optional[str] = None,
    jurisdiction_name: Optional[str] = None,
    district_name: Optional[str] = None,
    block_name: Optional[str] = None,
    panchayat_name: Optional[str] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jti = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    to_encode = {
        "jti": jti,
        "type": "access",
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "iat": now
    }
    if session_id:
        to_encode["session_id"] = session_id
    if university_id is not None:
        to_encode["university_id"] = university_id
    if permissions:
        to_encode["permissions"] = permissions
    if tier:
        to_encode["tier"] = tier
    if jurisdiction_name:
        to_encode["jurisdiction"] = jurisdiction_name
    if district_name:
        to_encode["district_name"] = district_name
    if block_name:
        to_encode["block_name"] = block_name
    if panchayat_name:
        to_encode["panchayat_name"] = panchayat_name

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Any, role: str, session_id: Optional[str] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    to_encode = {
        "jti": jti,
        "type": "refresh",
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "iat": now
    }
    if session_id:
        to_encode["session_id"] = session_id
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str, verify_exp: bool = True) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": verify_exp}
        )
        jti = payload.get("jti")
        if jti and jti in _revoked_tokens:
            return None
        return payload
    except jwt.PyJWTError:
        return None

def revoke_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
        jti = payload.get("jti")
        if jti:
            _revoked_tokens.add(jti)
        return True
    except Exception:
        return False

def is_token_revoked(jti: str) -> bool:
    return jti in _revoked_tokens

