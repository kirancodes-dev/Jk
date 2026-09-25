"""
Stage 6: Verified HEI Collaboration & Project Lifecycle — Automated Test Suite.

Validates:
1. Only verified, active HEIs can adopt challenges, create projects, invite members, approve deliverables.
2. Cross-HEI student/faculty IDs and arbitrary mentor IDs are rejected.
3. Milestone weights are validated transactionally (sum to 100%).
4. Progress is derived exclusively from approved weighted milestones + evidence, never a client percentage.
5. A student can submit only their assigned work; a faculty reviewer can approve only an authorized project.
6. No project/challenge becomes RESOLVED from milestone percentage alone.
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
    MilestoneStatus, ProjectMember
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
        email=email, full_name=full_name, phone_number="9000000000", role=role,
        hashed_password="hash", is_active=True, is_verified=is_verified,
        admin_tier="STATE"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _token(user, **kwargs):
    return create_access_token(subject=str(user.id), role=user.role.value, **kwargs)


@pytest.fixture
def gov_admin(db_session):
    user = _mk_user(db_session, "s6_gov@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "Stage6 Gov Admin")
    return user, _token(user)


def _mk_verified_university(db, suffix, verified=True, active=True):
    user = _mk_user(db, f"s6_univ_{suffix}@edu.in", UserRole.UNIVERSITY, f"University {suffix}")
    univ = db.query(University).filter(University.user_id == user.id).first()
    if not univ:
        univ = University(user_id=user.id, institution_name=f"Stage6 Institute {suffix}", district_name="Ranchi", is_active=active)
        db.add(univ)
        db.commit()
        db.refresh(univ)

    org = db.query(OrganizationProfile).filter(OrganizationProfile.user_id == user.id).first()
    if not org:
        org = OrganizationProfile(
            user_id=user.id, legal_name=univ.institution_name, org_type="UNIVERSITY",
            official_email=user.email, district_name="Ranchi",
            verification_status="VERIFIED" if verified else "PENDING"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
    univ.organization_profile_id = org.id
    univ.is_active = active
    # Test-only headroom: this fixture's university is reused (by fixed email) across every
    # run of this suite against the persistent shared DB, and each run adds another project,
    # so the real default cap of 10 eventually makes old runs' accumulated projects break new ones.
    if univ.capacity_max_active_projects < 999:
        univ.capacity_max_active_projects = 999
    db.commit()
    db.refresh(univ)

    dept = db.query(Department).filter(Department.university_id == univ.id).first()
    if not dept:
        dept = Department(university_id=univ.id, name=f"CSE-{suffix}")
        db.add(dept)
        db.commit()
        db.refresh(dept)

    fac_user = _mk_user(db, f"s6_faculty_{suffix}@edu.in", UserRole.FACULTY_MENTOR, f"Faculty {suffix}")
    faculty = db.query(Faculty).filter(Faculty.user_id == fac_user.id).first()
    if not faculty:
        faculty = Faculty(user_id=fac_user.id, university_id=univ.id, department_id=dept.id, designation="Professor", expertise="IoT")
        db.add(faculty)
        db.commit()
        db.refresh(faculty)

    stu_user = _mk_user(db, f"s6_student_{suffix}@edu.in", UserRole.STUDENT, f"Student {suffix}")
    student = db.query(Student).filter(Student.user_id == stu_user.id).first()
    if not student:
        student = Student(user_id=stu_user.id, university_id=univ.id, department_id=dept.id, roll_number=f"R{suffix}")
        db.add(student)
        db.commit()
        db.refresh(student)

    return {
        "user": user, "token": _token(user), "univ": univ, "dept": dept,
        "faculty": faculty, "faculty_token": _token(fac_user),
        "student": student, "student_token": _token(stu_user),
    }


def _mk_challenge(db, actor_user, university=None):
    citizen_user = _mk_user(db, "s6_citizen@example.com", UserRole.CITIZEN, "Stage6 Citizen")
    citizen = db.query(Citizen).filter(Citizen.user_id == citizen_user.id).first()
    if not citizen:
        citizen = Citizen(user_id=citizen_user.id, district_name="Ranchi")
        db.add(citizen)
        db.commit()
        db.refresh(citizen)

    challenge = Challenge(
        title=f"Stage6 Water Scarcity {actor_user.id}",
        description="A recurring drinking water scarcity issue affecting the village during summer months.",
        category="Water", citizen_id=citizen.id, status=ChallengeStatus.VALIDATED,
        affected_population=500
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    db.add(ChallengeLocation(challenge_id=challenge.id, district_name="Ranchi", block_name="Kanke"))
    db.commit()
    db.refresh(challenge)

    if university is not None:
        # Simulates a completed Stage 4 assignment + acceptance handshake so tests can
        # focus on Stage 6 behavior without re-exercising the full allocation workflow.
        challenge.assigned_university_id = university.id
        challenge.status = ChallengeStatus.TEAM_FORMED
        db.commit()
        db.refresh(challenge)

    return challenge


AUTH = lambda tok: {"Authorization": f"Bearer {tok}"}


# =========================================================================
# 1. Only verified, active HEIs can adopt/create/invite/approve
# =========================================================================

def test_unverified_university_cannot_create_project(db_session, gov_admin):
    gov_user, gov_token = gov_admin
    unverified = _mk_verified_university(db_session, "unverified1", verified=False)
    challenge = _mk_challenge(db_session, gov_user)

    resp = client.post(
        "/api/v1/projects",
        json={
            "challenge_id": challenge.id, "name": "Unverified Attempt", "description": "desc",
        },
        headers=AUTH(unverified["token"])
    )
    assert resp.status_code == status_forbidden(resp)


def status_forbidden(resp):
    # Accept 403 (not verified) as the only valid outcome
    assert resp.status_code == 403
    return 403


def test_verified_active_university_can_create_project(db_session, gov_admin):
    gov_user, _ = gov_admin
    verified = _mk_verified_university(db_session, "verified1", verified=True)
    challenge = _mk_challenge(db_session, gov_user, university=verified["univ"])

    resp = client.post(
        "/api/v1/projects",
        json={"challenge_id": challenge.id, "name": "Verified Project", "description": "desc"},
        headers=AUTH(verified["token"])
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["milestones_locked"] is False
    assert sum(m["weight_pct"] for m in body["milestones"]) == 100.0


def test_inactive_university_cannot_adopt_challenge(db_session, gov_admin):
    gov_user, _ = gov_admin
    inactive = _mk_verified_university(db_session, "inactive1", verified=True, active=False)
    challenge = _mk_challenge(db_session, gov_user)

    resp = client.post(f"/api/v1/universities/accept-challenge/{challenge.id}", headers=AUTH(inactive["token"]))
    assert resp.status_code == 403


# =========================================================================
# 2. Cross-HEI student/faculty IDs, arbitrary mentor IDs rejected
# =========================================================================

def test_cross_hei_student_invitation_rejected(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "home1", verified=True)
    other = _mk_verified_university(db_session, "other1", verified=True)
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])

    create_resp = client.post(
        "/api/v1/projects",
        json={"challenge_id": challenge.id, "name": "Cross HEI Test", "description": "desc"},
        headers=AUTH(home["token"])
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/v1/projects/{project_id}/team-invitations",
        json={"student_id": other["student"].id, "role_in_team": "Researcher"},
        headers=AUTH(home["token"])
    )
    assert resp.status_code == 400
    assert "institution" in resp.json()["detail"].lower()


def test_arbitrary_faculty_mentor_id_rejected_at_creation(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "home2", verified=True)
    other = _mk_verified_university(db_session, "other2", verified=True)
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])

    resp = client.post(
        "/api/v1/projects",
        json={
            "challenge_id": challenge.id, "name": "Bad Mentor Test", "description": "desc",
            "faculty_mentor_id": other["faculty"].id
        },
        headers=AUTH(home["token"])
    )
    assert resp.status_code == 400


# =========================================================================
# 3 & 4. Milestone weight validation + evidence-driven progress
# =========================================================================

def test_milestone_weight_overflow_rejected(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "weights1", verified=True)
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    create_resp = client.post(
        "/api/v1/projects",
        json={"challenge_id": challenge.id, "name": "Weight Test", "description": "desc"},
        headers=AUTH(home["token"])
    )
    project_id = create_resp.json()["id"]

    # Default scaffold already sums to 100; any further addition must be rejected.
    resp = client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json={"title": "Overflow Milestone", "weight_pct": 10},
        headers=AUTH(home["token"])
    )
    assert resp.status_code == 400
    assert "100%" in resp.json()["detail"]


def test_progress_never_client_supplied_requires_evidence_and_approval(db_session, gov_admin):
    gov_user, gov_token = gov_admin
    home = _mk_verified_university(db_session, "evidence1", verified=True)
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    create_resp = client.post(
        "/api/v1/projects",
        json={"challenge_id": challenge.id, "name": "Evidence Test", "description": "desc"},
        headers=AUTH(home["token"])
    )
    project_id = create_resp.json()["id"]
    project = db_session.query(Project).filter(Project.id == project_id).first()
    milestone = project.milestones[0]

    # Cannot submit without evidence
    resp = client.post(
        f"/api/v1/projects/{project_id}/milestones/{milestone.id}/submit",
        json={"notes": "trying without evidence"},
        headers=AUTH(home["token"])
    )
    assert resp.status_code == 400

    # Upload typed evidence
    files = {"file": ("survey.pdf", io.BytesIO(b"%PDF-1.4 fake pdf content for testing"), "application/pdf")}
    up_resp = client.post(
        f"/api/v1/projects/{project_id}/milestones/{milestone.id}/evidence",
        files=files, headers=AUTH(home["token"])
    )
    assert up_resp.status_code == 200, up_resp.text

    # Now submission succeeds
    resp = client.post(
        f"/api/v1/projects/{project_id}/milestones/{milestone.id}/submit",
        json={"notes": "submitting with evidence"},
        headers=AUTH(home["token"])
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUBMITTED"

    # Directly link the faculty mentor to bypass invitation flow for this focused test
    project.faculty_mentor_id = home["faculty"].id
    db_session.commit()

    # Faculty review + approval recalculates progress from weighted milestones (25%)
    review_resp = client.post(
        f"/api/v1/projects/{project_id}/milestones/{milestone.id}/review",
        json={"decision": "APPROVE", "notes": "Looks good, approved with evidence on file."},
        headers=AUTH(home["faculty_token"])
    )
    assert review_resp.status_code == 200, review_resp.text
    assert review_resp.json()["status"] == "APPROVED"

    refreshed = client.get(f"/api/v1/projects/{project_id}", headers=AUTH(home["token"]))
    assert refreshed.json()["progress_percentage"] == 25.0


# =========================================================================
# 5. Object-level authorization: student can submit only assigned work;
#    faculty reviewer can approve only an authorized project.
# =========================================================================

def test_faculty_cannot_approve_milestone_of_unrelated_project(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "authz1", verified=True)
    outsider = _mk_verified_university(db_session, "authz2", verified=True)
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])

    create_resp = client.post(
        "/api/v1/projects",
        json={"challenge_id": challenge.id, "name": "Authz Test", "description": "desc"},
        headers=AUTH(home["token"])
    )
    project_id = create_resp.json()["id"]
    project = db_session.query(Project).filter(Project.id == project_id).first()
    milestone = project.milestones[0]

    files = {"file": ("evidence.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
    client.post(f"/api/v1/projects/{project_id}/milestones/{milestone.id}/evidence", files=files, headers=AUTH(home["token"]))
    client.post(f"/api/v1/projects/{project_id}/milestones/{milestone.id}/submit", json={}, headers=AUTH(home["token"]))

    # Outsider faculty (not this project's mentor) attempts to approve
    resp = client.post(
        f"/api/v1/projects/{project_id}/milestones/{milestone.id}/review",
        json={"decision": "APPROVE", "notes": "Trying to approve someone else's project."},
        headers=AUTH(outsider["faculty_token"])
    )
    assert resp.status_code == 403


def test_student_cannot_submit_evidence_for_unassigned_task(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "task1", verified=True)
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    create_resp = client.post(
        "/api/v1/projects",
        json={"challenge_id": challenge.id, "name": "Task Test", "description": "desc"},
        headers=AUTH(home["token"])
    )
    project_id = create_resp.json()["id"]

    # Add the home student as an active member directly (bypassing invitation for test focus)
    db_session.add(ProjectMember(project_id=project_id, student_id=home["student"].id, role_in_team="Dev", is_active=True))
    db_session.commit()

    # Second, unrelated student at another verified HEI
    outsider = _mk_verified_university(db_session, "task2", verified=True)

    task_resp = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Wire the sensor", "assigned_to_student_id": home["student"].id},
        headers=AUTH(home["token"])
    )
    assert task_resp.status_code == 200, task_resp.text
    task_id = task_resp.json()["id"]

    files = {"file": ("work.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
    resp = client.post(f"/api/v1/projects/{project_id}/tasks/{task_id}/evidence", files=files, headers=AUTH(outsider["student_token"]))
    assert resp.status_code == 403


# =========================================================================
# 6. No project/challenge becomes RESOLVED from milestone percentage alone
# =========================================================================

def test_challenge_never_auto_resolved_from_milestones(db_session, gov_admin):
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "resolve1", verified=True)
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])
    create_resp = client.post(
        "/api/v1/projects",
        json={"challenge_id": challenge.id, "name": "Resolve Test", "description": "desc"},
        headers=AUTH(home["token"])
    )
    project_id = create_resp.json()["id"]
    project = db_session.query(Project).filter(Project.id == project_id).first()
    project.faculty_mentor_id = home["faculty"].id
    db_session.commit()

    for milestone in list(project.milestones):
        files = {"file": ("ev.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
        client.post(f"/api/v1/projects/{project_id}/milestones/{milestone.id}/evidence", files=files, headers=AUTH(home["token"]))
        client.post(f"/api/v1/projects/{project_id}/milestones/{milestone.id}/submit", json={}, headers=AUTH(home["token"]))
        review_resp = client.post(
            f"/api/v1/projects/{project_id}/milestones/{milestone.id}/review",
            json={"decision": "APPROVE", "notes": "Approved with evidence."},
            headers=AUTH(home["faculty_token"])
        )
        assert review_resp.status_code == 200

    refreshed_project = client.get(f"/api/v1/projects/{project_id}", headers=AUTH(home["token"])).json()
    assert refreshed_project["progress_percentage"] == 100.0

    db_session.refresh(challenge)
    assert challenge.status != ChallengeStatus.RESOLVED


# =========================================================================
# 7. Faculty routing by named specialization/expertise match (Phase 2, Item 11)
# =========================================================================

def test_recommended_faculty_ranks_by_specialization_match(db_session, gov_admin):
    """
    /universities/{id}/recommended-faculty must rank a university's OWN faculty
    by keyword overlap with the challenge's domain, surfacing the actual matching
    faculty member (not just an institution-level score). A faculty member with
    irrelevant expertise (Textiles) must rank below one with matching expertise
    (Water Resources / IoT), for a water-domain challenge.
    """
    gov_user, gov_token = gov_admin
    home = _mk_verified_university(db_session, "facmatch1")
    univ = home["univ"]

    # The fixture's default faculty has expertise="IoT" — irrelevant to water_expert below.
    irrelevant_user = _mk_user(db_session, "s6_faculty_facmatch1_textiles@edu.in", UserRole.FACULTY_MENTOR, "Faculty Textiles")
    irrelevant_faculty = db_session.query(Faculty).filter(Faculty.user_id == irrelevant_user.id).first()
    if not irrelevant_faculty:
        irrelevant_faculty = Faculty(
            user_id=irrelevant_user.id, university_id=univ.id, department_id=home["dept"].id,
            designation="Assistant Professor", expertise="Textile Engineering", research_interests="Handloom fabric design"
        )
        db_session.add(irrelevant_faculty)
        db_session.commit()

    water_expert_user = _mk_user(db_session, "s6_faculty_facmatch1_water@edu.in", UserRole.FACULTY_MENTOR, "Faculty Water Expert")
    water_expert = db_session.query(Faculty).filter(Faculty.user_id == water_expert_user.id).first()
    if not water_expert:
        water_expert = Faculty(
            user_id=water_expert_user.id, university_id=univ.id, department_id=home["dept"].id,
            designation="Professor", expertise="Water Resources Engineering",
            research_interests="Groundwater contamination and fluoride filtration"
        )
        db_session.add(water_expert)
        db_session.commit()

    challenge = _mk_challenge(db_session, gov_user, university=univ)
    challenge.category = "Water Resources"
    db_session.commit()

    resp = client.get(
        f"/api/v1/universities/{univ.id}/recommended-faculty?challenge_id={challenge.id}",
        headers=AUTH(gov_admin[1])
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["university_id"] == univ.id
    faculty_list = data["recommended_faculty"]
    assert len(faculty_list) >= 2

    ranked_ids = [f["faculty_id"] for f in faculty_list]
    assert ranked_ids.index(water_expert.id) < ranked_ids.index(irrelevant_faculty.id)

    top = faculty_list[0]
    assert top["faculty_id"] == water_expert.id
    assert "specialization" in top["matching_factors"].lower() or "keyword" in top["matching_factors"].lower()
    assert "allocation_notice" in top
    assert top["ranking"] == 1


# =========================================================================
# 8. Structured testing outcomes gate DEPLOYMENT (Phase 2, Item 15)
# =========================================================================

def test_deployment_requires_recorded_test_outcome(db_session, gov_admin):
    """
    A challenge cannot transition to DEPLOYMENT without at least one recorded
    PASS/PARTIAL test-report for its project. Submitting a test report via
    POST /projects/{id}/test-reports unblocks the transition.
    """
    gov_user, gov_token = gov_admin
    home = _mk_verified_university(db_session, "deploygate1")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])

    resp = client.post(
        "/api/v1/projects",
        json={"challenge_id": challenge.id, "name": "Deploy Gate Project", "description": "desc"},
        headers=AUTH(home["token"])
    )
    assert resp.status_code == 201, resp.text
    project_id = resp.json()["id"]

    # Move the challenge to a state where DEPLOYMENT is otherwise a legal
    # transition target, so the test isolates the test-outcome gate itself.
    challenge.status = ChallengeStatus.FIELD_TESTING
    db_session.commit()

    # No test reports exist yet — DEPLOYMENT must be rejected.
    deny = client.post(
        f"/api/v1/challenges/{challenge.id}/status",
        json={"status": "DEPLOYMENT", "remarks": "Attempting early deployment"},
        headers=AUTH(home["token"])
    )
    assert deny.status_code == 400
    assert "test outcome" in deny.json()["detail"].lower()

    # Listing test reports for a fresh project is empty.
    list_resp = client.get(f"/api/v1/projects/{project_id}/test-reports", headers=AUTH(home["token"]))
    assert list_resp.status_code == 200
    assert list_resp.json() == []

    # Record a passing field trial.
    submit = client.post(
        f"/api/v1/projects/{project_id}/test-reports",
        json={
            "test_type": "FIELD",
            "outcome": "PASS",
            "summary": "Field trial at the affected village completed with positive community feedback."
        },
        headers=AUTH(home["token"])
    )
    assert submit.status_code == 201, submit.text
    assert submit.json()["outcome"] == "PASS"
    assert submit.json()["reported_by_name"] == home["user"].full_name

    # DEPLOYMENT is now permitted.
    allow = client.post(
        f"/api/v1/challenges/{challenge.id}/status",
        json={"status": "DEPLOYMENT", "remarks": "Deploying after successful field trial"},
        headers=AUTH(home["token"])
    )
    assert allow.status_code == 200, allow.text
    db_session.refresh(challenge)
    assert challenge.status == ChallengeStatus.DEPLOYMENT

    list_resp2 = client.get(f"/api/v1/projects/{project_id}/test-reports", headers=AUTH(home["token"]))
    assert len(list_resp2.json()) == 1


def test_test_report_evidence_upload_and_list(db_session, gov_admin):
    """A test report can have supporting evidence (photo/lab report) attached, mirroring the milestone-evidence pattern."""
    gov_user, _ = gov_admin
    home = _mk_verified_university(db_session, "testevid1")
    challenge = _mk_challenge(db_session, gov_user, university=home["univ"])

    resp = client.post(
        "/api/v1/projects",
        json={"challenge_id": challenge.id, "name": "Evidence Test Project", "description": "desc"},
        headers=AUTH(home["token"])
    )
    assert resp.status_code == 201, resp.text
    project_id = resp.json()["id"]

    report_resp = client.post(
        f"/api/v1/projects/{project_id}/test-reports",
        json={"test_type": "LAB", "outcome": "PASS", "summary": "Lab water-quality assay confirmed fluoride reduction below WHO threshold."},
        headers=AUTH(home["token"])
    )
    assert report_resp.status_code == 201, report_resp.text
    report_id = report_resp.json()["id"]

    files = {"file": ("lab_report.pdf", io.BytesIO(b"%PDF-1.4 fake lab report"), "application/pdf")}
    up_resp = client.post(
        f"/api/v1/projects/{project_id}/test-reports/{report_id}/evidence",
        files=files,
        headers=AUTH(home["token"])
    )
    assert up_resp.status_code == 200, up_resp.text
    assert up_resp.json()["original_filename"] == "lab_report.pdf"

    list_resp = client.get(
        f"/api/v1/projects/{project_id}/test-reports/{report_id}/evidence",
        headers=AUTH(home["token"])
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["original_filename"] == "lab_report.pdf"
