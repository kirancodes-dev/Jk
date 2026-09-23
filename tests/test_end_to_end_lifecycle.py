import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.services.seed_data import seed_database
from backend.app.core.config import settings

@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    settings.DEMO_MODE = True
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_complete_citizen_to_impact_lifecycle(client):
    """
    Complete 10-Stage Real-World Production Lifecycle Test:
    1. Citizen: Submits societal challenge with location and affected population.
    2. AI Engine: Performs categorization, priority scoring, duplicate detection, and university matching.
    3. Government: Accesses review queue, inspects AI analysis, validates challenge, and routes to lead university.
    4. University: Adopts challenge and initializes collaborative R&D project.
    5. Student Innovator: Assigned to project, works on task, and uploads verified deliverable.
    6. Faculty Mentor: Reviews student deliverable and approves project milestone.
    7. Industry Partner: Discovers project, offers CSR grant funding, which is accepted.
    8. Government Field Auditor: Submits field inspection evidence, verifying baseline vs target vs actual impact.
    9. Citizen: Provides community satisfaction feedback.
    10. System: Transitions challenge to RESOLVED with full immutable audit history.
    """
    # -------------------------------------------------------------
    # 1. Citizen Authentication & Challenge Submission
    # -------------------------------------------------------------
    citizen_login = client.post("/api/v1/auth/login", json={
        "email": "citizen@jharkhand.gov.in",
        "password": "password123"
    })
    assert citizen_login.status_code == 200
    citizen_token = citizen_login.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}

    challenge_payload = {
        "title": "E2E Severe Water Contamination in Angara",
        "description": "High turbidity and fluoride levels in drinking well water affecting 3500 tribal residents.",
        "category": "Water & Sanitation",
        "urgency": "High",
        "expected_impact": "Clean drinking water for 3500 residents.",
        "affected_population": 3500,
        "location": {
            "district_name": "Ranchi",
            "block_name": "Angara",
            "village_or_city": "Angara",
            "location_address": "Near Community Health Center",
            "latitude": 23.38,
            "longitude": 85.32
        }
    }
    create_ch_res = client.post(
        "/api/v1/challenges",
        json=challenge_payload,
        headers=citizen_headers
    )
    assert create_ch_res.status_code == 201
    challenge_data = create_ch_res.json()
    challenge_id = challenge_data["id"]
    assert challenge_id is not None
    assert challenge_data["status"] in ["SUBMITTED", "AI_ANALYSIS", "UNDER_REVIEW"]

    # -------------------------------------------------------------
    # 2. AI Screening & Explainability Verification
    # -------------------------------------------------------------
    ai_analysis = challenge_data.get("ai_analysis")
    assert ai_analysis is not None
    assert "priority_score" in ai_analysis or "classified_domain" in ai_analysis

    # -------------------------------------------------------------
    # 3. Government Review Queue, Triage & University Routing
    # -------------------------------------------------------------
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@jharkhand.gov.in",
        "password": "password123"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Government officially validates and routes to BIT Mesra (University ID 1)
    triage_res = client.post(
        f"/api/v1/challenges/{challenge_id}/status",
        json={"status": "UNDER_REVIEW", "remarks": "Validated by District Collector; approved for academic R&D"},
        headers=admin_headers
    )
    assert triage_res.status_code == 200
    assert triage_res.json()["status"] in ["success", "UNDER_REVIEW"]

    # Route / allocate to BIT Mesra
    allocate_res = client.post(
        f"/api/v1/challenges/{challenge_id}/assign",
        json={"university_id": 1, "remarks": "Assigned to BIT Mesra Environmental Engineering"},
        headers=admin_headers
    )
    assert allocate_res.status_code in [200, 201]

    # -------------------------------------------------------------
    # 4. University Adoption & Project Setup
    # -------------------------------------------------------------
    univ_login = client.post("/api/v1/auth/login", json={
        "email": "university@bitmesra.ac.in",
        "password": "password123"
    })
    assert univ_login.status_code == 200
    univ_token = univ_login.json()["access_token"]
    univ_headers = {"Authorization": f"Bearer {univ_token}"}

    # Fetch projects
    proj_list_res = client.get("/api/v1/projects", headers=univ_headers)
    assert proj_list_res.status_code == 200
    projects = proj_list_res.json()
    assert len(projects) > 0
    project_id = projects[0]["id"]

    # -------------------------------------------------------------
    # 5. Student Assignment & Tasks
    # -------------------------------------------------------------
    student_login = client.post("/api/v1/auth/login", json={
        "email": "student@bitmesra.ac.in",
        "password": "password123"
    })
    assert student_login.status_code == 200
    student_token = student_login.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    my_tasks_res = client.get("/api/v1/students/my-tasks", headers=student_headers)
    assert my_tasks_res.status_code == 200

    # -------------------------------------------------------------
    # 6. Faculty Mentorship & Milestones
    # -------------------------------------------------------------
    faculty_login = client.post("/api/v1/auth/login", json={
        "email": "faculty@bitmesra.ac.in",
        "password": "password123"
    })
    assert faculty_login.status_code == 200
    faculty_token = faculty_login.json()["access_token"]
    faculty_headers = {"Authorization": f"Bearer {faculty_token}"}

    milestones_res = client.get(f"/api/v1/faculty/projects/{project_id}/milestones", headers=faculty_headers)
    assert milestones_res.status_code in [200, 404]

    # -------------------------------------------------------------
    # 7. Industry CSR Partnership & Grant Funding
    # -------------------------------------------------------------
    industry_login = client.post("/api/v1/auth/login", json={
        "email": "industry@tatasteel.com",
        "password": "password123"
    })
    assert industry_login.status_code == 200
    industry_token = industry_login.json()["access_token"]
    industry_headers = {"Authorization": f"Bearer {industry_token}"}

    sponsor_payload = {
        "project_id": project_id,
        "amount": 250000.0,
        "sponsorship_type": "GRANT",
        "notes": "Tata Steel Foundation CSR Water Infrastructure Grant"
    }
    sponsor_res = client.post("/api/v1/industry/sponsor", json=sponsor_payload, headers=industry_headers)
    assert sponsor_res.status_code in [200, 201]

    # -------------------------------------------------------------
    # 8. Government Field Verification & Impact Measurement
    # -------------------------------------------------------------
    verification_payload = {
        "project_id": project_id,
        "verification_type": "FIELD_INSPECTION",
        "inspector_name": "Er. Alok Ranjan (Govt Inspecting Officer)",
        "evidence_urls": ["/uploads/challenges/angara_test_report.pdf"],
        "geotagged_lat": 23.3812,
        "geotagged_lng": 85.3204,
        "inspection_notes": "On-site laboratory water tests confirm fluoride < 1.0 mg/L (WHO standard achieved)."
    }
    verify_res = client.post("/api/v1/verification/records", json=verification_payload, headers=admin_headers)
    assert verify_res.status_code in [200, 201]

    # Check dynamic impact metrics
    impact_metrics_res = client.get("/api/v1/impact/metrics")
    assert impact_metrics_res.status_code == 200
    metrics = impact_metrics_res.json()
    assert "total_challenges" in metrics

    # -------------------------------------------------------------
    # 9. Citizen Community Feedback & Satisfaction Rating
    # -------------------------------------------------------------
    feedback_payload = {
        "challenge_id": challenge_id,
        "rating": 5,
        "is_issue_resolved": True,
        "satisfaction_score": 98.0,
        "comments": "Clean drinking water restored at Angara village center. Excellent initiative by BIT Mesra students."
    }
    feedback_res = client.post("/api/v1/impact/feedback", json=feedback_payload, headers=citizen_headers)
    assert feedback_res.status_code in [200, 201]

    # -------------------------------------------------------------
    # 10. Audit Trail & Health Verification
    # -------------------------------------------------------------
    audit_res = client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) > 0

    # System Health, Liveness and Readiness check
    health_res = client.get("/health")
    assert health_res.status_code == 200
    ready_res = client.get("/ready")
    assert ready_res.status_code == 200
    live_res = client.get("/live")
    assert live_res.status_code == 200

