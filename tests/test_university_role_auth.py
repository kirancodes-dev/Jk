import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.services.seed_data import seed_database, ensure_sapthagiri_seeded
from backend.app.models.models import University

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        ensure_sapthagiri_seeded(db)
    finally:
        db.close()
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_list_universities_has_city_state_verified(client):
    res = client.get("/api/v1/universities")
    assert res.status_code == 200
    univs = res.json()
    assert len(univs) >= 4
    
    # Check Sapthagiri NPS University exists and has city, state, is_verified
    sap = next((u for u in univs if "Sapthagiri" in u["institution_name"]), None)
    assert sap is not None
    assert sap["city"] == "Bengaluru"
    assert sap["state"] == "Karnataka"
    assert sap["is_verified"] is True

def test_sapthagiri_student_login(client):
    db = SessionLocal()
    sap = db.query(University).filter(University.institution_name.ilike("%Sapthagiri%")).first()
    db.close()
    assert sap is not None

    res = client.post("/api/v1/auth/login", json={
        "email": "student@sapthagiri.edu.in",
        "password": "password123",
        "role": "STUDENT",
        "university_id": sap.id
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "STUDENT"
    assert data["university_id"] == sap.id
    assert "Sapthagiri" in data["university_name"]

def test_sapthagiri_faculty_login(client):
    db = SessionLocal()
    sap = db.query(University).filter(University.institution_name.ilike("%Sapthagiri%")).first()
    db.close()

    res = client.post("/api/v1/auth/login", json={
        "email": "faculty@sapthagiri.edu.in",
        "password": "password123",
        "role": "FACULTY_MENTOR",
        "university_id": sap.id
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "FACULTY_MENTOR"
    assert data["university_id"] == sap.id

def test_sapthagiri_admin_login(client):
    db = SessionLocal()
    sap = db.query(University).filter(University.institution_name.ilike("%Sapthagiri%")).first()
    db.close()

    res = client.post("/api/v1/auth/login", json={
        "email": "university@sapthagiri.edu.in",
        "password": "password123",
        "role": "UNIVERSITY",
        "university_id": sap.id
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "UNIVERSITY"
    assert data["university_id"] == sap.id

def test_role_tampering_rejected(client):
    db = SessionLocal()
    sap = db.query(University).filter(University.institution_name.ilike("%Sapthagiri%")).first()
    db.close()

    # Student trying to claim UNIVERSITY admin role
    res = client.post("/api/v1/auth/login", json={
        "email": "student@sapthagiri.edu.in",
        "password": "password123",
        "role": "UNIVERSITY",
        "university_id": sap.id
    })
    assert res.status_code == 403
    assert "Unauthorized role" in res.json()["detail"]

def test_cross_university_tampering_rejected(client):
    db = SessionLocal()
    sap = db.query(University).filter(University.institution_name.ilike("%Sapthagiri%")).first()
    db.close()

    # BIT Mesra student trying to authenticate under Sapthagiri
    res = client.post("/api/v1/auth/login", json={
        "email": "student@bitmesra.ac.in",
        "password": "password123",
        "role": "STUDENT",
        "university_id": sap.id
    })
    assert res.status_code == 403
    assert "University mismatch" in res.json()["detail"]

def test_existing_bitmesra_accounts_remain_valid(client):
    db = SessionLocal()
    bit = db.query(University).filter(University.institution_name.ilike("%Mesra%")).first()
    db.close()
    assert bit is not None

    for email, role in [
        ("university@bitmesra.ac.in", "UNIVERSITY"),
        ("faculty@bitmesra.ac.in", "FACULTY_MENTOR"),
        ("student@bitmesra.ac.in", "STUDENT")
    ]:
        res = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "password123",
            "role": role,
            "university_id": bit.id
        })
        assert res.status_code == 200
        assert res.json()["role"] == role
