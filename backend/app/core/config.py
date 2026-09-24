import os
from typing import Optional, List, Union
from pydantic import ConfigDict, field_validator, model_validator
from pydantic_settings import BaseSettings

INSECURE_DEFAULT_SECRETS = {
    "replace-with-a-random-secure-secret-key-in-production",
    "jharkhand-sih-2026-super-secure-key-portal-secret-key-32chars",
    "jharkhand-sih-2026-production-super-secret-key-64chars-minimum",
    "ci-secret-key-at-least-32-chars-long",
    "dev-insecure-secret-key-32chars-minimum-length-for-local-testing",
    "secret",
    "changeme",
    "password",
    "admin",
}

class Settings(BaseSettings):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    PROJECT_NAME: str = "SIH 2026 Societal Innovation Collaboration Portal"
    ORGANIZATION: str = "Government of Jharkhand - Higher & Technical Education"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # Environment mode
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    
    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./sih_jharkhand.db"
    )
    
    # Allowed CORS Origins: comma-separated string or list of origins
    ALLOWED_CORS_ORIGINS: Union[List[str], str] = os.getenv(
        "ALLOWED_CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:8008,http://127.0.0.1:3000,http://127.0.0.1:8008"
    )
    
    # S3 / Local Media Storage
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local").lower()
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(15 * 1024 * 1024)))  # Default 15 MB
    # .m4a/.wav/.webm/.mp3 support real citizen voice-note evidence attachments
    # (see report_challenge_screen.dart's voice recorder); detected and validated
    # by real magic-byte signatures in storage_service.py, same as every other type.
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".mp4", ".doc", ".docx", ".m4a", ".wav", ".webm", ".mp3"]
    ALLOWED_MIME_TYPES: List[str] = [
        "image/jpeg", "image/png", "application/pdf",
        "video/mp4", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "audio/mp4", "audio/wav", "audio/webm", "audio/mpeg"
    ]
    # Optional ClamAV daemon integration for real virus scanning (off by default).
    # When unset, uploads fall back to the basic EICAR-string + dangerous-magic-byte
    # signature check in storage_service.py — this is documented, not hidden, in the
    # scan_status recorded on each attachment ("CLEAN" vs "CLEAN_BASIC_CHECK_ONLY").
    CLAMAV_HOST: Optional[str] = os.getenv("CLAMAV_HOST", None)
    CLAMAV_PORT: int = int(os.getenv("CLAMAV_PORT", "3310"))

    # Optional real payment/finance settlement integration for CSR funding release
    # (off by default). See backend/app/services/finance_integration_service.py —
    # without this set, funds are never marked payment_confirmed.
    FINANCE_INTEGRATION_PROVIDER: Optional[str] = os.getenv("FINANCE_INTEGRATION_PROVIDER", None)

    # Optional real multilingual sentence-embedding similarity for deduplication
    # (off by default). See backend/app/services/ai/embedding_service.py — without
    # this enabled (and sentence-transformers installed), similarity scoring stays
    # on the deterministic bag-of-words rule-based fallback everywhere.
    AI_EMBEDDINGS_ENABLED: bool = os.getenv("AI_EMBEDDINGS_ENABLED", "false").lower() == "true"
    AI_EMBEDDINGS_MODEL_NAME: str = os.getenv("AI_EMBEDDINGS_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2")

    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    AWS_REGION: Optional[str] = os.getenv("AWS_REGION", "ap-south-1")
    S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME", "jharkhand-sih-challenges")
    S3_ENDPOINT_URL: Optional[str] = os.getenv("S3_ENDPOINT_URL", None)
    S3_USE_SSL: bool = os.getenv("S3_USE_SSL", "true").lower() in ("true", "1", "yes")
    S3_QUARANTINE_PREFIX: str = os.getenv("S3_QUARANTINE_PREFIX", "quarantine/")
    ENABLE_HSTS: bool = os.getenv("ENABLE_HSTS", "false").lower() in ("true", "1", "yes")
    TRUSTED_PROXIES: List[str] = [
        p.strip() for p in os.getenv("TRUSTED_PROXIES", "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16").split(",") if p.strip()
    ]
    
    # Pluggable LLM API
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)

    # SMTP Real Email Service
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", None)
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", None)
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@jharkhand.gov.in")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Government of Jharkhand Innovation Council")

    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    @field_validator("ALLOWED_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_production_and_runtime_constraints(self) -> "Settings":
        env = self.ENVIRONMENT.lower()
        if env not in ("development", "test", "production"):
            raise ValueError(f"ENVIRONMENT must be one of 'development', 'test', 'production'. Got: '{self.ENVIRONMENT}'")

        # Fallback secret for dev/test if not specified
        if not self.SECRET_KEY:
            if env == "production":
                raise ValueError("In production, SECRET_KEY must be explicitly set and cannot be empty.")
            # Dev fallback
            self.SECRET_KEY = "dev-insecure-secret-key-32chars-minimum-length-for-local-testing"

        # Production security validations (Fail Closed)
        if env == "production":
            # 1. Strong secret key requirement
            if len(self.SECRET_KEY) < 32:
                raise ValueError("In production, SECRET_KEY must be at least 32 characters long.")
            if self.SECRET_KEY in INSECURE_DEFAULT_SECRETS:
                raise ValueError("In production, SECRET_KEY cannot use an insecure default or placeholder value.")

            # 2. Database validation: No SQLite in production
            if not self.DATABASE_URL or self.DATABASE_URL.startswith("sqlite"):
                raise ValueError("In production, DATABASE_URL must be a valid PostgreSQL connection URL. SQLite is strictly prohibited.")
            if not (self.DATABASE_URL.startswith("postgresql://") or self.DATABASE_URL.startswith("postgresql+psycopg2://") or self.DATABASE_URL.startswith("postgres://")):
                raise ValueError("In production, DATABASE_URL must start with 'postgresql://' or 'postgresql+psycopg2://'.")

            # 3. CORS validation: No wildcard in production
            if not self.ALLOWED_CORS_ORIGINS:
                raise ValueError("In production, ALLOWED_CORS_ORIGINS must be configured with explicit origins.")
            if "*" in self.ALLOWED_CORS_ORIGINS:
                raise ValueError("In production, ALLOWED_CORS_ORIGINS cannot contain wildcard '*'.")

            # 4. Storage configuration validation: Local storage strictly prohibited in production
            if self.STORAGE_TYPE != "s3":
                raise ValueError("In production, STORAGE_TYPE must be 's3'. Local storage is strictly prohibited in production.")
            if not self.AWS_ACCESS_KEY_ID or not self.AWS_SECRET_ACCESS_KEY or not self.S3_BUCKET_NAME:
                raise ValueError("When STORAGE_TYPE='s3' in production, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME must all be set.")

            # 5. Demo mode strictly forbidden in production
            if self.DEMO_MODE:
                raise ValueError("In production, DEMO_MODE must be false. Demo mode is strictly prohibited in production.")

            # 6. No personal email defaults in production
            if "biradark56@gmail.com" in self.SMTP_FROM_EMAIL.lower():
                raise ValueError("In production, SMTP_FROM_EMAIL cannot use a personal email address.")

        # General validations (all environments)
        if self.STORAGE_TYPE not in ("local", "s3"):
            raise ValueError(f"STORAGE_TYPE must be 'local' or 's3'. Got: '{self.STORAGE_TYPE}'")

        if self.ACCESS_TOKEN_EXPIRE_MINUTES <= 0 or self.ACCESS_TOKEN_EXPIRE_MINUTES > 43200:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 43200 (30 days).")

        if self.REFRESH_TOKEN_EXPIRE_DAYS <= 0 or self.REFRESH_TOKEN_EXPIRE_DAYS > 365:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be between 1 and 365.")

        if self.MAX_UPLOAD_SIZE_BYTES <= 0 or self.MAX_UPLOAD_SIZE_BYTES > 100 * 1024 * 1024:
            raise ValueError("MAX_UPLOAD_SIZE_BYTES must be between 1 byte and 104,857,600 bytes (100 MB).")

        return self

settings = Settings()

