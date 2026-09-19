import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Set
import jwt
import bcrypt
from backend.app.core.config import settings

# In-memory revoked token JTI / token set for ultra-fast blacklist checking
_revoked_tokens: Set[str] = set()

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(
    subject: Any, 
    role: str, 
    expires_delta: Optional[timedelta] = None, 
    university_id: Optional[int] = None,
    permissions: Optional[list] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jti = uuid.uuid4().hex
    to_encode = {
        "jti": jti,
        "type": "access",
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "iat": datetime.now(timezone.utc)
    }
    if university_id is not None:
        to_encode["university_id"] = university_id
    if permissions:
        to_encode["permissions"] = permissions
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Any, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = uuid.uuid4().hex
    to_encode = {
        "jti": jti,
        "type": "refresh",
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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
