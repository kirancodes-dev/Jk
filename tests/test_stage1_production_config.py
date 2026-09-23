import os
import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from fastapi.testclient import TestClient
from backend.app.core.config import Settings
from backend.app.main import app

def test_production_fails_without_secret_key():
    with pytest.raises((ValueError, ValidationError)) as exc_info:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="",
            DATABASE_URL="postgresql://user:pass@localhost:5432/db",
            ALLOWED_CORS_ORIGINS=["https://portal.jharkhand.gov.in"]
        )
    assert "SECRET_KEY must be explicitly set" in str(exc_info.value)

def test_production_fails_with_insecure_default_secret():
    with pytest.raises((ValueError, ValidationError)) as exc_info:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="jharkhand-sih-2026-super-secure-key-portal-secret-key-32chars",
            DATABASE_URL="postgresql://user:pass@localhost:5432/db",
            ALLOWED_CORS_ORIGINS=["https://portal.jharkhand.gov.in"]
        )
    assert "insecure default" in str(exc_info.value)

def test_production_fails_with_short_secret():
    with pytest.raises((ValueError, ValidationError)) as exc_info:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="short-secret-key",
            DATABASE_URL="postgresql://user:pass@localhost:5432/db",
            ALLOWED_CORS_ORIGINS=["https://portal.jharkhand.gov.in"]
        )
    assert "at least 32 characters long" in str(exc_info.value)

def test_production_fails_with_sqlite():
    with pytest.raises((ValueError, ValidationError)) as exc_info:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 32,
            DATABASE_URL="sqlite:///./prod.db",
            ALLOWED_CORS_ORIGINS=["https://portal.jharkhand.gov.in"]
        )
    assert "SQLite is strictly prohibited" in str(exc_info.value)

def test_production_fails_with_wildcard_cors():
    with pytest.raises((ValueError, ValidationError)) as exc_info:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 32,
            DATABASE_URL="postgresql://user:pass@localhost:5432/db",
            ALLOWED_CORS_ORIGINS=["*"]
        )
    assert "cannot contain wildcard '*'" in str(exc_info.value)

def test_production_fails_with_missing_s3_credentials():
    with pytest.raises((ValueError, ValidationError)) as exc_info:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 32,
            DATABASE_URL="postgresql://user:pass@localhost:5432/db",
            ALLOWED_CORS_ORIGINS=["https://portal.jharkhand.gov.in"],
            STORAGE_TYPE="s3",
            AWS_ACCESS_KEY_ID=None,
            AWS_SECRET_ACCESS_KEY=None,
            S3_BUCKET_NAME=None
        )
    assert "STORAGE_TYPE='s3'" in str(exc_info.value)

def test_production_succeeds_with_valid_config():
    s = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a" * 40,
        DATABASE_URL="postgresql://sih_user:secure_pwd@db:5432/sih_jharkhand",
        ALLOWED_CORS_ORIGINS=["https://portal.jharkhand.gov.in", "https://admin.jharkhand.gov.in"],
        STORAGE_TYPE="local",
        UPLOAD_DIR="uploads"
    )
    assert s.ENVIRONMENT == "production"
    assert len(s.ALLOWED_CORS_ORIGINS) == 2

def test_token_and_upload_limits_validation():
    with pytest.raises((ValueError, ValidationError)):
        Settings(ACCESS_TOKEN_EXPIRE_MINUTES=-5)
    with pytest.raises((ValueError, ValidationError)):
        Settings(REFRESH_TOKEN_EXPIRE_DAYS=0)
    with pytest.raises((ValueError, ValidationError)):
        Settings(MAX_UPLOAD_SIZE_BYTES=200 * 1024 * 1024)

def test_liveness_probe_does_not_require_db():
    with TestClient(app) as client:
        res = client.get("/live")
        assert res.status_code == 200
        assert res.json() == {"status": "alive"}

def test_readiness_probe_success():
    with TestClient(app) as client:
        with patch("backend.app.main.check_database_connection", return_value=(True, None)):
            res = client.get("/ready")
            assert res.status_code == 200
            assert res.json() == {"status": "ready", "database": "connected"}

def test_readiness_probe_failure_safe_response():
    with TestClient(app) as client:
        with patch("backend.app.main.check_database_connection", return_value=(False, "Database connection unavailable")):
            res = client.get("/ready")
            assert res.status_code == 503
            body = res.json()
            assert body["status"] == "not_ready"
            assert body["database"] == "unavailable"
            # Ensure no secrets, hosts, or stack traces are leaked
            assert "password" not in str(body).lower()
            assert "traceback" not in str(body).lower()
            assert "localhost" not in str(body).lower()

def test_health_probe_success_and_failure():
    with TestClient(app) as client:
        with patch("backend.app.main.check_database_connection", return_value=(True, None)):
            res = client.get("/health")
            assert res.status_code == 200
            assert res.json()["status"] == "healthy"

        with patch("backend.app.main.check_database_connection", return_value=(False, "Connection error")):
            res = client.get("/health")
            assert res.status_code == 503
            assert res.json()["status"] == "unhealthy"

def test_lifespan_does_not_call_create_all_in_production():
    from backend.app.main import lifespan
    from backend.app.core.config import settings
    import asyncio

    with patch.object(settings, "ENVIRONMENT", "production"), \
         patch.object(settings, "DATABASE_URL", "postgresql://user:pass@localhost:5432/db"), \
         patch.object(settings, "DEMO_MODE", False), \
         patch("backend.app.core.database.Base.metadata.create_all") as mock_create_all:
        async def run_test():
            async with lifespan(app):
                pass
        asyncio.run(run_test())
        mock_create_all.assert_not_called()

def test_no_hardcoded_secrets_in_docker_files():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check docker-compose.yml
    compose_path = os.path.join(base_dir, "docker-compose.yml")
    with open(compose_path, "r") as f:
        compose_text = f.read()
    assert "sih_secure_password_2026" not in compose_text
    assert "jharkhand-sih-2026-production-super-secret-key" not in compose_text
    assert "${POSTGRES_PASSWORD" in compose_text
    assert "${SECRET_KEY" in compose_text

    # Check Dockerfile
    dockerfile_path = os.path.join(base_dir, "Dockerfile")
    with open(dockerfile_path, "r") as f:
        dockerfile_text = f.read()
    assert "COPY .env.example /app/.env" not in dockerfile_text
    assert "USER appuser" in dockerfile_text
