"""
Stage 12: Security Negative & Invariant Property Tests for SIH 26043.
Enforces defense-in-depth:
1. Vertical Privilege Escalation Protection (Citizens/Students cannot validate challenges or approve projects).
2. Horizontal Privilege Escalation / BOLA Defense (Cannot delete or modify other users' files).
3. Cross-District Jurisdiction Tampering Prevention (Officers strictly restricted to designated geographic tier).
4. Path Traversal & Injection Defense (Block directory walking / traversal characters).
5. Fail-Closed Production Configuration Constraints (Rejects demo flags, SQLite, and local storage in production).
6. Unauthenticated Access Rejection on Sensitive Resources.
"""

import uuid
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import Settings
from backend.app.core.database import SessionLocal
from backend.app.core.security import create_access_token
from backend.app.models.models import (
    User, UserRole, Challenge, ChallengeLocation, District, ChallengeStatus, ChallengePriority,
    ChallengeAttachment
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


def _mk_user(db, email, role, district_name="Ranchi", admin_tier="STATE"):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        email=email, full_name=f"User {role.value}", role=role,
        hashed_password="hash", is_active=True, is_verified=True,
        district_name=district_name, admin_tier=admin_tier
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
# Property 1: Vertical Privilege Escalation Rejection
# ==============================================================================

def test_vertical_privilege_escalation_rejected(db_session):
    """Citizens and Students cannot update challenge status or access administrative endpoints."""
    citizen = _mk_user(db_session, f"cit.unauth.{uuid.uuid4().hex[:6]}@jharkhand.gov.in", UserRole.CITIZEN)
    headers = _auth_header(citizen)

    # Attempt to change challenge status (officer/admin only)
    resp = client.post("/api/v1/challenges/1/status", headers=headers, json={"status": "VALIDATED", "expected_version": 1})
    assert resp.status_code in (400, 401, 403), f"Expected 400/403 for unauthorized status transition, got: {resp.status_code}"

    # Attempt to access admin overview analytics
    admin_resp = client.get("/api/v1/admin/dashboard", headers=headers)
    assert admin_resp.status_code in (401, 403)


# ==============================================================================
# Property 2: Horizontal Privilege Escalation / BOLA Rejection
# ==============================================================================

def test_horizontal_privilege_escalation_blocked(db_session):
    """User A cannot delete User B's private attachment."""
    user_a = _mk_user(db_session, f"user_a.{uuid.uuid4().hex[:6]}@jharkhand.gov.in", UserRole.CITIZEN)
    user_b = _mk_user(db_session, f"user_b.{uuid.uuid4().hex[:6]}@jharkhand.gov.in", UserRole.CITIZEN)

    att = ChallengeAttachment(
        object_id=f"test_bola_{uuid.uuid4().hex[:10]}",
        owner_id=user_a.id,
        original_filename="private_land_record.pdf",
        detected_mime="application/pdf",
        size_bytes=2048,
        sha256_checksum="hash123",
        storage_key="/tmp/private.pdf",
        retention_state="ACTIVE"
    )
    db_session.add(att)
    db_session.commit()

    # User B attempts to delete User A's attachment
    headers_b = _auth_header(user_b)
    del_resp = client.delete(f"/api/v1/files/attachments/{att.object_id}", headers=headers_b)
    assert del_resp.status_code == 403, f"Expected 403 Forbidden for unauthorized deletion, got: {del_resp.status_code}"

    # Verify attachment remains active
    db_session.refresh(att)
    assert att.retention_state == "ACTIVE"


# ==============================================================================
# Property 3: Cross-District Jurisdiction Tampering Prevention
# ==============================================================================

def test_cross_district_tampering_blocked(db_session):
    """
    Ranchi district officer cannot modify or validate a Dhanbad challenge.
    Enforces geographic tenant isolation across administrative tiers.
    """
    ranchi_officer = _mk_user(
        db_session, f"off.ranchi.{uuid.uuid4().hex[:6]}@jharkhand.gov.in",
        UserRole.GOVERNMENT_OFFICER, district_name="Ranchi", admin_tier="DISTRICT"
    )
    headers = _auth_header(ranchi_officer)

    # Create Dhanbad challenge
    dhanbad_citizen = _mk_user(db_session, f"cit.dhanbad.{uuid.uuid4().hex[:6]}@jharkhand.gov.in", UserRole.CITIZEN, district_name="Dhanbad")
    dhanbad_district = db_session.query(District).filter(District.name == "Dhanbad").first()
    if not dhanbad_district:
        dhanbad_district = District(name="Dhanbad", latitude=23.79, longitude=86.43)
        db_session.add(dhanbad_district)
        db_session.commit()
        db_session.refresh(dhanbad_district)

    dhanbad_ch = Challenge(
        title=f"Underground Coal Mine Fire in Jharia #{uuid.uuid4().hex[:6]}",
        description="Hazardous gas leak in Jharia mining sector.",
        submitted_by_user_id=dhanbad_citizen.id,
        category="Water Resources & Rural Irrigation",
        status=ChallengeStatus.SUBMITTED,
        priority=ChallengePriority.HIGH
    )
    db_session.add(dhanbad_ch)
    db_session.commit()
    db_session.refresh(dhanbad_ch)

    loc = ChallengeLocation(
        challenge_id=dhanbad_ch.id,
        district_id=dhanbad_district.id,
        district_name="Dhanbad",
        block_name="Jharia",
        latitude=23.79,
        longitude=86.43
    )
    db_session.add(loc)
    db_session.commit()

    # Ranchi officer attempts to validate Dhanbad challenge
    val_resp = client.post(
        f"/api/v1/challenges/{dhanbad_ch.id}/status",
        headers=headers,
        json={"status": "VALIDATED", "expected_version": dhanbad_ch.version}
    )
    assert val_resp.status_code in (403, 404), f"Expected 403 Forbidden for cross-district tampering, got: {val_resp.status_code}"


# ==============================================================================
# Property 4: Path Traversal & Injection Defense
# ==============================================================================

def test_path_traversal_payloads_rejected(db_session):
    """Directory traversal payloads containing '..' or null bytes are rejected with 400 Bad Request."""
    admin = _mk_user(db_session, f"admin.sec.{uuid.uuid4().hex[:6]}@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN)
    headers = _auth_header(admin)

    traversal_payloads = [
        "../../etc/passwd",
        "....//....//etc/shadow",
        "media/..%2F..%2Fetc",
        "sensitive/../../../secret.txt",
    ]

    for payload in traversal_payloads:
        resp = client.get(f"/api/v1/files/{payload}", headers=headers)
        assert resp.status_code in (400, 404), f"Payload {payload} was not properly blocked, got: {resp.status_code}"


# ==============================================================================
# Property 5: Fail-Closed Production Configuration Constraints
# ==============================================================================

def test_production_fails_closed_on_insecure_settings():
    """Verify that Settings validation fails closed with clear errors in production."""
    # 1. Reject DEMO_MODE=True in production
    with pytest.raises(ValueError, match="DEMO_MODE must be false"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a-very-secure-secret-key-at-least-32-chars-long",
            DATABASE_URL="postgresql://user:pass@localhost:5432/sih",
            ALLOWED_CORS_ORIGINS=["https://portal.jharkhand.gov.in"],
            STORAGE_TYPE="s3",
            AWS_ACCESS_KEY_ID="valid_key",
            AWS_SECRET_ACCESS_KEY="valid_secret",
            S3_BUCKET_NAME="valid_bucket",
            DEMO_MODE=True
        )

    # 2. Reject SQLite in production
    with pytest.raises(ValueError, match="SQLite is strictly prohibited"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a-very-secure-secret-key-at-least-32-chars-long",
            DATABASE_URL="sqlite:///./insecure_prod.db",
            ALLOWED_CORS_ORIGINS=["https://portal.jharkhand.gov.in"],
            STORAGE_TYPE="s3",
            AWS_ACCESS_KEY_ID="valid_key",
            AWS_SECRET_ACCESS_KEY="valid_secret",
            S3_BUCKET_NAME="valid_bucket",
            DEMO_MODE=False
        )

    # 3. Reject Local Storage in production
    with pytest.raises(ValueError, match="Local storage is strictly prohibited in production"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a-very-secure-secret-key-at-least-32-chars-long",
            DATABASE_URL="postgresql://user:pass@localhost:5432/sih",
            ALLOWED_CORS_ORIGINS=["https://portal.jharkhand.gov.in"],
            STORAGE_TYPE="local",
            DEMO_MODE=False
        )


# ==============================================================================
# Property 6: Unauthenticated Access Blocked on Sensitive Endpoints
# ==============================================================================

def test_unauthenticated_requests_rejected():
    """Protected endpoints require valid Bearer token."""
    # Post challenge without auth
    resp = client.post("/api/v1/challenges", json={"title": "Unauthorized"})
    assert resp.status_code == 401

    # Access my-data without auth
    privacy_resp = client.get("/api/v1/privacy/my-data")
    assert privacy_resp.status_code == 401
