"""
Challenge list endpoints must load a page in a constant number of SQL queries.
Lazily loading each row's location and university cost two extra queries per
row (102 queries for a 100-item review-queue page); see docs/LOAD_TEST.md.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from backend.app.core.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.models.models import Challenge, ChallengeLocation, University, User, UserRole

PAGE = 15
MAX_QUERIES = 4


@pytest.fixture(scope="module")
def seeded_challenges():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    tag = uuid.uuid4().hex[:8]
    try:
        owner = User(email=f"qb-{tag}@university.example.org", hashed_password="!", full_name="Query Budget",
                     role=UserRole.UNIVERSITY)
        db.add(owner)
        db.flush()
        university = University(user_id=owner.id, institution_name=f"Query Budget University {tag}",
                                district_name="Ranchi")
        db.add(university)
        db.flush()
        for i in range(PAGE):
            ch = Challenge(
                title=f"Query budget probe {tag} {i}",
                description="Seeded to check that list endpoints avoid per-row queries.",
                category="Water Resources",
                assigned_university_id=university.id if i % 2 else None,
            )
            ch.location = ChallengeLocation(district_name="Ranchi", block_name="Kanke")
            db.add(ch)
        db.commit()
        yield tag
    finally:
        db.close()


def _count_queries(client, url):
    statements = []

    def record(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        res = client.get(url)
    finally:
        event.remove(engine, "before_cursor_execute", record)
    return res, len(statements)


def test_challenge_list_page_uses_constant_queries(seeded_challenges):
    with TestClient(app) as client:
        res, queries = _count_queries(client, f"/api/v1/challenges?search={seeded_challenges}&page=1&page_size={PAGE}")
    assert res.status_code == 200
    assert len(res.json()) == PAGE
    assert any(item["assigned_university_name"] for item in res.json())
    assert all(item["district_name"] == "Ranchi" for item in res.json())
    assert queries <= MAX_QUERIES, f"{queries} queries for a {PAGE}-item page"


def test_nearby_challenges_use_constant_queries(seeded_challenges):
    with TestClient(app) as client:
        res, queries = _count_queries(client, "/api/v1/challenges/nearby?district=Ranchi")
    assert res.status_code == 200 and res.json()
    assert queries <= MAX_QUERIES
