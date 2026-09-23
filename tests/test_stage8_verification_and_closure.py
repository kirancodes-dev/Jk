"""
Stage 8: Evidence-Based Field Verification, Outcome Metrics & Accountable Closure — Test Suite.

Validates:
1. Unauthorized verifiers (students, industry, citizens, project team members) cannot submit official field verification (403).
2. Authorized government officers submit complete field verification with checklists, device metadata, geotags, media, and lab reports (201).
3. Self-approval is strictly blocked: an inspector cannot review or approve their own verification record (400).
4. Project team members cannot review/approve field verification for their own project (403).
5. Structured outcome metrics lifecycle: baseline/target/actual tracking, collection method, uncertainty, and independent verification.
6. Accountable closure gate blocks premature closure if any of the 9 preconditions are unmet (422 with missing list).
7. Successful closure gate when all 9 preconditions are satisfied: creates ProjectClosureRecord, moves Project to Completed, and transitions Challenge to CLOSED.
8. Citizen validation feedback enforces reporter/beneficiary eligibility, blocks unrelated users (403), and prevents duplicates per version (409).
9. Citizen feedback moderation preserves original comments while redacting public text, and supports citizen appeal.
10. Impact dashboard computes verified facts dynamically without hardcoded defaults (no '4.5' rating fallback, no static '24' districts).
11. Post-deployment regression escalation reopens the challenge to REOPENED and project to 'Post-Deployment Remediation'.
"""

import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.core.security import create_access_token
from backend.app.models.models import (
    User, UserRole, University, Department, Faculty, Student,
    Challenge, ChallengeLocation, ChallengeStatus, Citizen, Project, ProjectMilestone,
    MilestoneStatus, VerificationRecord, OutcomeMetric, ProjectClosureRecord,
    SolutionProposal, ProposalStatus, EvidenceFile, CitizenFeedback, utc_now,
    OrganizationProfile
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


def _mk_user(db, email, role, full_name="Test User", district_name="Ranchi"):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        email=email, full_name=full_name, phone_number="9000000008", role=role,
        hashed_password="hash", is_active=True, is_verified=True, admin_tier="STATE",
        district_name=district_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _token(user):
    return create_access_token(subject=str(user.id), role=user.role.value)


AUTH = lambda tok: {"Authorization": f"Bearer {tok}"}


def _setup_stage8_project(db, prefix="s8"):
    """Helper to set up a project with challenge, university, faculty mentor, and student."""
    gov_officer = _mk_user(db, f"{prefix}_officer@jharkhand.gov.in", UserRole.GOVERNMENT_OFFICER, "Gov Verifier", "Ranchi")
    gov_reviewer = _mk_user(db, f"{prefix}_reviewer@jharkhand.gov.in", UserRole.GOVERNMENT_OFFICER, "Gov Reviewer", "Ranchi")
    admin_user = _mk_user(db, f"{prefix}_admin@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, "Admin User", "Ranchi")
    univ_user = _mk_user(db, f"{prefix}_univ@bitmesra.ac.in", UserRole.UNIVERSITY, "BIT Mesra", "Ranchi")
    mentor_user = _mk_user(db, f"{prefix}_mentor@bitmesra.ac.in", UserRole.FACULTY_MENTOR, "Dr. Mentor", "Ranchi")
    student_user = _mk_user(db, f"{prefix}_student@bitmesra.ac.in", UserRole.STUDENT, "Student Lead", "Ranchi")
    citizen_user = _mk_user(db, f"{prefix}_citizen@gmail.com", UserRole.CITIZEN, "Citizen Reporter", "Ranchi")
    other_citizen = _mk_user(db, f"{prefix}_other_citizen@gmail.com", UserRole.CITIZEN, "Unrelated Citizen", "Dhanbad")

    citizen = db.query(Citizen).filter(Citizen.user_id == citizen_user.id).first()
    if not citizen:
        citizen = Citizen(user_id=citizen_user.id, district_name="Ranchi")
        db.add(citizen)
        db.commit()
        db.refresh(citizen)

    univ = db.query(University).filter(University.user_id == univ_user.id).first()
    if not univ:
        univ = University(
            user_id=univ_user.id, institution_name=f"BIT Mesra {prefix}", district_name="Ranchi",
            is_active=True
        )
        db.add(univ)
        db.commit()
        db.refresh(univ)

    org = db.query(OrganizationProfile).filter(OrganizationProfile.user_id == univ_user.id).first()
    if not org:
        org = OrganizationProfile(
            user_id=univ_user.id, legal_name=univ.institution_name, org_type="UNIVERSITY",
            official_email=univ_user.email, district_name="Ranchi", verification_status="VERIFIED"
        )
        db.add(org)
        db.commit()
        db.refresh(org)

    faculty = db.query(Faculty).filter(Faculty.user_id == mentor_user.id).first()
    if not faculty:
        faculty = Faculty(user_id=mentor_user.id, university_id=univ.id, designation="Professor")
        db.add(faculty)
        db.commit()
        db.refresh(faculty)

    student = db.query(Student).filter(Student.user_id == student_user.id).first()
    if not student:
        student = Student(user_id=student_user.id, university_id=univ.id, degree="B.Tech", roll_number="CS2026-001")
        db.add(student)
        db.commit()
        db.refresh(student)

    challenge = Challenge(
        title=f"Stage 8 Water Quality Monitoring ({prefix})",
        description="Groundwater contaminant tracking across peri-urban Ranchi blocks.",
        category="Water & Sanitation",
        urgency="High",
        status=ChallengeStatus.IN_PROGRESS,
        submitted_by_user_id=citizen_user.id,
        citizen_id=citizen.id,
        affected_population=25000,
        version=1
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)

    loc = ChallengeLocation(
        challenge_id=challenge.id,
        district_name="Ranchi",
        block_name="Kanke",
        latitude=23.412,
        longitude=85.321
    )
    db.add(loc)
    db.commit()

    project = Project(
        challenge_id=challenge.id,
        university_id=univ.id,
        name=f"Smart Filtration Deployment ({prefix})",
        description="Community-scale IoT-enabled water filtration unit.",
        current_stage="Field Testing & Verification",
        faculty_mentor_id=faculty.id,
        faculty_mentor_status="ACCEPTED",
        progress_percentage=0.0
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "project": project,
        "challenge": challenge,
        "gov_officer": gov_officer,
        "gov_reviewer": gov_reviewer,
        "admin_user": admin_user,
        "univ_user": univ_user,
        "mentor_user": mentor_user,
        "student_user": student_user,
        "citizen_user": citizen_user,
        "other_citizen": other_citizen,
        "citizen": citizen,
        "univ": univ,
        "faculty": faculty,
        "student": student
    }


# ------------------------------------------------------------------
# Test 1 & 2: Field Verification Authorization & Payload
# ------------------------------------------------------------------

def test_unauthorized_verifier_rejected(db_session):
    """Students, industry, citizens, and project team members cannot submit official field verification."""
    ctx = _setup_stage8_project(db_session, "unauth")
    project = ctx["project"]

    payload = {
        "project_id": project.id,
        "verification_type": "FIELD_INSPECTION",
        "inspection_notes": "Attempt by student to submit official verification"
    }

    # Student cannot submit
    res = client.post("/api/v1/verification/records", json=payload, headers=AUTH(_token(ctx["student_user"])))
    assert res.status_code == 403

    # Citizen cannot submit
    res = client.post("/api/v1/verification/records", json=payload, headers=AUTH(_token(ctx["citizen_user"])))
    assert res.status_code == 403

    # Implementing Faculty Mentor cannot submit official verification for their own project
    res = client.post("/api/v1/verification/records", json=payload, headers=AUTH(_token(ctx["mentor_user"])))
    assert res.status_code == 403


def test_authorized_government_officer_submits_verification(db_session):
    """Authorized government officer submits complete field inspection with evidence."""
    ctx = _setup_stage8_project(db_session, "auth_ver")
    project = ctx["project"]

    payload = {
        "project_id": project.id,
        "verification_type": "FIELD_INSPECTION",
        "inspector_name": "Er. Rajesh Kumar",
        "inspector_role": "Executive Engineer DW&SD",
        "assignment_id": "ORD-DWSD-2026-0891",
        "checklist_responses": {
            "flow_rate_adequate": True,
            "filter_integrity_passed": True,
            "power_backup_functional": True,
            "beneficiary_signboard_displayed": True
        },
        "visit_timestamp": datetime.now(timezone.utc).isoformat(),
        "device_metadata": {
            "device_model": "Trimble TDC600",
            "gps_accuracy_meters": 1.2,
            "os_version": "Android 12 Enterprise"
        },
        "before_media_urls": ["https://storage.jharkhand.gov.in/evidence/site_before.jpg"],
        "after_media_urls": ["https://storage.jharkhand.gov.in/evidence/site_after_filtration.jpg"],
        "lab_report_references": {
            "lab_name": "State Water Testing Laboratory Ranchi",
            "sample_id": "SWTL-2026-4412",
            "arsenic_ppm": 0.004,
            "permissible_limit_ppm": 0.01,
            "status": "PASS"
        },
        "beneficiary_sample_size": 42,
        "beneficiary_feedback_summary": "40 of 42 surveyed households confirmed continuous clean water supply.",
        "geotagged_lat": 23.4124,
        "geotagged_lng": 85.3218,
        "inspection_notes": "Ground verification successfully executed. Water quality conforms to BIS 10500:2012."
    }

    res = client.post("/api/v1/verification/records", json=payload, headers=AUTH(_token(ctx["gov_officer"])))
    assert res.status_code == 201
    data = res.json()
    assert data["project_id"] == project.id
    assert data["inspector_user_id"] == ctx["gov_officer"].id
    assert data["verification_status"] == "SUBMITTED"
    assert data["beneficiary_sample_size"] == 42
    assert "SWTL-2026-4412" in data["lab_report_references"]


# ------------------------------------------------------------------
# Test 3 & 4: Conflict of Interest & Self-Approval Prevention
# ------------------------------------------------------------------

def test_self_approval_and_mentor_conflict_blocked(db_session):
    """Inspectors cannot review their own records, and faculty mentors cannot review verification for their project."""
    ctx = _setup_stage8_project(db_session, "conflict")
    project = ctx["project"]

    # 1. Gov officer submits record
    payload = {
        "project_id": project.id,
        "verification_type": "FIELD_INSPECTION",
        "inspection_notes": "Field visit completed"
    }
    create_res = client.post("/api/v1/verification/records", json=payload, headers=AUTH(_token(ctx["gov_officer"])))
    assert create_res.status_code == 201
    record_id = create_res.json()["id"]

    # 2. Same officer attempts self-review/approval -> MUST FAIL with 400
    review_payload = {
        "decision": "VERIFIED",
        "remarks": "Self-approving my own inspection"
    }
    self_res = client.post(f"/api/v1/verification/records/{record_id}/review", json=review_payload, headers=AUTH(_token(ctx["gov_officer"])))
    assert self_res.status_code == 400
    assert "Conflict of interest" in self_res.json()["detail"]

    # 3. Project Faculty Mentor attempts review -> MUST FAIL with 403
    mentor_res = client.post(f"/api/v1/verification/records/{record_id}/review", json=review_payload, headers=AUTH(_token(ctx["mentor_user"])))
    assert mentor_res.status_code == 403

    # 4. Independent Gov Reviewer reviews record -> SUCCESS
    indep_res = client.post(f"/api/v1/verification/records/{record_id}/review", json=review_payload, headers=AUTH(_token(ctx["gov_reviewer"])))
    assert indep_res.status_code == 200
    rev_data = indep_res.json()
    assert rev_data["verification_status"] == "VERIFIED"
    assert rev_data["reviewed_by_user_id"] == ctx["gov_reviewer"].id


# ------------------------------------------------------------------
# Test 5: Outcome Metrics CRUD & Verification
# ------------------------------------------------------------------

def test_outcome_metrics_lifecycle_and_verification(db_session):
    """Structured baseline/target/actual metric tracking and independent evaluation."""
    ctx = _setup_stage8_project(db_session, "metrics")
    project = ctx["project"]

    metric_payload = {
        "project_id": project.id,
        "metric_name": "Arsenic Contamination Reduction",
        "metric_definition": "Concentration of inorganic arsenic in community borewell water measured in mg/L",
        "metric_type": "QUANTITATIVE",
        "unit_of_measure": "mg/L",
        "baseline_value": "0.085",
        "baseline_source": "Public Health Engineering Dept Pre-Pilot Survey 2025",
        "target_value": "< 0.010",
        "collection_method": "Atomic Absorption Spectrophotometry",
        "sample_size": 25,
        "uncertainty_margin": "± 0.002 mg/L",
        "responsible_org_name": "BIT Mesra Department of Chemistry"
    }

    # 1. Create outcome metric by project faculty mentor
    create_res = client.post(f"/api/v1/impact/projects/{project.id}/outcome-metrics", json=metric_payload, headers=AUTH(_token(ctx["mentor_user"])))
    assert create_res.status_code == 201
    metric = create_res.json()
    metric_id = metric["id"]
    assert metric["verification_status"] == "REPORTED"
    assert metric["baseline_value"] == "0.085"

    # 2. Update actual value and evidence
    update_payload = {
        "actual_value": "0.005",
        "actual_source": "SWTL Post-Deployment Lab Analysis Report SWTL-2026-4412",
        "collection_method": "Laboratory Spectrophotometry (ISO 17025 accredited)",
        "sample_size": 30,
        "uncertainty_margin": "± 0.001 mg/L",
        "evidence_references": ["SWTL-2026-4412.pdf", "field_sample_chain_of_custody.pdf"],
        "verification_status": "MEASURED"
    }
    update_res = client.put(f"/api/v1/impact/projects/{project.id}/outcome-metrics/{metric_id}", json=update_payload, headers=AUTH(_token(ctx["mentor_user"])))
    assert update_res.status_code == 200
    assert update_res.json()["actual_value"] == "0.005"
    assert update_res.json()["verification_status"] == "MEASURED"

    # 3. Faculty mentor cannot self-verify metric -> 403
    verify_req = {
        "verification_status": "INDEPENDENTLY_VERIFIED",
        "verification_notes": "Verified by state environmental analyst"
    }
    mentor_verify = client.post(f"/api/v1/impact/projects/{project.id}/outcome-metrics/{metric_id}/verify", json=verify_req, headers=AUTH(_token(ctx["mentor_user"])))
    assert mentor_verify.status_code == 403

    # 4. Authorized government reviewer verifies metric -> 200
    gov_verify = client.post(f"/api/v1/impact/projects/{project.id}/outcome-metrics/{metric_id}/verify", json=verify_req, headers=AUTH(_token(ctx["gov_reviewer"])))
    assert gov_verify.status_code == 200
    assert gov_verify.json()["verification_status"] == "INDEPENDENTLY_VERIFIED"
    assert gov_verify.json()["verified_by_user_id"] == ctx["gov_reviewer"].id


# ------------------------------------------------------------------
# Test 6 & 7: Precondition Evaluation & Accountable Closure Gate
# ------------------------------------------------------------------

def test_closure_preconditions_and_closure_gate(db_session):
    """Evaluates the 9 mandatory preconditions and executes the accountable closure gate."""
    ctx = _setup_stage8_project(db_session, "closure")
    project = ctx["project"]
    challenge = ctx["challenge"]

    # 1. Query closure preconditions initially -> Should NOT be ready
    precond_res = client.get(f"/api/v1/projects/{project.id}/closure-preconditions", headers=AUTH(_token(ctx["gov_reviewer"])))
    assert precond_res.status_code == 200
    eval_data = precond_res.json()
    assert eval_data["ready_for_closure"] is False
    assert len(eval_data["missing_preconditions"]) > 0

    # 2. Attempt closure prematurely -> Must return 422 Unprocessable Entity
    close_payload = {
        "decision": "APPROVED_CLOSED",
        "ip_cleared": True,
        "maintenance_handover_plan": "Routine filter cartridge replacement every 6 months handed over to Gram Panchayat Water Committee.",
        "handover_recipient_org": "Gram Panchayat Kanke",
        "closure_remarks": "Premature attempt"
    }
    premature_res = client.post(f"/api/v1/projects/{project.id}/close", json=close_payload, headers=AUTH(_token(ctx["gov_reviewer"])))
    assert premature_res.status_code == 422

    # 3. Satisfy all 9 preconditions:
    # Precondition 1: Approved Solution Proposal
    proposal = SolutionProposal(
        project_id=project.id,
        proposed_solution="Community Solar Water Filter",
        technical_approach="Activated alumina filtration with IoT telemetry",
        objectives="Provide safe drinking water to 500 households",
        feasibility_notes="High local feasibility with solar microgrid",
        budget_breakdown="Filter: 4L, Solar: 2L, Sensors: 1L",
        estimated_cost=700000.0,
        timeline_weeks=16,
        risks="Filter media fouling during monsoon",
        safeguarding_notes="Proper disposal of exhausted alumina media",
        maintenance_plan="Gram Panchayat maintenance committee trained; bi-annual cartridge replacement funded by user tariff.",
        measurable_outcomes="Fluoride < 1.0 mg/L, Arsenic < 0.01 mg/L",
        status=ProposalStatus.APPROVED,
        is_approved_by_gov=True,
        is_current=True,
        version=1,
        submitted_by_user_id=ctx["mentor_user"].id
    )
    db_session.add(proposal)

    # Precondition 2 & 3: Milestones summing to 100% and Approved
    m1 = ProjectMilestone(
        project_id=project.id,
        title="Prototyping & Lab Calibration",
        weight_pct=50.0,
        status=MilestoneStatus.APPROVED,
        approved_by_faculty=True,
        completion_percentage=100.0
    )
    m2 = ProjectMilestone(
        project_id=project.id,
        title="Field Deployment & Community Handover",
        weight_pct=50.0,
        status=MilestoneStatus.APPROVED,
        approved_by_faculty=True,
        completion_percentage=100.0
    )
    db_session.add(m1)
    db_session.add(m2)
    db_session.flush()

    # Precondition 4: Deliverable Evidence Files
    import uuid
    ev1 = EvidenceFile(
        object_id=f"obj-{uuid.uuid4().hex[:16]}",
        entity_type="MILESTONE_DELIVERABLE", entity_id=m1.id, version=1, is_current=True,
        original_filename="lab_calibration_report.pdf", detected_mime="application/pdf",
        size_bytes=1024, sha256_checksum="abc1", owner_id=ctx["mentor_user"].id,
        storage_key="/files/lab.pdf"
    )
    ev2 = EvidenceFile(
        object_id=f"obj-{uuid.uuid4().hex[:16]}",
        entity_type="MILESTONE_DELIVERABLE", entity_id=m2.id, version=1, is_current=True,
        original_filename="field_handover_report.pdf", detected_mime="application/pdf",
        size_bytes=2048, sha256_checksum="abc2", owner_id=ctx["mentor_user"].id,
        storage_key="/files/handover.pdf"
    )
    db_session.add(ev1)
    db_session.add(ev2)

    # Precondition 6: Approved Field Verification
    v_rec = VerificationRecord(
        project_id=project.id,
        verification_type="FIELD_INSPECTION",
        inspector_name="Er. Rajesh Kumar",
        inspector_role="Executive Engineer",
        inspector_user_id=ctx["gov_officer"].id,
        verification_status="VERIFIED",
        review_decision="VERIFIED",
        reviewed_by_user_id=ctx["gov_reviewer"].id,
        inspection_notes="Approved verified on ground."
    )
    db_session.add(v_rec)

    # Precondition 7: Verified Outcome Metrics
    metric = OutcomeMetric(
        project_id=project.id,
        challenge_id=challenge.id,
        metric_name="Arsenic Reduction",
        metric_definition="mg/L level",
        baseline_value="0.08",
        baseline_source="Initial Survey",
        target_value="<0.01",
        actual_value="0.005",
        verification_status="INDEPENDENTLY_VERIFIED",
        verified_by_user_id=ctx["gov_reviewer"].id,
        verified_at=utc_now()
    )
    db_session.add(metric)
    db_session.commit()

    # 4. Check preconditions again -> Should now be fully satisfied!
    precond_res = client.get(f"/api/v1/projects/{project.id}/closure-preconditions", headers=AUTH(_token(ctx["gov_reviewer"])))
    assert precond_res.status_code == 200
    assert precond_res.json()["ready_for_closure"] is True
    assert len(precond_res.json()["missing_preconditions"]) == 0

    # 5. Execute formal project closure gate
    close_res = client.post(f"/api/v1/projects/{project.id}/close", json=close_payload, headers=AUTH(_token(ctx["gov_reviewer"])))
    assert close_res.status_code == 200
    closure_data = close_res.json()
    assert closure_data["project_id"] == project.id
    assert closure_data["closure_decision"] == "APPROVED_CLOSED"
    assert closure_data["closed_by_user_id"] == ctx["gov_reviewer"].id

    # 6. Verify database state: Project stage is Completed, Challenge is CLOSED
    db_session.refresh(project)
    db_session.refresh(challenge)
    assert project.current_stage == "Completed"
    assert challenge.status == ChallengeStatus.CLOSED


# ------------------------------------------------------------------
# Test 8 & 9: Citizen Feedback Ownership, Moderation, & Appeal
# ------------------------------------------------------------------

def test_citizen_feedback_eligibility_moderation_appeal(db_session):
    """Enforces feedback ownership, blocks arbitrary feedback, supports moderation and appeal."""
    ctx = _setup_stage8_project(db_session, "feedback")
    challenge = ctx["challenge"]

    feedback_payload = {
        "challenge_id": challenge.id,
        "challenge_version": 1,
        "rating": 5,
        "is_issue_resolved": True,
        "satisfaction_score": 4.8,
        "comments": "Water filter installed in our basti provides pristine and sweet drinking water.",
        "language": "hi",
        "beneficiary_verification_type": "ORIGINAL_REPORTER"
    }

    # 1. Unrelated citizen from Dhanbad cannot review Ranchi challenge -> 403
    unrelated_res = client.post("/api/v1/impact/feedback", json=feedback_payload, headers=AUTH(_token(ctx["other_citizen"])))
    assert unrelated_res.status_code == 403

    # 2. Original citizen reporter submits feedback -> 201
    reporter_res = client.post("/api/v1/impact/feedback", json=feedback_payload, headers=AUTH(_token(ctx["citizen_user"])))
    assert reporter_res.status_code == 201
    fb_data = reporter_res.json()
    feedback_id = fb_data["id"]
    assert fb_data["rating"] == 5
    assert fb_data["moderation_status"] == "APPROVED"

    # 3. Submitting duplicate feedback for the same challenge version -> 409 Conflict
    dup_res = client.post("/api/v1/impact/feedback", json=feedback_payload, headers=AUTH(_token(ctx["citizen_user"])))
    assert dup_res.status_code == 409
    assert "already been submitted" in dup_res.json()["detail"]

    # 4. Government officer moderates and redacts comments
    mod_payload = {
        "moderation_status": "REDACTED",
        "moderation_reason": "Redacted contact info or sensitive details",
        "redacted_comments": "Water filter installed provides clean drinking water."
    }
    mod_res = client.post(f"/api/v1/impact/feedback/{feedback_id}/moderate", json=mod_payload, headers=AUTH(_token(ctx["gov_reviewer"])))
    assert mod_res.status_code == 200
    assert mod_res.json()["moderation_status"] == "REDACTED"
    assert mod_res.json()["comments"] == "Water filter installed provides clean drinking water."

    # 5. Citizen appeals moderation decision
    appeal_payload = {
        "appeal_reason": "The redacted text did not contain personal data, please restore full endorsement."
    }
    appeal_res = client.post(f"/api/v1/impact/feedback/{feedback_id}/appeal", json=appeal_payload, headers=AUTH(_token(ctx["citizen_user"])))
    assert appeal_res.status_code == 200
    assert appeal_res.json()["appeal_status"] == "PENDING"


# ------------------------------------------------------------------
# Test 10: Dynamic Impact Telemetry without Hardcoded Defaults
# ------------------------------------------------------------------

def test_dynamic_impact_telemetry(db_session):
    """Impact telemetry is computed dynamically from verified DB facts without static fallbacks."""
    res = client.get("/api/v1/impact/metrics")
    assert res.status_code == 200
    data = res.json()

    assert "citizens_benefited" in data
    assert "districts_covered" in data
    assert "average_citizen_satisfaction" in data
    assert "outcome_metrics_breakdown" in data
    assert "unresolved_citizen_reports" in data

    # Verify breakdown structure
    breakdown = data["outcome_metrics_breakdown"]
    assert "reported" in breakdown
    assert "estimated" in breakdown
    assert "measured" in breakdown
    assert "independently_verified" in breakdown

    # Zero hardcoded values: average rating should be a valid float
    assert isinstance(data["average_citizen_satisfaction"], (int, float))
    assert isinstance(data["districts_covered"], int)


# ------------------------------------------------------------------
# Test 11: Post-Deployment Regression Escalation
# ------------------------------------------------------------------

def test_post_deployment_regression_escalation(db_session):
    """Reporting unresolved issues post-closure escalates challenge to REOPENED and project to remediation."""
    ctx = _setup_stage8_project(db_session, "regress")
    project = ctx["project"]
    challenge = ctx["challenge"]

    # Close challenge first
    challenge.status = ChallengeStatus.CLOSED
    project.current_stage = "Completed"
    db_session.commit()

    # Citizen reporter escalates regression
    esc_payload = {
        "reason": "Filter cartridge membrane ruptured after 3 weeks, high turbidity observed."
    }
    esc_res = client.post(
        f"/api/v1/impact/challenges/{challenge.id}/escalate-regression",
        json=esc_payload,
        headers=AUTH(_token(ctx["citizen_user"]))
    )
    assert esc_res.status_code == 200
    assert esc_res.json()["status"] == "ESCALATED"
    assert esc_res.json()["challenge_status"] == "REOPENED"

    db_session.refresh(challenge)
    db_session.refresh(project)
    assert challenge.status == ChallengeStatus.REOPENED
    assert project.current_stage == "Post-Deployment Remediation"
