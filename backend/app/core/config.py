import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH 2026 Societal Innovation Collaboration Portal"
    ORGANIZATION: str = "Government of Jharkhand - Higher & Technical Education"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "jharkhand-sih-2026-super-secure-key-portal-secret-key-32chars")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30   # 30 days
    
    # Environment mode
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    
    # Dual database support: defaults to SQLite for instant local test, works with PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./sih_jharkhand.db"
    )
    
    # S3 / Local Media Storage
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # 'local' or 's3'
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".mp4", ".doc", ".docx"]
    ALLOWED_MIME_TYPES: List[str] = [
        "image/jpeg", "image/png", "application/pdf", 
        "video/mp4", "application/msword", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    AWS_REGION: Optional[str] = os.getenv("AWS_REGION", "ap-south-1")
    S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME", "jharkhand-sih-challenges")
    
    # Pluggable LLM API
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)

    # SMTP Real Email Service
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", None)
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", None)
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "biradark56@gmail.com")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Government of Jharkhand Innovation Council")

    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
