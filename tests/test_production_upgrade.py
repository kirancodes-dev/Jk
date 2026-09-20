import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.services.seed_data import seed_database
from backend.app.models.models import Challenge, AuditLog, CitizenFeedback, VerificationRecord

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_refresh_token_flow(client):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@jharkhand.gov.in",
        "password": "password123"
    })
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # Test token refresh
    refresh_res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"]
    })
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

def test_token_logout_revocation(client):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "citizen@jharkhand.gov.in",
        "password": "password123"
    })
    token = login_res.json()["access_token"]

    # Verify active access works
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200

    # Logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_res.status_code == 200

    # Revoked token should be rejected on protected endpoints
    revoked_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert revoked_res.status_code == 401

def test_unauthenticated_upload_rejected(client):
    # Missing Authorization header
    res = client.post("/api/v1/challenges/upload")
    assert res.status_code == 401

def test_invalid_otp_rejected(client):
    res = client.post("/api/v1/auth/verify-otp", json={
        "email": "citizen@jharkhand.gov.in",
        "otp": "999999"
    })
    assert res.status_code == 400

def test_state_machine_transition_and_audit_logging(client):
    # 1. Login as Admin
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@jharkhand.gov.in",
        "password": "password123"
    })
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Get challenge eligible for transition to UNDER_REVIEW
    ch_res = client.get("/api/v1/challenges")
    assert ch_res.status_code == 200
    challenges = ch_res.json()
    assert len(challenges) > 0
    target_ch = next((c for c in challenges if c["status"] in ["SUBMITTED", "AI_ANALYSIS"]), None)
    if not target_ch:
        # Create a fresh challenge to test state transition
        citizen_login = client.post("/api/v1/auth/login", json={
            "email": "citizen@jharkhand.gov.in",
            "password": "password123"
        })
        c_token = citizen_login.json()["access_token"]
        new_ch = client.post("/api/v1/challenges", json={
            "title": "Road pothole hazard on NH33",
            "description": "Critical road damage near Ormanjhi block affecting daily traffic and transport.",
            "category": "Infrastructure",
            "urgency": "High",
            "expected_impact": "Prevent accidents and vehicle damage.",
            "location": {
                "district_name": "Ranchi",
                "block_name": "Ormanjhi",
                "village_or_city": "Ormanjhi",
                "location_address": "NH33 Mile 14",
                "latitude": 23.48,
                "longitude": 85.45
            }
        }, headers={"Authorization": f"Bearer {c_token}"})
        target_ch = new_ch.json()

    ch_id = target_ch["id"]

    # 3. Transition challenge status as Admin
    status_res = client.post(
        f"/api/v1/challenges/{ch_id}/status",
        json={"status": "UNDER_REVIEW", "remarks": "Official government validation"},
        headers=admin_headers
    )
    assert status_res.status_code == 200

    # 4. Verify audit log / status history was created
    audit_res = client.get(f"/api/v1/challenges/{ch_id}/history")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) >= 1
    assert any("UNDER_REVIEW" in str(log) for log in logs)

def test_citizen_feedback_and_impact_metrics(client):
    # Login citizen
    login_res = client.post("/api/v1/auth/login", json={
        "email": "citizen@jharkhand.gov.in",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ch_res = client.get("/api/v1/challenges")
    ch_id = ch_res.json()[0]["id"]

    # Submit citizen feedback
    fb_res = client.post("/api/v1/impact/feedback", json={
        "challenge_id": ch_id,
        "rating": 5,
        "is_issue_resolved": True,
        "satisfaction_score": 95.0,
        "comments": "Solar water pump is installed and working perfectly for all 400 students."
    }, headers=headers)
    assert fb_res.status_code == 201
    fb_data = fb_res.json()
    assert fb_data["rating"] == 5

    # Check metrics
    metrics_res = client.get("/api/v1/impact/metrics")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert "citizen_satisfaction_avg" in metrics
    assert "total_challenges" in metrics

def test_verification_record_submission_and_review(client):
    # Login as Student
    stud_login = client.post("/api/v1/auth/login", json={
        "email": "rahul.verma@bitmesra.ac.in",
        "password": "password123"
    })
    stud_token = stud_login.json()["access_token"]
    stud_headers = {"Authorization": f"Bearer {stud_token}"}

    # Get a project
    proj_res = client.get("/api/v1/projects")
    assert proj_res.status_code == 200
    projects = proj_res.json()
    assert len(projects) > 0
    proj_id = projects[0]["id"]

    # Submit verification record
    v_res = client.post("/api/v1/verification/records", json={
        "project_id": proj_id,
        "verification_type": "FIELD_INSPECTION",
        "inspector_name": "Field Officer Ananya",
        "evidence_urls": ["https://storage.jharkhand.gov.in/evidence/water_test.pdf"],
        "geotagged_lat": 23.3441,
        "geotagged_lng": 85.3096,
        "inspection_notes": "Groundwater filtration unit inspected and water purity verified."
    }, headers=stud_headers)
    assert v_res.status_code == 201
    record_id = v_res.json()["id"]

    # Admin review and approval
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@jharkhand.gov.in",
        "password": "password123"
    })
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    review_res = client.post(f"/api/v1/verification/records/{record_id}/review", json={
        "status": "APPROVED",
        "review_notes": "Complies with drinking water safety standards ISO 10500:2012."
    }, headers=admin_headers)
    assert review_res.status_code == 200
    assert review_res.json()["verification_status"] in ["VERIFIED", "APPROVED"]

def test_pagination_headers(client):
    res = client.get("/api/v1/challenges?page=1&page_size=5")
    assert res.status_code == 200
    assert "X-Total-Count" in res.headers
    assert "X-Page" in res.headers
    assert res.headers["X-Page"] == "1"
    assert "X-Page-Size" in res.headers
    assert res.headers["X-Page-Size"] == "5"
    assert len(res.json()) <= 5

def test_demo_mode_gating(client):
    from backend.app.core.config import settings
    # Test when DEMO_MODE is False
    settings.DEMO_MODE = False
    res = client.post("/api/v1/demo/reset")
    assert res.status_code == 403
    accounts_res = client.get("/api/v1/demo/accounts")
    assert accounts_res.status_code == 403
    # Restore for other tests
    settings.DEMO_MODE = True

def test_async_ai_background_processing(client):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "citizen@jharkhand.gov.in",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/v1/challenges?async_ai=true", json={
        "title": "Broken Handpump in Tamar Village",
        "description": "Deep borehole handpump handle snapped off, leaving 120 villagers without water.",
        "category": "Water Management",
        "urgency": "High",
        "location": {
            "district_name": "Ranchi",
            "block_name": "Tamar",
            "village_or_city": "Ulidih"
        }
    }, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["id"] is not None

def test_secure_file_access_path_traversal_blocked(client):
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@jharkhand.gov.in",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Path traversal with relative dots in path or filename
    res1 = client.get("/api/v1/files/challenges/..%2F..%2Fetc/passwd", headers=headers)
    assert res1.status_code in [400, 404]

    res2 = client.get("/api/v1/files/challenges/....//secret.txt", headers=headers)
    assert res2.status_code in [400, 404]

def test_unauthenticated_file_access_blocked(client):
    # Calling secure file endpoint without Bearer token must return 401
    res = client.get("/api/v1/files/challenges/sample.pdf")
    assert res.status_code == 401

def test_project_detail_idor_protection(client):
    # Login Rahul (BIT Mesra student)
    login_rahul = client.post("/api/v1/auth/login", json={
        "email": "rahul.verma@bitmesra.ac.in",
        "password": "password123"
    })
    assert login_rahul.status_code == 200
    rahul_token = login_rahul.json()["access_token"]
    rahul_headers = {"Authorization": f"Bearer {rahul_token}"}

    # Login Sapthagiri student (different institution/project)
    login_sapth = client.post("/api/v1/auth/login", json={
        "email": "student@sapthagiri.edu.in",
        "password": "password123"
    })
    assert login_sapth.status_code == 200
    sapth_token = login_sapth.json()["access_token"]
    sapth_headers = {"Authorization": f"Bearer {sapth_token}"}

    # Get a project
    proj_res = client.get("/api/v1/projects")
    projects = proj_res.json()
    assert len(projects) > 0
    project_id = projects[0]["id"]

    # Citizen who is not a member of this project must be blocked (403 IDOR guard)
    citizen_login = client.post("/api/v1/auth/login", json={
        "email": "citizen@jharkhand.gov.in",
        "password": "password123"
    })
    citizen_token = citizen_login.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}

    res_citizen = client.get(f"/api/v1/projects/{project_id}", headers=citizen_headers)
    assert res_citizen.status_code == 403
    assert "Forbidden" in res_citizen.json()["detail"] or "Access forbidden" in res_citizen.json()["detail"]

    # An unauthorized student not enrolled in this project must also be blocked (403 IDOR guard)
    res_sapth = client.get(f"/api/v1/projects/{project_id}", headers=sapth_headers)
    assert res_sapth.status_code == 403

def test_concurrent_challenge_assignment_conflict(client):
    # Admin logs in
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@jharkhand.gov.in",
        "password": "password123"
    })
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # Create fresh challenge
    citizen_login = client.post("/api/v1/auth/login", json={
        "email": "citizen@jharkhand.gov.in",
        "password": "password123"
    })
    c_token = citizen_login.json()["access_token"]
    ch_res = client.post("/api/v1/challenges", json={
        "title": "Solar Power Microgrid in Bundu",
        "description": "Rural electrification challenge for distributed mini-grid installation.",
        "category": "Renewable Energy",
        "urgency": "High",
        "location": {"district_name": "Ranchi", "block_name": "Bundu"}
    }, headers={"Authorization": f"Bearer {c_token}"})
    ch_id = ch_res.json()["id"]

    # Assign to University 1
    assign1 = client.post(
        f"/api/v1/challenges/{ch_id}/assign",
        json={"university_id": 1, "remarks": "Assigned to BIT Mesra"},
        headers=admin_headers
    )
    assert assign1.status_code == 200

    # Re-assigning to a DIFFERENT University (e.g. 2) should trigger 409 Conflict
    assign2 = client.post(
        f"/api/v1/challenges/{ch_id}/assign",
        json={"university_id": 2, "remarks": "Conflicting assignment to NIT Jamshedpur"},
        headers=admin_headers
    )
    assert assign2.status_code == 409
    assert "Conflict" in assign2.json()["detail"]

