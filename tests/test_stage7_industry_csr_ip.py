"""
Stage 7: Verified Industry/Startup/CSR Partnership & IP Workflow — Automated Test Suite.

Validates:
1. Unverified or suspended partners cannot offer or accept support.
2. A partner cannot create a collaboration under another partner's identity, and
   cannot review a collaboration/project it has no access to.
3. Funding status never advances (release) without the required milestone approval
   and utilization evidence; payment is never claimed "confirmed" without a
   configured finance integration.
4. Agreement and IP changes are versioned and audited.
5. Private student research/source documents are not visible in public project
   discovery (redacted view).
"""

import io
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.core.security import create_access_token
from backend.app.models.models import (
    User, UserRole, University, Department, Faculty, Student, OrganizationProfile,
    Challenge, ChallengeLocation, ChallengeStatus, Citizen, Project, ProjectMilestone,
    MilestoneStatus, IndustryPartner, IndustryCollaboration, FundingRecord
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


def _mk_user(db, email, role, full_name="Test User", is_verified=True):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        email=email, full_name=full_name, phone_number="9000000001", role=role,
        hashed_password="hash", is_active=True, is_verified=is_verified, admin_tier="STATE"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _token(user):
    return create_access_token(subject=str(user.id), role=user.role.value)


AUTH = lambda tok: {"Authorization": f"Bearer {tok}"}


@pytest.fixture
def gov_admin(db_session):
    user = _mk_user(db_session, "s7_gov@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "Stage7 Gov Admin")
    return user, _token(user)


def _mk_verified_university(db, suffix):
    user = _mk_user(db, f"s7_univ_{suffix}@edu.in", UserRole.UNIVERSITY, f"University {suffix}")
    univ = db.query(University).filter(University.user_id == user.id).first()
    if not univ:
        univ = University(
            user_id=user.id, institution_name=f"Stage7 Institute {suffix}", district_name="Ranchi", is_active=True,
            capacity_max_active_projects=999
        )
        db.add(univ)
        db.commit()
        db.refresh(univ)
    elif univ.capacity_max_active_projects < 999:
        # Test-only headroom: this fixture's university is reused (by fixed email) across every
        # run of this suite against the persistent shared DB, and each run adds another project,
        # so the real default cap of 10 eventually makes old runs' accumulated projects break new ones.
        univ.capacity_max_active_projects = 999
        db.commit()
    org = db.query(OrganizationProfile).filter(OrganizationProfile.user_id == user.id).first()
    if not org:
        org = OrganizationProfile(
            user_id=user.id, legal_name=univ.institution_name, org_type="UNIVERSITY",
            official_email=user.email, district_name="Ranchi", verification_status="VERIFIED"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
    univ.organization_profile_id = org.id
    univ.is_active = True
    db.commit()
    db.refresh(univ)

    fac_user = _mk_user(db, f"s7_faculty_{suffix}@edu.in", UserRole.FACULTY_MENTOR, f"Faculty {suffix}")
    faculty = db.query(Faculty).filter(Faculty.user_id == fac_user.id).first()
    if not faculty:
        faculty = Faculty(user_id=fac_user.id, university_id=univ.id, designation="Professor", expertise="IoT")
        db.add(faculty)
        db.commit()
        db.refresh(faculty)

    return {"user": user, "token": _token(user), "univ": univ, "faculty": faculty, "faculty_token": _token(fac_user)}


def _mk_partner(db, suffix, verified=True, active=True, partner_type="INDUSTRY"):
    user = _mk_user(db, f"s7_partner_{suffix}@corp.in", UserRole.INDUSTRY, f"Partner Corp {suffix}")
    partner = db.query(IndustryPartner).filter(IndustryPartner.user_id == user.id).first()
    if not partner:
        partner = IndustryPartner(
            user_id=user.id, company_name=f"Partner Corp {suffix}", industry_domain="Water Tech",
            partner_type=partner_type, is_active=active
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)
    org = db.query(OrganizationProfile).filter(OrganizationProfile.user_id == user.id).first()
    if not org:
        org = OrganizationProfile(
            user_id=user.id, legal_name=partner.company_name, org_type="INDUSTRY",
            official_email=user.email, district_name="Ranchi",
            verification_status="VERIFIED" if verified else "PENDING"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
    partner.organization_profile_id = org.id
    partner.is_active = active
    db.commit()
    db.refresh(partner)
    return {"user": user, "token": _token(user), "partner": partner}


def _mk_challenge(db, actor_user, university=None):
    citizen_user = _mk_user(db, "s7_citizen@example.com", UserRole.CITIZEN, "Stage7 Citizen")
    citizen = db.query(Citizen).filter(Citizen.user_id == citizen_user.id).first()
    if not citizen:
        citizen = Citizen(user_id=citizen_user.id, district_name="Ranchi")
        db.add(citizen)
        db.commit()
        db.refresh(citizen)

    challenge = Challenge(
        title=f"Stage7 Industrial Effluent {actor_user.id}-{university.id if university else 0}",
        description="Industrial effluent treatment challenge requiring corporate technical support.",
        category="Environment", citizen_id=citizen.id, status=ChallengeStatus.VALIDATED, affected_population=800
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    db.add(ChallengeLocation(challenge_id=challenge.id, district_name="Ranchi", block_name="Kanke"))
    db.commit()
    db.refresh(challenge)

    if university is not None:
        challenge.assigned_university_id = university.id
        challenge.status = ChallengeStatus.TEAM_FORMED
        db.commit()
        db.refresh(challenge)
    return challenge


def _mk_project(db, university_token, challenge_id, name="Stage7 Project"):
    resp = client.post("/api/v1/projects", json={"challenge_id": challenge_id, "name": name, "description": "desc"}, headers=AUTH(university_token))
    assert resp.status_code == 201, resp.text
    return resp.json()


# =========================================================================
# 1. Unverified/suspended partners cannot offer or accept support
# =========================================================================

def test_unverified_partner_cannot_offer_collaboration(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "p1")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    project = _mk_project(db_session, home["token"], challenge.id, "P1")

    unverified_partner = _mk_partner(db_session, "unverified1", verified=False)

    resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations",
        json={"offer_type": "MENTORSHIP", "scope": "Technical mentorship for effluent sensors."},
        headers=AUTH(unverified_partner["token"])
    )
    assert resp.status_code == 403


def test_suspended_partner_cannot_offer_collaboration(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "p2")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    project = _mk_project(db_session, home["token"], challenge.id, "P2")

    suspended_partner = _mk_partner(db_session, "suspended1", verified=True, active=False)

    resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations",
        json={"offer_type": "FUNDING", "scope": "CSR funding for pilot deployment.", "cash_value": 50000},
        headers=AUTH(suspended_partner["token"])
    )
    assert resp.status_code == 403


def test_verified_active_partner_can_offer_collaboration(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "p3")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    project = _mk_project(db_session, home["token"], challenge.id, "P3")
    partner = _mk_partner(db_session, "verified1", verified=True)

    resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations",
        json={"offer_type": "EQUIPMENT", "scope": "Lend a portable TDS/turbidity test kit for field trials."},
        headers=AUTH(partner["token"])
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["agreement_status"] == "OFFERED"
    assert body["version"] == 1


# =========================================================================
# 2. Object-level authorization for collaborations
# =========================================================================

def test_partner_cannot_review_another_partners_collaboration(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "p4")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    project = _mk_project(db_session, home["token"], challenge.id, "P4")
    owner = _mk_partner(db_session, "owner1", verified=True)
    outsider = _mk_partner(db_session, "outsider1", verified=True)

    offer_resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations",
        json={"offer_type": "TESTING", "scope": "Lab testing support."},
        headers=AUTH(owner["token"])
    )
    collab_id = offer_resp.json()["id"]

    # Outsider partner attempts to withdraw/decline someone else's offer
    resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations/{collab_id}/review",
        json={"decision": "DECLINED", "notes": "Trying to interfere with another partner's offer."},
        headers=AUTH(outsider["token"])
    )
    assert resp.status_code == 403


def test_partner_cannot_offer_under_another_projects_university_review(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "p5")
    other_univ = _mk_verified_university(db_session, "p5b")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    project = _mk_project(db_session, home["token"], challenge.id, "P5")
    partner = _mk_partner(db_session, "verified2", verified=True)

    offer_resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations",
        json={"offer_type": "MENTORSHIP", "scope": "Mentorship offer."},
        headers=AUTH(partner["token"])
    )
    collab_id = offer_resp.json()["id"]

    # Another (uninvolved) university attempts to review a collaboration on a project it doesn't own
    resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations/{collab_id}/review",
        json={"decision": "UNDER_REVIEW", "notes": "Not my project."},
        headers=AUTH(other_univ["token"])
    )
    assert resp.status_code == 403


# =========================================================================
# 3. Funding status never advances without approval/evidence; no fabricated payment
# =========================================================================

def test_funding_release_requires_approval_milestone_and_evidence(db_session, gov_admin):
    gov_user, gov_token = gov_admin
    home = _mk_verified_university(db_session, "p6")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    project = _mk_project(db_session, home["token"], challenge.id, "P6")
    partner = _mk_partner(db_session, "funder1", verified=True)

    offer_resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations",
        json={"offer_type": "FUNDING", "scope": "CSR grant for prototype fabrication.", "cash_value": 100000},
        headers=AUTH(partner["token"])
    )
    collab_id = offer_resp.json()["id"]

    # Walk the agreement to ACTIVE via government review
    for decision in ["UNDER_REVIEW", "CONFLICT_CHECK", "ACCEPTED", "CONTRACT_RECORDED", "ACTIVE"]:
        r = client.post(
            f"/api/v1/projects/{project['id']}/collaborations/{collab_id}/review",
            json={"decision": decision, "notes": f"Moving to {decision}", "conflict_declared": False},
            headers=AUTH(gov_token)
        )
        assert r.status_code == 200, r.text

    milestone = db_session.query(Project).filter(Project.id == project["id"]).first().milestones[0]

    funding_resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations/{collab_id}/funding",
        json={"collaboration_id": collab_id, "milestone_id": milestone.id, "budget_line_item": "Prototype materials",
              "amount": 25000, "sanction_authority": "State Nodal Officer"},
        headers=AUTH(gov_token)
    )
    assert funding_resp.status_code == 201, funding_resp.text
    funding_id = funding_resp.json()["id"]

    # Cannot release before approval
    resp = client.post(f"/api/v1/projects/{project['id']}/funding/{funding_id}/action", json={"action": "RELEASE"}, headers=AUTH(gov_token))
    assert resp.status_code == 400

    # Approve -> HELD
    resp = client.post(f"/api/v1/projects/{project['id']}/funding/{funding_id}/action", json={"action": "APPROVE"}, headers=AUTH(gov_token))
    assert resp.status_code == 200
    assert resp.json()["hold_state"] == "HELD"

    # Cannot release: milestone not yet approved
    resp = client.post(
        f"/api/v1/projects/{project['id']}/funding/{funding_id}/action",
        json={"action": "RELEASE", "receipt_evidence_object_id": "not-uploaded-yet"},
        headers=AUTH(gov_token)
    )
    assert resp.status_code == 400
    assert "milestone" in resp.json()["detail"].lower()

    # Approve the milestone with evidence
    files = {"file": ("evidence.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
    client.post(f"/api/v1/projects/{project['id']}/milestones/{milestone.id}/evidence", files=files, headers=AUTH(home["token"]))
    client.post(f"/api/v1/projects/{project['id']}/milestones/{milestone.id}/submit", json={}, headers=AUTH(home["token"]))
    proj = db_session.query(Project).filter(Project.id == project["id"]).first()
    proj.faculty_mentor_id = home["faculty"].id
    db_session.commit()
    review_resp = client.post(
        f"/api/v1/projects/{project['id']}/milestones/{milestone.id}/review",
        json={"decision": "APPROVE", "notes": "Deliverable approved."},
        headers=AUTH(home["faculty_token"])
    )
    assert review_resp.status_code == 200

    # Still cannot release without receipt evidence on the funding record itself
    resp = client.post(f"/api/v1/projects/{project['id']}/funding/{funding_id}/action", json={"action": "RELEASE"}, headers=AUTH(gov_token))
    assert resp.status_code == 400
    assert "evidence" in resp.json()["detail"].lower()

    # Provide receipt evidence, then release succeeds — but payment is NEVER confirmed
    # without a configured finance integration.
    resp = client.post(
        f"/api/v1/projects/{project['id']}/funding/{funding_id}/action",
        json={"action": "RELEASE", "receipt_evidence_object_id": "manually-recorded-receipt-ref"},
        headers=AUTH(gov_token)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["hold_state"] == "RELEASED"
    assert body["payment_confirmed"] is False
    assert body["settlement_status"] == "NOT_CONFIGURED"


def test_project_comment_thread_visible_to_team_mentor_industry_and_officer(db_session, gov_admin):
    """
    A project-level comment thread (entity_type=PROJECT) must be readable by
    everyone verify_project_membership already grants access to for this
    project — the university team, the assigned faculty mentor, an industry
    partner with an active collaboration, and government reviewers — and
    rejected for an outsider with no relationship to the project.
    """
    gov_user, gov_token = gov_admin
    home = _mk_verified_university(db_session, "p8")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    project = _mk_project(db_session, home["token"], challenge.id, "P8")

    proj = db_session.query(Project).filter(Project.id == project["id"]).first()
    proj.faculty_mentor_id = home["faculty"].id
    db_session.commit()

    partner = _mk_partner(db_session, "commenter1", verified=True)
    offer_resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations",
        json={"offer_type": "MENTORSHIP", "scope": "Technical mentorship."},
        headers=AUTH(partner["token"])
    )
    collab_id = offer_resp.json()["id"]
    for decision in ["UNDER_REVIEW", "CONFLICT_CHECK", "ACCEPTED", "CONTRACT_RECORDED", "ACTIVE"]:
        r = client.post(
            f"/api/v1/projects/{project['id']}/collaborations/{collab_id}/review",
            json={"decision": decision, "notes": f"Moving to {decision}", "conflict_declared": False},
            headers=AUTH(gov_token)
        )
        assert r.status_code == 200, r.text

    post_resp = client.post(
        f"/api/v1/projects/{project['id']}/comments",
        json={"entity_type": "PROJECT", "entity_id": project["id"], "content": "Kickoff call scheduled for Friday."},
        headers=AUTH(home["token"])
    )
    assert post_resp.status_code == 201, post_resp.text
    comment_id = post_resp.json()["id"]

    for label, token in [
        ("university team", home["token"]),
        ("faculty mentor", home["faculty_token"]),
        ("industry partner", partner["token"]),
        ("government reviewer", gov_token),
    ]:
        resp = client.get(f"/api/v1/projects/{project['id']}/comments", headers=AUTH(token))
        assert resp.status_code == 200, f"{label} could not read the thread: {resp.text}"
        assert comment_id in [c["id"] for c in resp.json()], f"{label} did not see the posted comment"

    outsider = _mk_partner(db_session, "outsider2", verified=True)
    resp = client.get(f"/api/v1/projects/{project['id']}/comments", headers=AUTH(outsider["token"]))
    assert resp.status_code == 403


def test_industry_dashboard_reflects_funding_summary(db_session, gov_admin):
    """
    The industry partner's own dashboard (GET /industry/dashboard) must show a
    live PENDING/HELD/RELEASED funding summary per collaboration — the same
    per-collaboration funding records the project dashboard's Funding Ledger
    uses — not a static count.
    """
    gov_user, gov_token = gov_admin
    home = _mk_verified_university(db_session, "p6b")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    project = _mk_project(db_session, home["token"], challenge.id, "P6b")
    partner = _mk_partner(db_session, "funder2", verified=True)

    offer_resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations",
        json={"offer_type": "FUNDING", "scope": "CSR grant for field pilot.", "cash_value": 40000},
        headers=AUTH(partner["token"])
    )
    collab_id = offer_resp.json()["id"]

    for decision in ["UNDER_REVIEW", "CONFLICT_CHECK", "ACCEPTED", "CONTRACT_RECORDED", "ACTIVE"]:
        r = client.post(
            f"/api/v1/projects/{project['id']}/collaborations/{collab_id}/review",
            json={"decision": decision, "notes": f"Moving to {decision}", "conflict_declared": False},
            headers=AUTH(gov_token)
        )
        assert r.status_code == 200, r.text

    funding_resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations/{collab_id}/funding",
        json={"collaboration_id": collab_id, "budget_line_item": "Field pilot logistics",
              "amount": 15000, "sanction_authority": "State Nodal Officer"},
        headers=AUTH(gov_token)
    )
    assert funding_resp.status_code == 201, funding_resp.text
    funding_id = funding_resp.json()["id"]

    dash = client.get("/api/v1/industry/dashboard", headers=AUTH(partner["token"]))
    assert dash.status_code == 200, dash.text
    collab_entry = next(c for c in dash.json()["collaborations"] if c["id"] == collab_id)
    assert collab_entry["funding_summary"]["pending_amount"] == 15000
    assert collab_entry["funding_summary"]["held_amount"] == 0
    assert collab_entry["funding_summary"]["count"] == 1

    approve_resp = client.post(f"/api/v1/projects/{project['id']}/funding/{funding_id}/action", json={"action": "APPROVE"}, headers=AUTH(gov_token))
    assert approve_resp.status_code == 200

    dash2 = client.get("/api/v1/industry/dashboard", headers=AUTH(partner["token"]))
    collab_entry2 = next(c for c in dash2.json()["collaborations"] if c["id"] == collab_id)
    assert collab_entry2["funding_summary"]["pending_amount"] == 0
    assert collab_entry2["funding_summary"]["held_amount"] == 15000


# =========================================================================
# 4. Agreement and IP changes are versioned and audited
# =========================================================================

def test_agreement_version_increments_on_each_transition(db_session, gov_admin):
    gov_user, gov_token = gov_admin
    home = _mk_verified_university(db_session, "p7")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    project = _mk_project(db_session, home["token"], challenge.id, "P7")
    partner = _mk_partner(db_session, "versioned1", verified=True)

    offer_resp = client.post(
        f"/api/v1/projects/{project['id']}/collaborations",
        json={"offer_type": "PROTOTYPING", "scope": "3D printing support for enclosure."},
        headers=AUTH(partner["token"])
    )
    collab_id = offer_resp.json()["id"]
    assert offer_resp.json()["version"] == 1

    r1 = client.post(
        f"/api/v1/projects/{project['id']}/collaborations/{collab_id}/review",
        json={"decision": "UNDER_REVIEW", "notes": "Reviewing offer."},
        headers=AUTH(gov_token)
    )
    assert r1.json()["version"] == 2

    r2 = client.post(
        f"/api/v1/projects/{project['id']}/collaborations/{collab_id}/review",
        json={"decision": "CONFLICT_CHECK", "notes": "No conflicts found.", "conflict_declared": False},
        headers=AUTH(gov_token)
    )
    assert r2.json()["version"] == 3


def test_ip_record_requires_all_party_consent_before_approval(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "p8")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    project = _mk_project(db_session, home["token"], challenge.id, "P8")

    other_party = db_session.query(User).filter(User.email == "s7_ip_party@edu.in").first()
    if not other_party:
        other_party = _mk_user(db_session, "s7_ip_party@edu.in", UserRole.FACULTY_MENTOR, "Consenting Faculty")

    create_resp = client.post(
        f"/api/v1/projects/{project['id']}/ip-records",
        json={"record_type": "SOFTWARE", "title": "Effluent Sensor Firmware", "ownership": "JOINT",
              "consent_party_user_ids": [other_party.id]},
        headers=AUTH(home["token"])
    )
    assert create_resp.status_code == 201, create_resp.text
    ip = create_resp.json()
    assert ip["status"] == "PENDING_CONSENT"

    other_token = _token(other_party)
    consent_resp = client.post(
        f"/api/v1/projects/{project['id']}/ip-records/{ip['id']}/consent",
        json={"status": "ACCEPTED", "notes": "I consent to joint ownership."},
        headers=AUTH(other_token)
    )
    assert consent_resp.status_code == 200

    listing = client.get(f"/api/v1/projects/{project['id']}/ip-records", headers=AUTH(home["token"])).json()
    record = next(r for r in listing if r["id"] == ip["id"])
    assert record["status"] == "APPROVED"


# =========================================================================
# 5. Private documents are not visible in public project discovery
# =========================================================================

def test_discovery_view_redacts_sensitive_information(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "p9")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    project = _mk_project(db_session, home["token"], challenge.id, "Confidential Research Codename Zeta")

    resp = client.get("/api/v1/industry/discovery")
    assert resp.status_code == 200
    entries = resp.json()
    match = next((e for e in entries if e["id"] == project["id"]), None)
    assert match is not None
    # Only redacted/banded fields are present — no objectives, documents, proposals, or student names.
    assert set(match.keys()) == {
        "id", "challenge_title", "university_name", "domain", "current_stage",
        "district_name", "progress_band", "seeking_support_types"
    }
    assert "%" in match["progress_band"]
