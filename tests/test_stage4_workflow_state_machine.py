import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.models import (
    User, UserRole, AccountStatus, Challenge, ChallengeLocation,
    ChallengeStatus, District, University, OrganizationProfile,
    ChallengeAllocation, AllocationStatus, DomainAuditEvent
)
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.services.workflow_service import WorkflowService


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _get_or_create_user(
    db: Session,
    email: str,
    role: UserRole,
    full_name: str,
    tier: str = "STATE",
    district: str = "Ranchi",
    block: str = "Angara"
) -> User:
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(
            email=email,
            hashed_password=get_password_hash("StrongPass!2026"),
            full_name=full_name,
            role=role,
            admin_tier=tier,
            district_name=district,
            block_name=block,
            account_status=AccountStatus.ACTIVE,
            is_verified=True,
            is_active=True
        )
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


def _headers_for(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        role=user.role.value,
        tier=user.admin_tier,
        district_name=user.district_name,
        block_name=user.block_name
    )
    return {"Authorization": f"Bearer {token}"}


def _create_test_challenge(db: Session, submitter: User, district_name: str = "Ranchi") -> Challenge:
    dist = db.query(District).filter(District.name == district_name).first()
    if not dist:
        dist = District(name=district_name, state="Jharkhand")
        db.add(dist)
        db.commit()
        db.refresh(dist)

    ch = Challenge(
        title=f"Test Challenge {uuid.uuid4().hex[:6]}",
        description="Water scarcity in rural village hindering irrigation and drinking supply.",
        category="WATER_RESOURCES",
        status=ChallengeStatus.SUBMITTED,
        current_tier="PANCHAYAT",
        submitted_by_user_id=submitter.id,
        version=1
    )
    db.add(ch)
    db.flush()

    loc = ChallengeLocation(
        challenge_id=ch.id,
        district_id=dist.id,
        district_name=district_name,
        block_name="Angara",
        village_or_city="Getalsud"
    )
    db.add(loc)
    db.commit()
    db.refresh(ch)
    return ch


def _get_or_create_university(db: Session, admin_user: User, univ_name: str = "Birsa Agricultural University") -> University:
    univ = db.query(University).filter(University.institution_name == univ_name).first()
    if not univ:
        u_user = _get_or_create_user(db, f"univ_{uuid.uuid4().hex[:4]}@bau.ac.in", UserRole.UNIVERSITY, univ_name)
        univ = University(
            user_id=u_user.id,
            institution_name=univ_name,
            district_name="Ranchi",
            has_incubation_center=True
        )
        db.add(univ)
        db.commit()
        db.refresh(univ)

    # Ensure organization profile exists
    org = db.query(OrganizationProfile).filter(OrganizationProfile.user_id == univ.user_id).first()
    if not org:
        org = OrganizationProfile(
            user_id=univ.user_id,
            legal_name=univ.institution_name,
            org_type="UNIVERSITY",
            official_email=f"contact@{uuid.uuid4().hex[:4]}.ac.in",
            district_name="Ranchi",
            verification_status="VERIFIED"
        )
        db.add(org)
        db.commit()

    return univ


# ============================================================================
# 1. State Machine Transitions Matrix (Table-Driven Legal & Illegal Transitions)
# ============================================================================

def test_challenge_full_lifecycle_transitions(client, db):
    """Verifies complete legal progression through all Stage 4 workflow states."""
    gov_admin = _get_or_create_user(db, "state_admin_s4@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "State Admin", tier="STATE")
    citizen = _get_or_create_user(db, "citizen_s4@jharkhand.gov.in", UserRole.CITIZEN, "Citizen S4")
    univ = _get_or_create_university(db, gov_admin)
    univ_user = db.query(User).filter(User.id == univ.user_id).first()

    ch = _create_test_challenge(db, citizen, "Ranchi")
    admin_hdr = _headers_for(gov_admin)
    univ_hdr = _headers_for(univ_user)

    assert ch.status == ChallengeStatus.SUBMITTED

    # 1. SUBMITTED -> UNDER_REVIEW
    res = client.post(f"/api/v1/challenges/{ch.id}/accept-review", json={"notes": "Intake accepted"}, headers=admin_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.UNDER_REVIEW

    # 2. UNDER_REVIEW -> VALIDATED
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "VALIDATED", "remarks": "Officially validated"}, headers=admin_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.VALIDATED

    # 3. VALIDATED -> UNIVERSITY_ASSIGNED (via explicit allocation)
    res = client.post(f"/api/v1/challenges/{ch.id}/assign", json={"university_id": univ.id, "deadline_days": 10}, headers=admin_hdr)
    assert res.status_code == 200
    alloc_id = res.json()["allocation_id"]
    db.refresh(ch)
    assert ch.status == ChallengeStatus.UNIVERSITY_ASSIGNED

    # 4. UNIVERSITY_ASSIGNED -> TEAM_FORMED (University accepts allocation)
    res = client.post(f"/api/v1/challenges/allocations/{alloc_id}/respond", json={"decision": "ACCEPT", "coi_declared": True, "notes": "Capacity confirmed"}, headers=univ_hdr)
    assert res.status_code == 200
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "TEAM_FORMED", "remarks": "Faculty mobilized"}, headers=univ_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.TEAM_FORMED

    # 5. TEAM_FORMED -> SOLUTION_PROPOSED
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "SOLUTION_PROPOSED", "remarks": "Technical schematics ready"}, headers=univ_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.SOLUTION_PROPOSED

    # 6. SOLUTION_PROPOSED -> APPROVED
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "APPROVED", "remarks": "Proposal cleared by dept"}, headers=admin_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.APPROVED

    # 7. APPROVED -> PROTOTYPE
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "PROTOTYPE", "remarks": "Lab prototype built"}, headers=univ_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.PROTOTYPE

    # 8. PROTOTYPE -> FIELD_TESTING
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "FIELD_TESTING", "remarks": "Pilot testing at village"}, headers=univ_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.FIELD_TESTING

    # 9. FIELD_TESTING -> DEPLOYMENT
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "DEPLOYMENT", "remarks": "Community deployment completed"}, headers=univ_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.DEPLOYMENT

    # 10. DEPLOYMENT -> FIELD_VERIFICATION
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "FIELD_VERIFICATION", "remarks": "Ready for field inspection"}, headers=univ_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.FIELD_VERIFICATION

    # 11. FIELD_VERIFICATION -> RESOLVED
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "RESOLVED", "remarks": "Officer verified water flow"}, headers=admin_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.RESOLVED

    # 12. RESOLVED -> IMPACT_AUDITED
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "IMPACT_AUDITED", "remarks": "Beneficiary count verified"}, headers=admin_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.IMPACT_AUDITED

    # 13. IMPACT_AUDITED -> CLOSED
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "CLOSED", "remarks": "Fully resolved and audited"}, headers=admin_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.CLOSED


@pytest.mark.parametrize("from_status, illegal_target", [
    (ChallengeStatus.SUBMITTED, ChallengeStatus.CLOSED),
    (ChallengeStatus.SUBMITTED, ChallengeStatus.PROTOTYPE),
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.DEPLOYMENT),
    (ChallengeStatus.VALIDATED, ChallengeStatus.RESOLVED),
    (ChallengeStatus.REJECTED, ChallengeStatus.FIELD_TESTING),
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.FIELD_VERIFICATION),
])
def test_illegal_state_transitions_rejected(client, db, from_status, illegal_target):
    """Ensures illegal state transitions are blocked with HTTP 400 Bad Request."""
    gov_admin = _get_or_create_user(db, "admin_illegal@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "State Admin")
    citizen = _get_or_create_user(db, "citizen_illegal@jharkhand.gov.in", UserRole.CITIZEN, "Citizen")
    ch = _create_test_challenge(db, citizen)
    ch.status = from_status
    db.commit()

    admin_hdr = _headers_for(gov_admin)
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": illegal_target.value}, headers=admin_hdr)
    assert res.status_code == 400
    assert "Illegal state transition" in res.json()["detail"]


def test_unauthorized_role_transition_rejected(client, db):
    """Ensures actors without required roles are rejected with HTTP 403 Forbidden."""
    citizen = _get_or_create_user(db, "citizen_unauth@jharkhand.gov.in", UserRole.CITIZEN, "Citizen")
    ch = _create_test_challenge(db, citizen)
    ch.status = ChallengeStatus.UNDER_REVIEW
    db.commit()

    cit_hdr = _headers_for(citizen)
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "VALIDATED"}, headers=cit_hdr)
    assert res.status_code == 403
    assert "not authorized" in res.json()["detail"]


# ============================================================================
# 2. Clarification Flow (NEEDS_MORE_INFO <-> UNDER_REVIEW)
# ============================================================================

def test_clarification_cycle(client, db):
    """Tests the government clarification request and citizen response cycle."""
    gov_admin = _get_or_create_user(db, "admin_clarify@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "Admin Clarify")
    citizen = _get_or_create_user(db, "citizen_clarify@jharkhand.gov.in", UserRole.CITIZEN, "Citizen Clarify")
    ch = _create_test_challenge(db, citizen)
    ch.status = ChallengeStatus.UNDER_REVIEW
    db.commit()

    admin_hdr = _headers_for(gov_admin)
    cit_hdr = _headers_for(citizen)

    # Officer requests clarification
    res = client.post(
        f"/api/v1/challenges/{ch.id}/request-info",
        json={"clarification_items": ["Specify exact pump model", "Number of affected households"], "notes": "Need more data"},
        headers=admin_hdr
    )
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.NEEDS_MORE_INFO

    # Citizen submits clarification
    res = client.post(
        f"/api/v1/challenges/{ch.id}/submit-info",
        json={"responses": {"pump_model": "Kirloskar 5HP", "households": 120}},
        headers=cit_hdr
    )
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.UNDER_REVIEW


# ============================================================================
# 3. Jurisdictional Moderation Enforcement
# ============================================================================

def test_jurisdictional_moderation_enforcement(client, db):
    """Enforces that district officers cannot moderate challenges outside their assigned district."""
    ranchi_officer = _get_or_create_user(db, "ranchi_officer@jharkhand.gov.in", UserRole.GOVERNMENT_OFFICER, "Ranchi Officer", tier="DISTRICT", district="Ranchi")
    dhanbad_officer = _get_or_create_user(db, "dhanbad_officer@jharkhand.gov.in", UserRole.GOVERNMENT_OFFICER, "Dhanbad Officer", tier="DISTRICT", district="Dhanbad")
    citizen = _get_or_create_user(db, "citizen_ranchi@jharkhand.gov.in", UserRole.CITIZEN, "Citizen")

    # Challenge is located in Ranchi
    ch = _create_test_challenge(db, citizen, "Ranchi")
    ch.status = ChallengeStatus.UNDER_REVIEW
    db.commit()

    # Dhanbad officer attempts to validate Ranchi challenge -> 403 Forbidden
    dhanbad_hdr = _headers_for(dhanbad_officer)
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "VALIDATED"}, headers=dhanbad_hdr)
    assert res.status_code == 403
    assert "Jurisdiction mismatch" in res.json()["detail"] or "Forbidden" in res.json()["detail"]

    # Ranchi officer validates Ranchi challenge -> 200 OK
    ranchi_hdr = _headers_for(ranchi_officer)
    res = client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "VALIDATED"}, headers=ranchi_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.VALIDATED


# ============================================================================
# 4. Optimistic Concurrency Control (Version Tokens & Conflict Handling)
# ============================================================================

def test_optimistic_concurrency_control(client, db):
    """Verifies that version collisions trigger HTTP 409 Conflict with a reload URL."""
    gov_admin = _get_or_create_user(db, "admin_occ@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "Admin OCC")
    citizen = _get_or_create_user(db, "citizen_occ@jharkhand.gov.in", UserRole.CITIZEN, "Citizen OCC")
    ch = _create_test_challenge(db, citizen)
    ch.status = ChallengeStatus.UNDER_REVIEW
    ch.version = 1
    db.commit()

    admin_hdr = _headers_for(gov_admin)

    # Actor A succeeds with correct version 1 -> version increments to 2
    res_a = client.post(
        f"/api/v1/challenges/{ch.id}/status",
        json={"status": "VALIDATED", "expected_version": 1},
        headers=admin_hdr
    )
    assert res_a.status_code == 200
    db.refresh(ch)
    assert ch.version == 2

    # Actor B attempts to mutate using stale expected_version 1 -> 409 Conflict
    res_b = client.post(
        f"/api/v1/challenges/{ch.id}/status",
        json={"status": "UNDER_REVIEW", "expected_version": 1},
        headers=admin_hdr
    )
    assert res_b.status_code == 409
    body = res_b.json()["detail"]
    assert body["error"] == "VERSION_CONFLICT"
    assert body["current_version"] == 2
    assert f"/api/v1/challenges/{ch.id}" in body["reload_url"]


# ============================================================================
# 5. Explicit Challenge Allocation & Conflict-of-Interest (CoI)
# ============================================================================

def test_allocation_coi_and_decline_workflow(client, db):
    """Verifies explicit allocation records, mandatory CoI, and decline-reassignment behavior."""
    gov_admin = _get_or_create_user(db, "admin_alloc@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "Admin Alloc")
    citizen = _get_or_create_user(db, "citizen_alloc@jharkhand.gov.in", UserRole.CITIZEN, "Citizen Alloc")
    univ = _get_or_create_university(db, gov_admin, "Ranchi Institute of Technology")
    univ_user = db.query(User).filter(User.id == univ.user_id).first()

    ch = _create_test_challenge(db, citizen)
    ch.status = ChallengeStatus.VALIDATED
    db.commit()

    admin_hdr = _headers_for(gov_admin)
    univ_hdr = _headers_for(univ_user)

    # 1. Government assigns challenge -> creates ChallengeAllocation
    res = client.post(
        f"/api/v1/challenges/{ch.id}/assign",
        json={"university_id": univ.id, "deadline_days": 14, "capacity_notes": "Hydrology lab qualified"},
        headers=admin_hdr
    )
    assert res.status_code == 200
    alloc_id = res.json()["allocation_id"]

    alloc = db.query(ChallengeAllocation).filter(ChallengeAllocation.id == alloc_id).first()
    assert alloc.status == AllocationStatus.OFFERED
    assert alloc.coi_declared is False

    # 2. University attempts to accept WITHOUT CoI declaration -> 400 Bad Request
    res_no_coi = client.post(
        f"/api/v1/challenges/allocations/{alloc_id}/respond",
        json={"decision": "ACCEPT", "coi_declared": False},
        headers=univ_hdr
    )
    assert res_no_coi.status_code == 400
    assert "Conflict of interest" in res_no_coi.json()["detail"]

    # 3. University declines allocation -> reverts challenge back to VALIDATED
    res_decline = client.post(
        f"/api/v1/challenges/allocations/{alloc_id}/respond",
        json={"decision": "DECLINE", "notes": "All senior faculty occupied with semester exams"},
        headers=univ_hdr
    )
    assert res_decline.status_code == 200
    db.refresh(alloc)
    db.refresh(ch)
    assert alloc.status == AllocationStatus.DECLINED
    assert ch.status == ChallengeStatus.VALIDATED
    assert ch.assigned_university_id is None


# ============================================================================
# 6. Duplicates, False Similarity (Keep Separate) & Controlled Rejection
# ============================================================================

def test_duplicate_keep_separate_and_rejection(client, db):
    """Tests duplicate confirmation, dismissing false duplicates, and controlled rejection."""
    gov_admin = _get_or_create_user(db, "admin_moderation@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "Admin Mod")
    citizen = _get_or_create_user(db, "citizen_mod@jharkhand.gov.in", UserRole.CITIZEN, "Citizen Mod")

    ch_canonical = _create_test_challenge(db, citizen)
    ch_canonical.status = ChallengeStatus.UNDER_REVIEW
    ch_duplicate = _create_test_challenge(db, citizen)
    ch_duplicate.status = ChallengeStatus.UNDER_REVIEW
    ch_separate = _create_test_challenge(db, citizen)
    ch_separate.status = ChallengeStatus.UNDER_REVIEW
    db.commit()

    admin_hdr = _headers_for(gov_admin)

    # 1. Confirm duplicate
    res_dup = client.post(
        f"/api/v1/challenges/{ch_duplicate.id}/duplicate",
        json={"canonical_challenge_id": ch_canonical.id, "remarks": "Exact duplicate pump location"},
        headers=admin_hdr
    )
    assert res_dup.status_code == 200
    db.refresh(ch_duplicate)
    assert ch_duplicate.status == ChallengeStatus.DUPLICATE
    assert f"Duplicate of #{ch_canonical.id}" in ch_duplicate.moderation_reason

    # 2. Keep separate (dismiss false duplicate candidate)
    res_sep = client.post(
        f"/api/v1/challenges/{ch_separate.id}/keep-separate",
        json={"compared_challenge_id": ch_canonical.id, "justification": "Different aquifer source 10km away"},
        headers=admin_hdr
    )
    assert res_sep.status_code == 200
    db.refresh(ch_separate)
    assert ch_separate.status == ChallengeStatus.UNDER_REVIEW  # Status unchanged

    # 3. Controlled rejection
    res_rej = client.post(
        f"/api/v1/challenges/{ch_separate.id}/reject",
        json={"reason": "Water resource issue is commercially viable and managed by private entity", "reason_code": "COMMERCIALLY_VIABLE_EXISTING_SERVICE"},
        headers=admin_hdr
    )
    assert res_rej.status_code == 200
    db.refresh(ch_separate)
    assert ch_separate.status == ChallengeStatus.REJECTED
    assert "[COMMERCIALLY_VIABLE_EXISTING_SERVICE]" in ch_separate.moderation_reason


# ============================================================================
# 7. Pause, Resume, Reopen & Appeals
# ============================================================================

def test_pause_resume_reopen_appeal_workflow(client, db):
    """Tests administrative pause, resume, reopening, and citizen appeals."""
    gov_admin = _get_or_create_user(db, "admin_pause@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "Admin Pause")
    citizen = _get_or_create_user(db, "citizen_pause@jharkhand.gov.in", UserRole.CITIZEN, "Citizen Pause")

    ch = _create_test_challenge(db, citizen)
    ch.status = ChallengeStatus.UNDER_REVIEW
    db.commit()

    admin_hdr = _headers_for(gov_admin)
    cit_hdr = _headers_for(citizen)

    # 1. Pause challenge
    res = client.post(f"/api/v1/challenges/{ch.id}/pause", json={"reason": "Pending local PRI elections"}, headers=admin_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.PAUSED

    # 2. Resume challenge
    res = client.post(f"/api/v1/challenges/{ch.id}/resume", json={"remarks": "Elections concluded, resuming triage"}, headers=admin_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.UNDER_REVIEW

    # 3. Reject challenge
    res = client.post(f"/api/v1/challenges/{ch.id}/reject", json={"reason": "Lack of detail", "reason_code": "INSUFFICIENT_INFORMATION"}, headers=admin_hdr)
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.REJECTED

    # 4. Citizen appeals rejected challenge
    res = client.post(
        f"/api/v1/challenges/{ch.id}/appeal",
        json={"grounds": "Attached additional groundwater survey confirming dry borehole"},
        headers=cit_hdr
    )
    assert res.status_code == 200
    db.refresh(ch)
    assert ch.status == ChallengeStatus.UNDER_REVIEW


# ============================================================================
# 8. Cryptographic Tamper-Evident Audit Chain & Tamper Detection
# ============================================================================

def test_cryptographic_tamper_detection(client, db):
    """Tests SHA-256 hash chaining and mathematical tamper detection."""
    gov_admin = _get_or_create_user(db, "admin_tamper@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "Admin Tamper")
    citizen = _get_or_create_user(db, "citizen_tamper@jharkhand.gov.in", UserRole.CITIZEN, "Citizen Tamper")

    ch = _create_test_challenge(db, citizen)
    admin_hdr = _headers_for(gov_admin)

    # Perform operations to create chain entries
    client.post(f"/api/v1/challenges/{ch.id}/accept-review", json={"notes": "Triage 1"}, headers=admin_hdr)
    client.post(f"/api/v1/challenges/{ch.id}/status", json={"status": "VALIDATED", "remarks": "Validated 1"}, headers=admin_hdr)

    # 1. Untampered check: ledger must be valid
    verify_res = client.get("/api/v1/admin/audit-events/verify", headers=admin_hdr)
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is True
    assert verify_res.json()["tampered_sequence"] is None

    # 2. Tamper simulation: mutate an event's payload directly in the database
    event_to_tamper = db.query(DomainAuditEvent).order_by(DomainAuditEvent.sequence_number.desc()).first()
    original_payload = event_to_tamper.payload_json
    event_to_tamper.payload_json = '{"tampered": "illegal_modification"}'
    db.commit()

    # 3. Audit verification must detect the break
    verify_tampered = client.get("/api/v1/admin/audit-events/verify", headers=admin_hdr)
    assert verify_tampered.status_code == 200
    tamper_report = verify_tampered.json()
    assert tamper_report["is_valid"] is False
    assert tamper_report["tampered_sequence"] == event_to_tamper.sequence_number

    # Restore ledger for clean state
    event_to_tamper.payload_json = original_payload
    db.commit()

    # Verify restored ledger
    verify_restored = client.get("/api/v1/admin/audit-events/verify", headers=admin_hdr)
    assert verify_restored.json()["is_valid"] is True


# ============================================================================
# 9. Public Redaction of Sensitive Administrative History
# ============================================================================

def test_public_history_redaction(client, db):
    """Verifies that public callers receive sanitized notes while officers see full logs."""
    gov_admin = _get_or_create_user(db, "admin_redact@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "Admin Redact")
    citizen = _get_or_create_user(db, "citizen_redact@jharkhand.gov.in", UserRole.CITIZEN, "Citizen Redact")

    ch = _create_test_challenge(db, citizen)
    admin_hdr = _headers_for(gov_admin)
    cit_hdr = _headers_for(citizen)

    # Officer records an internal administrative action
    client.post(
        f"/api/v1/challenges/{ch.id}/keep-separate",
        json={"compared_challenge_id": 9999, "justification": "Internal investigation showed no correlation"},
        headers=admin_hdr
    )

    # 1. Unauthenticated or citizen caller views history -> internal notes are redacted
    pub_res = client.get(f"/api/v1/challenges/{ch.id}/history", headers=cit_hdr)
    assert pub_res.status_code == 200
    pub_logs = pub_res.json()
    assert len(pub_logs) > 0
    internal_entries = [log for log in pub_logs if log.get("action") == "DISMISS_DUPLICATE_CANDIDATE"]
    if internal_entries:
        assert internal_entries[0]["notes"] == "[Confidential Administrative Review]"

    # 2. Privileged officer views history -> full confidential notes are visible
    priv_res = client.get(f"/api/v1/challenges/{ch.id}/history", headers=admin_hdr)
    assert priv_res.status_code == 200
    priv_logs = priv_res.json()
    internal_priv = [log for log in priv_logs if log.get("action") == "DISMISS_DUPLICATE_CANDIDATE"]
    if internal_priv:
        assert "Internal investigation" in internal_priv[0]["notes"]
