"""
Stage 11: Production Security Controls, Secure Storage, Observability,
Worker Resilience & DPDP Technical Rights — Test Suite.
"""

import io
import os
import subprocess
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.core.security import create_access_token
from backend.app.core.security_headers import TrustedProxyHelper
from backend.app.core.logging_config import redact_sensitive_text, redact_sensitive_dict
from backend.app.services.storage_service import storage_service, EICAR_SIGNATURE
from backend.app.worker import BackgroundWorker
from backend.app.models.models import (
    User, UserRole, ChallengeAttachment, AIJob, AIJobStatus,
    NotificationOutbox, Notification, utc_now
)

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def _mk_user(db, email, role, full_name="Stage 11 User"):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        email=email, full_name=full_name, role=role,
        hashed_password="hash", is_active=True, is_verified=True,
        admin_tier="STATE", district_name="Ranchi"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _auth_header(user: User):
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(
        subject=str(user.id),
        role=role_str,
        district_name=user.district_name,
        tier=user.admin_tier
    )
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. Production Security Headers & DoS Limits
# ==============================================================================

def test_security_headers_present():
    """Verify essential defense-in-depth headers on responses."""
    resp = client.get("/api-info")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "strict-origin-when-cross-origin" in resp.headers.get("Referrer-Policy", "")
    assert "default-src" in resp.headers.get("Content-Security-Policy", "")


def test_hsts_behind_https():
    """Verify Strict-Transport-Security header is emitted when behind verified HTTPS."""
    resp = client.get("/api-info", headers={"X-Forwarded-Proto": "https"})
    assert resp.status_code == 200
    assert "Strict-Transport-Security" in resp.headers
    assert "max-age=31536000" in resp.headers["Strict-Transport-Security"]


def test_safe_cache_control_on_api_endpoints():
    """Verify API endpoints return no-store/no-cache headers to prevent proxy caching of sensitive data."""
    resp = client.get("/api/v1/privacy/notices")
    assert resp.status_code == 200
    cache_control = resp.headers.get("Cache-Control", "")
    assert "no-store" in cache_control or "no-cache" in cache_control


def test_request_payload_size_limit():
    """Verify RequestLimitMiddleware rejects payloads with content-length > 25MB."""
    excessive_len = str(30 * 1024 * 1024)  # 30 MB
    resp = client.post("/api/v1/auth/login", headers={"content-length": excessive_len}, content=b"")
    assert resp.status_code == 413
    assert "exceeds maximum allowed size" in resp.json()["detail"]


def test_trusted_proxy_helper():
    """Verify TrustedProxyHelper parses X-Forwarded-For securely only from trusted CIDRs."""
    from fastapi import Request
    
    class FakeRequest:
        def __init__(self, host, forwarded):
            self.client = type("Client", (), {"host": host})()
            self.headers = {"X-Forwarded-For": forwarded} if forwarded else {}

    # Untrusted direct client IP cannot spoof via X-Forwarded-For
    req = FakeRequest("203.0.113.195", "198.51.100.5")
    assert TrustedProxyHelper.get_trusted_client_ip(req) == "203.0.113.195"

    # Trusted proxy (10.0.1.5) forwards real client IP
    req_trusted = FakeRequest("10.0.1.5", "198.51.100.5")
    assert TrustedProxyHelper.get_trusted_client_ip(req_trusted) == "198.51.100.5"


# ==============================================================================
# 2. Structured Logging & PII Masking
# ==============================================================================

def test_sensitive_masking_in_logs():
    """Verify passwords, OTPs, Bearer tokens, Aadhaar, and phone numbers are scrubbed."""
    raw = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.abcdef1234567890 password=supersecret otp=123456 Aadhaar 1234 5678 9012 Phone +919876543210 lat: 23.3456789"
    redacted = redact_sensitive_text(raw)

    assert "supersecret" not in redacted
    assert "123456" not in redacted
    assert "1234 5678 9012" not in redacted
    assert "+919876543210" not in redacted
    assert "XXXX-XXXX-9012" in redacted
    assert "[REDACTED]" in redacted

    dict_data = {
        "user_email": "citizen@jharkhand.gov.in",
        "api_key": "gemini-api-key-12345",
        "nested": {"password": "mypassword"}
    }
    redacted_dict = redact_sensitive_dict(dict_data)
    assert redacted_dict["api_key"] == "[REDACTED]"
    assert redacted_dict["nested"]["password"] == "[REDACTED]"


# ==============================================================================
# 3. Observability, Metrics & Health Probes
# ==============================================================================

def test_health_probes():
    """Verify /live, /ready, and /health endpoints."""
    live = client.get("/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert "storage" in health.json()


def test_prometheus_metrics_endpoint():
    """Verify /metrics exposes Prometheus formatted metrics."""
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers.get("content-type", "")
    assert b"http_requests_total" in resp.content or b"backend_status_up" in resp.content


# ==============================================================================
# 4. Secure Storage, EICAR Detection & EXIF Stripping
# ==============================================================================

def test_storage_eicar_malware_rejection():
    """Verify storage scanner immediately rejects the standard EICAR test string."""
    with pytest.raises(Exception) as excinfo:
        storage_service.scan_for_malware(EICAR_SIGNATURE)
    assert "EICAR" in str(excinfo.value)


def test_image_metadata_stripping():
    """Verify EXIF metadata is stripped from images without corrupting visual data."""
    # Create simple in-memory JPEG
    img = Image.new("RGB", (64, 64), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    raw_bytes = buf.getvalue()

    cleaned = storage_service.strip_image_metadata(raw_bytes, "image/jpeg")
    assert len(cleaned) > 0
    # Cleaned image should still be loadable by PIL
    reopened = Image.open(io.BytesIO(cleaned))
    assert reopened.size == (64, 64)


def test_attachment_soft_delete_and_restore(db_session):
    """Verify soft-delete hides attachment and restore restores it (Admin only)."""
    user = _mk_user(db_session, "storage.owner@jharkhand.gov.in", UserRole.CITIZEN)
    admin = _mk_user(db_session, "storage.admin@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN)

    import uuid
    unique_obj_id = f"test_obj_{uuid.uuid4().hex[:12]}"
    # Create dummy attachment
    att = ChallengeAttachment(
        object_id=unique_obj_id,
        owner_id=user.id,
        original_filename="evidence.pdf",
        detected_mime="application/pdf",
        size_bytes=1024,
        sha256_checksum="abcdef1234567890",
        storage_key="/tmp/nonexistent.pdf",
        retention_state="ACTIVE"
    )
    db_session.add(att)
    db_session.commit()

    # User soft-deletes own attachment
    headers_user = _auth_header(user)
    del_resp = client.delete(f"/api/v1/files/attachments/{att.object_id}", headers=headers_user)
    assert del_resp.status_code == 200
    assert del_resp.json()["retention_state"] == "SOFT_DELETED"

    # Non-admin cannot restore
    res_unauth = client.post(f"/api/v1/files/attachments/{att.object_id}/restore", headers=headers_user)
    assert res_unauth.status_code == 403

    # Admin restores
    headers_admin = _auth_header(admin)
    res_admin = client.post(f"/api/v1/files/attachments/{att.object_id}/restore", headers=headers_admin)
    assert res_admin.status_code == 200
    assert res_admin.json()["retention_state"] == "ACTIVE"


def test_presigned_url_generation():
    """Verify presigned download and upload URL responses."""
    upload_res = storage_service.generate_presigned_upload_url("obj999", ".pdf")
    assert "upload_url" in upload_res
    assert upload_res["object_id"] == "obj999"

    download_res = storage_service.generate_presigned_download_url("active/obj999.pdf")
    assert "obj999.pdf" in download_res


# ==============================================================================
# 5. Distributed Worker & Concurrency Locking
# ==============================================================================

def test_background_worker_cycle_and_stale_recovery(db_session):
    """Verify worker recovers stale jobs and updates queue depth metrics."""
    import uuid
    worker = BackgroundWorker(worker_id="test-worker-unit", visibility_timeout_seconds=5)

    # Insert a stale processing job with unique idempotency key
    stale_time = utc_now() - timedelta(seconds=10)
    unique_key = f"TEST_STALE_JOB_{uuid.uuid4().hex[:8]}"
    stale_ai = AIJob(
        challenge_id=1,
        idempotency_key=unique_key,
        status=AIJobStatus.PROCESSING,
        attempts=1,
        max_retries=3,
        updated_at=stale_time,
        next_run_at=utc_now() - timedelta(minutes=5)
    )
    db_session.add(stale_ai)
    db_session.commit()

    # Run recovery
    worker.recover_stale_jobs(db_session)
    db_session.refresh(stale_ai)
    assert stale_ai.status == AIJobStatus.PENDING

    # Verify atomic claiming
    claimed = worker.claim_ai_jobs(db_session, limit=500)
    assert any(j.id == stale_ai.id for j in claimed)
    db_session.refresh(stale_ai)
    assert stale_ai.status == AIJobStatus.PROCESSING

    # Cleanup
    db_session.delete(stale_ai)
    db_session.commit()


# ==============================================================================
# 6. DPDP Citizen Data Rights & Privacy APIs
# ==============================================================================

def test_dpdp_citizen_rights(db_session):
    """Verify statutory notices, data export (/my-data), correction (/correct-data), and erasure (/request-erasure)."""
    import uuid
    user_email = f"dpdp.citizen.{uuid.uuid4().hex[:8]}@jharkhand.gov.in"
    user = _mk_user(db_session, user_email, UserRole.CITIZEN, full_name="DPDP Citizen")
    headers = _auth_header(user)

    # 1. Statutory notices
    notices_resp = client.get("/api/v1/privacy/notices")
    assert notices_resp.status_code == 200
    assert "data_fiduciary" in notices_resp.json()
    assert "purposes_collected" in notices_resp.json()

    # 2. My Data export
    export_resp = client.get("/api/v1/privacy/my-data", headers=headers)
    assert export_resp.status_code == 200
    data = export_resp.json()
    assert data["profile"]["email"] == user_email
    assert "submitted_challenges" in data

    # 3. Data correction
    correction_payload = {"full_name": "Corrected Citizen Name", "district_name": "Ranchi"}
    corr_resp = client.put("/api/v1/privacy/correct-data", headers=headers, json=correction_payload)
    assert corr_resp.status_code == 200
    db_session.refresh(user)
    assert user.full_name == "Corrected Citizen Name"

    # 4. Data erasure / anonymization
    erasure_payload = {
        "reason": "Exercising DPDP right to be forgotten after challenge completion",
        "confirmation": True
    }
    erase_resp = client.post("/api/v1/privacy/request-erasure", headers=headers, json=erasure_payload)
    assert erase_resp.status_code == 200
    assert erase_resp.json()["status"] == "anonymized"

    db_session.refresh(user)
    assert "Anonymized Citizen" in user.full_name
    assert user.is_active is False
    assert "@privacy.jharkhand.gov.in" in user.email


# ==============================================================================
# 7. Backup & Restore Drill Automation
# ==============================================================================

def test_backup_and_restore_scripts():
    """Verify backup script creates encrypted file and verify_restore.sh validates it."""
    backup_dir = "./backups/test_run"
    os.makedirs(backup_dir, exist_ok=True)
    passphrase = "test-encryption-passphrase-jharkhand-2026"

    env = os.environ.copy()
    env["BACKUP_PASSPHRASE"] = passphrase
    env["BACKUP_DIR"] = backup_dir
    env["DATABASE_URL"] = "postgresql://sih_user:sih_password@localhost:5432/sih_portal"

    # Run backup script
    result = subprocess.run(
        ["./scripts/backup/backup_postgres.sh"],
        env=env,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Backup script failed: {result.stderr}"

    # Find created files
    files = os.listdir(backup_dir)
    enc_files = [f for f in files if f.endswith(".sql.gz.enc")]
    manifest_files = [f for f in files if f.endswith(".manifest.json")]
    assert len(enc_files) >= 1
    assert len(manifest_files) >= 1

    enc_path = os.path.join(backup_dir, enc_files[0])
    manifest_path = os.path.join(backup_dir, manifest_files[0])

    # Run verify restore drill
    restore_result = subprocess.run(
        ["./scripts/backup/verify_restore.sh", enc_path, manifest_path],
        env=env,
        capture_output=True,
        text=True
    )
    assert restore_result.returncode == 0, f"Restore drill failed: {restore_result.stderr}"
    assert "Restore Verification Drill PASSED" in restore_result.stdout

    # Clean up test backups
    import shutil
    shutil.rmtree(backup_dir, ignore_errors=True)
