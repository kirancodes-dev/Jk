import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.services.seed_data import seed_database

from backend.app.core.config import settings

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    settings.DEMO_MODE = True
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

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_demo_accounts(client):
    res = client.get("/api/v1/demo/accounts")
    assert res.status_code == 200
    accounts = res.json()["accounts"]
    assert len(accounts) >= 6

def test_citizen_login(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "citizen@jharkhand.gov.in",
        "password": "password123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "CITIZEN"

def test_admin_dashboard(client):
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@jharkhand.gov.in",
        "password": "password123"
    })
    token = admin_login.json()["access_token"]
    res = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["total_challenges"] >= 10
    assert data["total_universities"] >= 3

def test_jharkhand_map(client):
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@jharkhand.gov.in",
        "password": "password123"
    })
    token = admin_login.json()["access_token"]
    res = client.get("/api/v1/admin/jharkhand-map", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    districts = res.json()
    assert len(districts) == 24

def test_ai_text_analysis(client):
    res = client.post("/api/v1/ai/analyze-text", json={
        "title": "Severe groundwater fluoride poisoning",
        "description": "Villagers in Angara have brown teeth and joint pain from borehole drinking water.",
        "district_name": "Ranchi"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["domain"] == "Water Resources"
    assert data["priority"] in ["HIGH", "CRITICAL"]
    assert len(data["recommended_universities"]) >= 1

def test_citizen_report_challenge_flow(client):
    # 1. Login citizen
    login_res = client.post("/api/v1/auth/login", json={
        "email": "citizen@jharkhand.gov.in",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Report challenge
    res = client.post("/api/v1/challenges", json={
        "title": "Severe drinking water shortage in rural school",
        "description": "Our high school in Dumka has 400 students but the solar borehole pump failed, causing children to drink pond water.",
        "category": "Water Resources",
        "urgency": "High",
        "expected_impact": "Provide clean drinking water to 400 school students.",
        "affected_population": 400,
        "location": {
            "district_name": "Dumka",
            "block_name": "Dumka Sadar",
            "village_or_city": "Ghasipur",
            "location_address": "Near Government High School",
            "latitude": 24.26,
            "longitude": 87.24
        }
    }, headers=headers)
    assert res.status_code == 201
    ch_data = res.json()
    assert ch_data["id"] is not None
    assert ch_data["ai_analysis"] is not None
    assert ch_data["ai_analysis"]["classified_domain"] == "Water Resources"
    assert len(ch_data["university_matches"]) >= 1
