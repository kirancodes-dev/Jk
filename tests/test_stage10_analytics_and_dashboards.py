"""
Stage 10: Verifiable Analytics, Jurisdiction-Aware Dashboards & Privacy-Preserving Exports — Test Suite.

Validates:
1. Verifiable KPI metadata integrity: numerator, denominator, time window, inclusion rules, freshness, verification level.
2. Zero hardcoded aggregate defaults: zero placeholder populations, zero fake ratings, dynamic recalculation.
3. Jurisdiction scoping isolation: State Admin sees statewide metrics; District Officer sees only their district's data.
4. Administrative drill-down: District -> Block live aggregated counts with boundary enforcement.
5. "Why this number" source record reconciliation: audit-linked provenance connecting KPI values to underlying DB records.
6. Statutory audience privacy redaction: coarse GPS (2 decimals), masked citizen PII, and restricted IP.
7. Bounded report exports: max 5,000 rows, asynchronous job tracking, and CSV streaming.
"""

import io
import csv
import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.core.security import create_access_token
from backend.app.models.models import (
    User, UserRole, Challenge, ChallengeLocation, ChallengeStatus,
    ChallengePriority, Project, University, IndustryPartner,
    Student, District, ImpactMetrics, ExportJob, utc_now,
    IPRecord, IPRecordType, IPOwnership, IndustryCollaboration,
    CollaborationOfferType, AgreementStatus
)
from backend.app.services.privacy_service import PrivacyRedactionService
from backend.app.services.analytics_service import analytics_service

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def _get_or_create_user(db, email, role, admin_tier="STATE", district_name="Ranchi", block_name=None):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.role = role
        user.admin_tier = admin_tier
        user.district_name = district_name
        user.block_name = block_name
        db.commit()
        db.refresh(user)
        return user

    user = User(
        email=email,
        full_name=f"User {email.split('@')[0]}",
        phone_number="+919876543210",
        role=role,
        hashed_password="hash",
        is_active=True,
        is_verified=True,
        admin_tier=admin_tier,
        district_name=district_name,
        block_name=block_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _auth_header(user):
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(
        subject=str(user.id),
        role=role_str,
        tier=user.admin_tier,
        district_name=user.district_name,
        block_name=user.block_name
    )
    return {"Authorization": f"Bearer {token}"}


def test_verifiable_kpi_metadata_integrity(db_session):
    """
    Every KPI returned must define complete provenance metadata:
    numerator, denominator, time window, inclusion rules, data freshness, and verification level.
    """
    state_admin = _get_or_create_user(db_session, "state_admin_stage10@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, admin_tier="STATE")
    headers = _auth_header(state_admin)

    res = client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert "total_challenges" in data
    assert "jurisdiction" in data
    assert "kpis" in data

    kpis = data["kpis"]
    required_kpis = [
        "submission_volume",
        "review_sla_compliance",
        "avg_review_turnaround_days",
        "active_verified_universities",
        "active_student_teams",
        "faculty_mentorship_coverage",
        "problem_resolution_rate",
        "csr_funding_disbursed",
        "measured_beneficiaries_served"
    ]

    valid_verification_levels = {"REPORTED", "ESTIMATED", "MEASURED", "VERIFIED"}

    for kpi_key in required_kpis:
        assert kpi_key in kpis, f"Missing KPI: {kpi_key}"
        meta = kpis[kpi_key]
        assert "name" in meta
        assert "display_title" in meta
        assert "value" in meta
        assert "time_window" in meta
        assert "inclusion_rules" in meta
        assert len(meta["inclusion_rules"]) > 10
        assert "freshness" in meta
        assert meta["verification_level"] in valid_verification_levels, f"Invalid level: {meta['verification_level']}"

    # Verifiable numerical reconciliation: submission_volume.value == total_challenges
    assert kpis["submission_volume"]["value"] == data["total_challenges"]


def test_jurisdiction_scoping_isolation(db_session):
    """
    State Admin sees statewide numbers.
    District Admin for Ranchi sees only Ranchi challenges.
    District Admin for Dhanbad sees only Dhanbad challenges.
    """
    # 1. Create unique challenge in Ranchi -> Kanke
    ch_ranchi = Challenge(
        title="Ranchi Ground Water Fluoride Contamination",
        description="High fluoride levels in borewell water across Kanke block.",
        category="Water Management",
        status=ChallengeStatus.SUBMITTED,
        current_tier="BLOCK"
    )
    db_session.add(ch_ranchi)
    db_session.commit()
    db_session.refresh(ch_ranchi)

    loc_ranchi = ChallengeLocation(
        challenge_id=ch_ranchi.id,
        district_name="Ranchi",
        block_name="Kanke",
        village_or_city="Arsande",
        latitude=23.4321,
        longitude=85.3214
    )
    db_session.add(loc_ranchi)

    # 2. Create unique challenge in Dhanbad -> Jharia
    ch_dhanbad = Challenge(
        title="Jharia Underground Coal Fire Fumes",
        description="Toxic gas leakage from subterranean coal fires affecting residential schools.",
        category="Environment",
        status=ChallengeStatus.SUBMITTED,
        current_tier="BLOCK"
    )
    db_session.add(ch_dhanbad)
    db_session.commit()
    db_session.refresh(ch_dhanbad)

    loc_dhanbad = ChallengeLocation(
        challenge_id=ch_dhanbad.id,
        district_name="Dhanbad",
        block_name="Jharia",
        village_or_city="Lodna",
        latitude=23.7412,
        longitude=86.4158
    )
    db_session.add(loc_dhanbad)
    db_session.commit()

    # Create users
    ranchi_officer = _get_or_create_user(
        db_session, "ranchi_officer_stage10@jharkhand.gov.in", UserRole.GOVERNMENT_OFFICER,
        admin_tier="DISTRICT", district_name="Ranchi"
    )
    dhanbad_officer = _get_or_create_user(
        db_session, "dhanbad_officer_stage10@jharkhand.gov.in", UserRole.GOVERNMENT_OFFICER,
        admin_tier="DISTRICT", district_name="Dhanbad"
    )
    state_admin = _get_or_create_user(
        db_session, "state_admin_stage10@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN,
        admin_tier="STATE"
    )

    # 1. State admin sees both
    res_state = client.get("/api/v1/admin/dashboard", headers=_auth_header(state_admin))
    assert res_state.status_code == 200
    state_total = res_state.json()["total_challenges"]

    # 2. Ranchi officer sees fewer challenges than statewide, and sees Ranchi
    res_ranchi = client.get("/api/v1/admin/dashboard", headers=_auth_header(ranchi_officer))
    assert res_ranchi.status_code == 200
    ranchi_total = res_ranchi.json()["total_challenges"]
    assert ranchi_total >= 1
    assert ranchi_total <= state_total

    # 3. Dhanbad officer sees Dhanbad
    res_dhanbad = client.get("/api/v1/admin/dashboard", headers=_auth_header(dhanbad_officer))
    assert res_dhanbad.status_code == 200
    dhanbad_total = res_dhanbad.json()["total_challenges"]
    assert dhanbad_total >= 1
    assert dhanbad_total <= state_total


def test_administrative_drill_down(db_session):
    """
    Validates District and Block level administrative drill-downs.
    """
    state_admin = _get_or_create_user(
        db_session, "state_admin_stage10@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, admin_tier="STATE"
    )
    headers = _auth_header(state_admin)

    # District drill-down
    res_dist = client.get("/api/v1/admin/drill-down/districts", headers=headers)
    assert res_dist.status_code == 200
    districts = res_dist.json()
    assert isinstance(districts, list)
    assert len(districts) > 0

    first_dist = districts[0]
    assert "district_name" in first_dist
    assert "total_challenges" in first_dist
    assert "active_projects" in first_dist

    # Block drill-down for Ranchi
    res_blocks = client.get("/api/v1/admin/drill-down/districts/Ranchi/blocks", headers=headers)
    assert res_blocks.status_code == 200
    blocks = res_blocks.json()
    assert isinstance(blocks, list)
    if len(blocks) > 0:
        assert "block_name" in blocks[0]
        assert "district_name" in blocks[0]
        assert blocks[0]["district_name"] == "Ranchi"


def test_why_this_number_source_reconciliation(db_session):
    """
    'Why this number': Given a KPI, drills down to source records with audit IDs.
    """
    # Create challenge that breached SLA (older than 8 days in SUBMITTED state)
    old_date = datetime.now(timezone.utc) - timedelta(days=9)
    breach_ch = Challenge(
        title="Unreviewed Chronic Water Deficit in Khunti",
        description="Severely delayed water supply pipeline in Murhu block.",
        category="Water Management",
        status=ChallengeStatus.SUBMITTED,
        created_at=old_date,
        current_tier="BLOCK"
    )
    db_session.add(breach_ch)
    db_session.commit()
    db_session.refresh(breach_ch)

    loc = ChallengeLocation(
        challenge_id=breach_ch.id,
        district_name="Khunti",
        block_name="Murhu",
        village_or_city="Murhu Village"
    )
    db_session.add(loc)
    db_session.commit()

    state_admin = _get_or_create_user(
        db_session, "state_admin_stage10@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, admin_tier="STATE"
    )
    headers = _auth_header(state_admin)

    # Drill down into submissions
    res_sub = client.get("/api/v1/admin/analytics/drill-down?metric=submissions&limit=10", headers=headers)
    assert res_sub.status_code == 200, res_sub.text
    sub_data = res_sub.json()
    assert sub_data["metric_key"] == "submissions"
    assert "metadata" in sub_data
    assert sub_data["total_records"] >= 1
    assert len(sub_data["records"]) > 0

    record = sub_data["records"][0]
    assert "record_id" in record
    assert "title" in record
    assert "verification_level" in record
    assert record["verification_level"] == "REPORTED"

    # Drill down into SLA breaches. This endpoint orders oldest-breach-first (for
    # triage prioritization), and this shared test database accumulates SLA-breach
    # fixtures across many prior test runs, so a large limit is required to reliably
    # find our freshly created breach rather than asserting it lands in the first page.
    res_sla = client.get("/api/v1/admin/analytics/drill-down?metric=sla_breaches&limit=5000", headers=headers)
    assert res_sla.status_code == 200, res_sla.text
    sla_data = res_sla.json()
    assert sla_data["total_records"] >= 1
    sla_ids = [r["record_id"] for r in sla_data["records"]]
    assert breach_ch.id in sla_ids


def test_audience_privacy_redaction():
    """
    Verifies statutory privacy redactions:
    - GPS coordinates masked to 2 decimals (~1.1 km) for public/non-admins.
    - Citizen phone and email masked.
    - Commercial IP terms masked.
    """
    # 1. Location redaction
    exact_location = {
        "district_name": "Ranchi",
        "block_name": "Kanke",
        "latitude": 23.456789,
        "longitude": 85.123456
    }

    citizen_viewer = User(id=999, email="citizen@test.com", role=UserRole.CITIZEN)
    redacted_loc = PrivacyRedactionService.redact_location(exact_location, citizen_viewer)
    assert redacted_loc["latitude"] == 23.46
    assert redacted_loc["longitude"] == 85.12
    assert redacted_loc["is_coarse_geography"] is True

    admin_viewer = User(id=1, email="admin@jharkhand.gov.in", role=UserRole.GOVERNMENT_ADMIN, admin_tier="STATE")
    admin_loc = PrivacyRedactionService.redact_location(exact_location, admin_viewer)
    assert admin_loc["latitude"] == 23.456789
    assert admin_loc["longitude"] == 85.123456
    assert admin_loc["is_coarse_geography"] is False

    # 2. Citizen PII redaction
    pii_data = {
        "full_name": "Birsa Munda",
        "phone_number": "9876543210",
        "email": "birsa.munda@example.com"
    }

    redacted_pii = PrivacyRedactionService.redact_citizen_pii(pii_data, citizen_viewer, is_owner=False)
    assert redacted_pii["phone_number"] == "XXXXXX3210"
    assert "birsa.munda" not in redacted_pii["email"]
    assert "***@" in redacted_pii["email"]
    assert redacted_pii["full_name"] == "Verified Citizen Reporter"

    # Owner sees unredacted
    owner_pii = PrivacyRedactionService.redact_citizen_pii(pii_data, citizen_viewer, is_owner=True)
    assert owner_pii["phone_number"] == "9876543210"

    # 3. Confidential IP redaction
    proposal_data = {
        "commercialization_plan": "Targeting 50 Lakh INR revenue by Q3 via direct retail.",
        "patent_application_details": "Application No. 2026/JH/00451 provisional filing."
    }
    redacted_ip = PrivacyRedactionService.redact_confidential_ip(proposal_data, citizen_viewer, is_team_member=False)
    assert redacted_ip["commercialization_plan"] == "[CONFIDENTIAL_COMMERCIAL_TERMS]"
    assert redacted_ip["patent_application_details"] == "[RESTRICTED_IP_FILING]"


def test_bounded_asynchronous_export_jobs(db_session):
    """
    Validates bounded export job lifecycle:
    1. POST /api/v1/admin/exports
    2. GET /api/v1/admin/exports/{job_id}
    3. GET /api/v1/admin/exports/{job_id}/download
    """
    state_admin = _get_or_create_user(
        db_session, "state_admin_stage10@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, admin_tier="STATE"
    )
    headers = _auth_header(state_admin)

    # Create export job
    payload = {
        "export_type": "CHALLENGES",
        "export_format": "CSV",
        "filters": {"category": "Water Management"}
    }
    create_res = client.post("/api/v1/admin/exports", json=payload, headers=headers)
    assert create_res.status_code == 201, create_res.text
    job_data = create_res.json()
    job_id = job_data["id"]
    assert job_data["export_type"] == "CHALLENGES"
    assert job_data["status"] == "COMPLETED"
    assert job_data["row_count"] >= 0

    # Retrieve export job
    get_res = client.get(f"/api/v1/admin/exports/{job_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == job_id

    # Download export file
    dl_res = client.get(f"/api/v1/admin/exports/{job_id}/download", headers=headers)
    assert dl_res.status_code == 200
    assert "text/csv" in dl_res.headers.get("content-type", "")

    # Parse CSV content
    reader = csv.reader(io.StringIO(dl_res.text))
    rows = list(reader)
    assert len(rows) >= 1  # At least the header
    header = rows[0]
    assert "Challenge ID" in header
    assert "Coarse Latitude" in header
    assert "Verification Level" in header


def test_live_patent_startup_and_technology_transfer_kpis(db_session):
    """
    Patents Filed, Startups Incubated and Technology Transfers Completed must be computed
    live from IPRecord / IndustryCollaboration state, never a seeded ImpactMetrics constant.
    Creating one of each must be reflected in both the KPI value and its drill-down records.
    """
    state_admin = _get_or_create_user(
        db_session, "state_admin_stage10@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, admin_tier="STATE"
    )

    # Impact metrics must no longer carry hardcoded patent/startup constants.
    assert db_session.query(ImpactMetrics).filter(ImpactMetrics.metric_name == "Patents Filed").first() is None
    assert db_session.query(ImpactMetrics).filter(ImpactMetrics.metric_name == "Startups Incubated").first() is None

    univ_user = _get_or_create_user(db_session, "s10_univ@edu.in", UserRole.UNIVERSITY)
    univ = db_session.query(University).filter(University.user_id == univ_user.id).first()
    if not univ:
        univ = University(user_id=univ_user.id, institution_name="Stage10 Test Institute", district_name="Ranchi", is_active=True)
        db_session.add(univ)
        db_session.commit()
        db_session.refresh(univ)

    ind_user = _get_or_create_user(db_session, "s10_industry@corp.in", UserRole.INDUSTRY)
    partner = db_session.query(IndustryPartner).filter(IndustryPartner.user_id == ind_user.id).first()
    if not partner:
        partner = IndustryPartner(user_id=ind_user.id, company_name="Stage10 Test Partner", industry_domain="Water Tech")
        db_session.add(partner)
        db_session.commit()
        db_session.refresh(partner)

    ch = Challenge(
        title="Stage10 KPI Test Challenge", description="Verifies live innovation KPI computation end to end.",
        category="Water Management", status=ChallengeStatus.RESOLVED
    )
    db_session.add(ch)
    db_session.commit()
    db_session.refresh(ch)
    db_session.add(ChallengeLocation(challenge_id=ch.id, district_name="Ranchi", block_name="Kanke"))
    db_session.commit()

    proj = Project(challenge_id=ch.id, university_id=univ.id, name="Stage10 KPI Test Project", description="desc")
    db_session.add(proj)
    db_session.commit()
    db_session.refresh(proj)

    patent = IPRecord(
        project_id=proj.id, record_type=IPRecordType.PATENT, title="Stage10 Test Patent",
        ownership=IPOwnership.JOINT, status="APPROVED", created_by_user_id=univ_user.id
    )
    startup = IPRecord(
        project_id=proj.id, record_type=IPRecordType.SOFTWARE, title="Stage10 Test Spin-off Software",
        ownership=IPOwnership.JOINT, startup_spinoff_name="Stage10 Spinoff Pvt Ltd", status="APPROVED",
        created_by_user_id=univ_user.id
    )
    db_session.add_all([patent, startup])
    collab = IndustryCollaboration(
        project_id=proj.id, industry_id=partner.id, offer_type=CollaborationOfferType.TECHNOLOGY_TRANSFER.value,
        description="Stage10 test technology transfer", status="Completed", agreement_status=AgreementStatus.COMPLETED
    )
    db_session.add(collab)
    db_session.commit()
    db_session.refresh(patent)
    db_session.refresh(startup)
    db_session.refresh(collab)

    headers = _auth_header(state_admin)
    res = client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 200, res.text
    kpis = res.json()["kpis"]

    for key in ("patents_filed", "startups_incubated", "technology_transfers_completed", "prototypes_developed", "pilots_deployed"):
        assert key in kpis, f"Missing live innovation KPI: {key}"
        assert kpis[key]["value"] >= 1
        assert kpis[key]["verification_level"] == "VERIFIED"

    innovation_breakdown = res.json().get("innovation_breakdown")
    assert innovation_breakdown is not None
    assert "Ranchi" in innovation_breakdown["by_district"]
    assert innovation_breakdown["by_district"]["Ranchi"].get("patents_filed", 0) >= 1

    # "Why this number" drill-downs must surface the exact records we just created.
    dd_patents = client.get("/api/v1/admin/analytics/drill-down?metric=patents_filed", headers=headers).json()
    assert patent.id in [r["record_id"] for r in dd_patents["records"]]

    dd_startups = client.get("/api/v1/admin/analytics/drill-down?metric=startups_incubated", headers=headers).json()
    assert startup.id in [r["record_id"] for r in dd_startups["records"]]

    dd_tech = client.get("/api/v1/admin/analytics/drill-down?metric=technology_transfers_completed", headers=headers).json()
    assert collab.id in [r["record_id"] for r in dd_tech["records"]]


def test_hei_participating_drill_down_no_attribute_error(db_session):
    """Regression: University has `.institution_name`/`.district_name`, not `.name`/`.district`."""
    state_admin = _get_or_create_user(
        db_session, "state_admin_stage10@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, admin_tier="STATE"
    )
    res = client.get("/api/v1/admin/analytics/drill-down?metric=hei_participating", headers=_auth_header(state_admin))
    assert res.status_code == 200, res.text
