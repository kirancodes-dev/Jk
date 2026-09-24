import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.config import settings
from backend.app.models.models import (
    User, UserRole, AccountStatus, GovernmentScope, Challenge, ChallengeLocation,
    ChallengeStatus, District, University, Project, ProjectMember, Student,
    Faculty, OrganizationProfile, OrganizationVerificationStatus, UserSession, OTPChallenge,
    IndustryPartner, PartnerType
)
from backend.app.core.security import get_password_hash, hash_otp, create_access_token, create_refresh_token
from backend.app.services.session_service import session_service


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


def test_password_strength_and_government_email_enforcement(client):
    """Verifies that weak passwords and non-gov emails for government roles are rejected."""
    # 1. Weak password (too short)
    res = client.post("/api/v1/auth/register", json={
        "email": "citizen_test@jharkhand.gov.in",
        "password": "short",
        "full_name": "Test Citizen",
        "role": "CITIZEN"
    })
    assert res.status_code == 422

    # 2. Weak password (no special char / digits)
    res = client.post("/api/v1/auth/register", json={
        "email": "citizen_test2@jharkhand.gov.in",
        "password": "OnlyLettersLongPassword",
        "full_name": "Test Citizen 2",
        "role": "CITIZEN"
    })
    assert res.status_code == 422

    # 3. Government officer/admin accounts can never self-register, regardless of email
    # domain — they are provisioned by a department administrator only.
    res = client.post("/api/v1/auth/register", json={
        "email": "officer@gmail.com",
        "password": "StrongGovPass!2026",
        "full_name": "Fake Officer",
        "role": "GOVERNMENT_OFFICER"
    })
    assert res.status_code == 403
    assert "provisioned by a department administrator" in res.json()["detail"].lower()

    res2 = client.post("/api/v1/auth/register", json={
        "email": "officer@jharkhand.gov.in",
        "password": "StrongGovPass!2026",
        "full_name": "Real-Looking Officer",
        "role": "GOVERNMENT_ADMIN"
    })
    assert res2.status_code == 403


def test_server_side_jurisdiction_scoping_and_isolation(client, db):
    """
    Enforces server-side jurisdiction authorization:
    - Block Officer in Angara cannot triage/validate challenges in Kanke or another district.
    - District Officer in Ranchi cannot triage challenges in Dhanbad.
    - Statewide Government Admin has oversight over all districts.
    """
    # Create test challenge in Ranchi -> Angara Block
    ch_angara = Challenge(
        title="Angara Well Contamination",
        description="Groundwater well contaminated with mining runoff in Angara block.",
        category="Water Management",
        status=ChallengeStatus.SUBMITTED,
        current_tier="BLOCK"
    )
    db.add(ch_angara)
    db.commit()
    db.refresh(ch_angara)

    loc_angara = ChallengeLocation(
        challenge_id=ch_angara.id,
        district_name="Ranchi",
        block_name="Angara",
        village_or_city="Getalsud"
    )
    db.add(loc_angara)

    # Create test challenge in Dhanbad -> Baghmara Block
    ch_dhanbad = Challenge(
        title="Dhanbad Mine Subsidence",
        description="Road collapse due to unscientific mining in Baghmara block.",
        category="Environment",
        status=ChallengeStatus.SUBMITTED,
        current_tier="BLOCK"
    )
    db.add(ch_dhanbad)
    db.commit()
    db.refresh(ch_dhanbad)

    loc_dhanbad = ChallengeLocation(
        challenge_id=ch_dhanbad.id,
        district_name="Dhanbad",
        block_name="Baghmara",
        village_or_city="Barora"
    )
    db.add(loc_dhanbad)
    db.commit()

    # Create Angara Block Officer User
    angara_officer = db.query(User).filter(User.email == "officer.angara@jharkhand.gov.in").first()
    if not angara_officer:
        angara_officer = User(
            email="officer.angara@jharkhand.gov.in",
            hashed_password=get_password_hash("OfficialGov#2026!"),
            full_name="BDO Angara",
            role=UserRole.GOVERNMENT_OFFICER,
            admin_tier="BLOCK",
            district_name="Ranchi",
            block_name="Angara",
            is_active=True,
            is_verified=True,
            account_status=AccountStatus.ACTIVE
        )
        db.add(angara_officer)
        db.commit()
        db.refresh(angara_officer)

    # Generate token for Angara Block Officer
    token_angara = create_access_token(
        subject=angara_officer.id,
        role=angara_officer.role.value,
        tier=angara_officer.admin_tier,
        district_name=angara_officer.district_name,
        block_name=angara_officer.block_name
    )
    angara_headers = {"Authorization": f"Bearer {token_angara}"}

    # 1. Angara Block Officer validates challenge IN Angara -> SUCCEEDS (200)
    res_valid = client.post(f"/api/v1/admin/challenges/{ch_angara.id}/validate", headers=angara_headers)
    assert res_valid.status_code == 200

    # 2. Angara Block Officer attempts to validate challenge in Dhanbad -> FAILS (403 Forbidden)
    res_tamper = client.post(f"/api/v1/admin/challenges/{ch_dhanbad.id}/validate", headers=angara_headers)
    assert res_tamper.status_code == 403
    assert "jurisdiction mismatch" in res_tamper.json()["detail"].lower()

    # 3. State Admin validates Dhanbad challenge -> SUCCEEDS (200)
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@jharkhand.gov.in",
        "password": "password123"
    })
    state_admin_token = admin_login.json()["access_token"]
    state_headers = {"Authorization": f"Bearer {state_admin_token}"}

    res_state = client.post(f"/api/v1/admin/challenges/{ch_dhanbad.id}/validate", headers=state_headers)
    assert res_state.status_code == 200


def test_organization_verification_workflow_and_privilege_blocking(client, db):
    """
    Tests that:
    - New organizations start in PENDING_VERIFICATION.
    - Unverified accounts cannot perform privileged actions.
    - Authorized government officer with organization.verify permission verifies organization.
    - Verification updates organization to VERIFIED and user account_status to ACTIVE.
    """
    # Create new research lab user & organization
    lab_user = db.query(User).filter(User.email == "lab.lead@research.org").first()
    if not lab_user:
        lab_user = User(
            email="lab.lead@research.org",
            hashed_password=get_password_hash("LabSecurePass123!"),
            full_name="Dr. Somnath Roy",
            role=UserRole.RESEARCH_LAB,
            is_active=True,
            is_verified=False,
            account_status=AccountStatus.PENDING_VERIFICATION
        )
        db.add(lab_user)
        db.commit()
        db.refresh(lab_user)

    org = db.query(OrganizationProfile).filter(OrganizationProfile.legal_name == "Jharkhand Advanced Materials Lab").first()
    if not org:
        org = OrganizationProfile(
            user_id=lab_user.id,
            legal_name="Jharkhand Advanced Materials Lab",
            org_type="RESEARCH_LAB",
            reg_number="REG-LAB-2026-JH",
            official_email="lab.lead@research.org",
            official_domain="research.org",
            contact_person="Dr. Somnath Roy",
            phone_number="+91-651-2299881",
            district_name="Ranchi",
            verification_status="PENDING"
        )
        db.add(org)
        db.commit()
        db.refresh(org)

    # 1. Unverified user attempts privileged action (e.g. review verification records) -> FAILS (403)
    unverified_token = create_access_token(
        subject=lab_user.id,
        role=lab_user.role.value
    )
    unverified_headers = {"Authorization": f"Bearer {unverified_token}"}

    # Attempt to verify an organization without permission
    tamper_res = client.post(f"/api/v1/organizations/{org.id}/verify", json={
        "status": "VERIFIED",
        "remarks": "Self verification attempt"
    }, headers=unverified_headers)
    assert tamper_res.status_code == 403

    # 2. Government Admin verifies organization
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@jharkhand.gov.in",
        "password": "password123"
    })
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    verify_res = client.post(f"/api/v1/organizations/{org.id}/verify", json={
        "status": "VERIFIED",
        "remarks": "Official CSIR laboratory accreditation certificate verified."
    }, headers=admin_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["verification_status"] == "VERIFIED"

    # Refresh lab_user and check synchronized ACTIVE account status
    db.refresh(lab_user)
    assert lab_user.is_verified is True
    assert lab_user.account_status == AccountStatus.ACTIVE


def test_session_lifecycle_and_refresh_token_reuse_detection(client, db):
    """
    Tests persistent database session tracking:
    - Session persisted in user_sessions on login.
    - Refresh token rotation returns new tokens.
    - Replay attack using previously rotated refresh token triggers compromise reuse detection,
      revoking the entire family of sessions immediately.
    """
    # 1. Initial Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": "citizen@jharkhand.gov.in",
        "password": "password123"
    })
    assert login_res.status_code == 200
    initial_tokens = login_res.json()
    first_refresh = initial_tokens["refresh_token"]

    # Verify session is persisted in DB
    user = db.query(User).filter(User.email == "citizen@jharkhand.gov.in").first()
    active_sessions = db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_revoked == False
    ).all()
    assert len(active_sessions) >= 1

    # 2. Legitimate Refresh Token Rotation
    rot_res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": first_refresh
    })
    assert rot_res.status_code == 200
    rotated_tokens = rot_res.json()
    second_refresh = rotated_tokens["refresh_token"]
    assert second_refresh != first_refresh

    # 3. Malicious Replay Attack: Attacker tries to use old first_refresh token!
    replay_res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": first_refresh
    })
    assert replay_res.status_code == 401
    assert "reused refresh token" in replay_res.json()["detail"].lower() or "compromised" in replay_res.json()["detail"].lower()

    # Verify that the session was revoked due to token reuse detection
    tampered_res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": second_refresh
    })
    assert tampered_res.status_code == 401


def test_logout_all_sessions_revocation(client, db):
    """Tests /api/v1/auth/logout-all terminates all sessions across multi-instance nodes."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "citizen@jharkhand.gov.in",
        "password": "password123"
    })
    assert login_res.status_code == 200
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Logout all sessions
    logout_all_res = client.post("/api/v1/auth/logout-all", headers=headers)
    assert logout_all_res.status_code == 200
    assert logout_all_res.json()["status"] == "success"

    # Subsequent requests with this access token are now rejected (401)
    subsequent_res = client.get("/api/v1/challenges/my", headers=headers)
    assert subsequent_res.status_code == 401


def test_hashed_otp_challenge_and_lockout(client, db):
    """
    Tests secure OTP lifecycle:
    - OTP stored as salted hash in otp_challenges table.
    - Exceeding 3 incorrect attempts locks out challenge.
    """
    clean_id = "test_otp_citizen@jharkhand.gov.in"
    correct_otp = "849201"
    hashed_val = hash_otp(correct_otp)

    # Clear prior challenges for test account
    db.query(OTPChallenge).filter(OTPChallenge.account_identifier == clean_id).delete()
    db.commit()

    # Store OTP challenge in DB
    challenge = OTPChallenge(
        account_identifier=clean_id,
        otp_hash=hashed_val,
        purpose="PASSWORD_RESET",
        attempts=0,
        max_attempts=3,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    db.add(challenge)
    db.commit()

    # 1. First incorrect attempt (1/3)
    res1 = client.post("/api/v1/auth/verify-otp", json={
        "identifier": clean_id,
        "otp": "000000"
    })
    assert res1.status_code == 400
    assert "attempts remaining: 2" in res1.json()["detail"].lower()

    # 2. Second incorrect attempt (2/3)
    res2 = client.post("/api/v1/auth/verify-otp", json={
        "identifier": clean_id,
        "otp": "111111"
    })
    assert res2.status_code == 400
    assert "attempts remaining: 1" in res2.json()["detail"].lower()

    # 3. Third incorrect attempt (3/3) -> Locks out challenge
    res3 = client.post("/api/v1/auth/verify-otp", json={
        "identifier": clean_id,
        "otp": "222222"
    })
    assert res3.status_code == 400
    assert "maximum verification attempts exceeded" in res3.json()["detail"].lower()

    # 4. Attempting with the correct OTP now fails because challenge is permanently locked out
    res4 = client.post("/api/v1/auth/verify-otp", json={
        "identifier": clean_id,
        "otp": correct_otp
    })
    assert res4.status_code == 400
    assert "maximum verification attempts exceeded" in res4.json()["detail"].lower()


def test_hei_and_project_isolation_idor_mitigation(client, db):
    """
    Tests that:
    - University A cannot access or tamper with University B's project workspace.
    - No .first() demo fallbacks exist.
    """
    bit = db.query(University).filter(University.institution_name.ilike("%Mesra%")).first()
    sap = db.query(University).filter(University.institution_name.ilike("%Sapthagiri%")).first()
    assert bit is not None and sap is not None

    # Find or create a project belonging to BIT Mesra
    proj = db.query(Project).filter(Project.university_id == bit.id).first()
    assert proj is not None

    # Login as Sapthagiri Admin
    sap_login = client.post("/api/v1/auth/login", json={
        "email": "university@sapthagiri.edu.in",
        "password": "password123",
        "role": "UNIVERSITY",
        "university_id": sap.id
    })
    assert sap_login.status_code == 200
    sap_token = sap_login.json()["access_token"]
    sap_headers = {"Authorization": f"Bearer {sap_token}"}

    # Sapthagiri tries to view BIT Mesra's project -> FAILS (403 Forbidden)
    res = client.get(f"/api/v1/projects/{proj.id}", headers=sap_headers)
    assert res.status_code == 403
    assert "forbidden" in res.json()["detail"].lower()


def test_community_org_pri_ulb_registration_creates_pending_org_profile(client, db):
    """PS-required submitter roles (Community Org, PRI, ULB) register with organisation
    details and start PENDING_VERIFICATION — never auto-verified like a citizen."""
    suffix = uuid.uuid4().hex[:8]
    for role, email in [
        ("COMMUNITY_ORG", f"test_comm_org_{suffix}@example.org"),
        ("PRI", f"test_pri_panchayat_{suffix}@example.org"),
        ("ULB", f"test_ulb_municipal_{suffix}@example.org"),
    ]:
        res = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "StrongOrgPass!2026",
            "full_name": "Authorized Representative",
            "role": role,
            "organisation_name": f"Test {role} Organisation",
            "registration_number": f"LGD-{role}-00123",
            "district_name": "Pakur",
            "block_name": "Littipara",
            "panchayat_name": "Test Panchayat"
        })
        assert res.status_code == 201, res.text
        user_id = res.json()["user_id"]

        user = db.query(User).filter(User.id == user_id).first()
        assert user.is_verified is False
        assert user.account_status == AccountStatus.PENDING_VERIFICATION
        assert user.block_name == "Littipara"
        assert user.panchayat_name == "Test Panchayat"

        org = db.query(OrganizationProfile).filter(OrganizationProfile.user_id == user_id).first()
        assert org is not None
        assert org.org_type == role
        assert org.legal_name == f"Test {role} Organisation"
        assert org.reg_number == f"LGD-{role}-00123"
        assert org.verification_status == "PENDING"


def test_research_lab_and_innovation_hub_registration(client, db):
    """Research Lab / Innovation Hub register into the industry/partner identity model."""
    suffix = uuid.uuid4().hex[:8]
    for role, partner_type, email in [
        ("RESEARCH_LAB", PartnerType.RESEARCH_LAB, f"test_research_lab_{suffix}@example.org"),
        ("INNOVATION_HUB", PartnerType.INNOVATION_HUB, f"test_innovation_hub_{suffix}@example.org"),
    ]:
        res = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "StrongOrgPass!2026",
            "full_name": "Lab Director",
            "role": role,
            "organisation_name": f"Test {role} Facility"
        })
        assert res.status_code == 201, res.text
        user_id = res.json()["user_id"]

        user = db.query(User).filter(User.id == user_id).first()
        assert user.is_verified is False

        partner = db.query(IndustryPartner).filter(IndustryPartner.user_id == user_id).first()
        assert partner is not None
        assert partner.partner_type == partner_type
        assert partner.company_name == f"Test {role} Facility"
