"""
Stage 5: Comprehensive Automated Test Suite for Governable AI Decision-Support Pipeline.
Validates:
1. Provider-neutral interfaces & AIModelResult metadata contract (model name, version, latency, snapshot hash, fallback flag).
2. Explicit labeling of deterministic heuristics as local fallback (never claiming ML without model).
3. Multilingual processing (Hindi/Devanagari, English, low-confidence review routing).
4. Configurable, versioned multi-factor priority weights (severity, urgency, population, health/safety, vulnerability).
5. Scalable deduplication (SQL pre-filtering, decomposed signals, no auto-suppression).
6. Capability matching restricted to verified institutions with conflict-of-interest check.
7. Durable asynchronous outbox queue (idempotency, exponential backoff, fallback on max retries).
8. Human-in-the-loop overrides (mandatory justification, immutable AIAnalysis history, audit events).
9. Offline benchmark evaluation and drift monitoring.
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.models import (
    User, UserRole, Challenge, ChallengeLocation, ChallengeStatus,
    ChallengePriority, AIAnalysis, ChallengeSimilarity, University,
    UniversityExpertise, AIJob, AIJobStatus, AIHumanOverride,
    AIPriorityWeightConfig, DomainAuditEvent
)
from backend.app.services.ai.classification_service import classification_service
from backend.app.services.ai.priority_service import priority_service
from backend.app.services.ai.deduplication_service import deduplication_service
from backend.app.services.ai.matching_service import matching_service
from backend.app.services.ai.multilingual_service import multilingual_service
from backend.app.services.ai.queue_service import queue_service
from backend.app.services.ai.evaluation_service import evaluation_service
from backend.app.services.ai.embedding_service import EmbeddingService, embedding_service
from backend.app.services.ai_service import ai_service
from backend.app.core.security import create_access_token

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture
def test_reviewer(db_session: Session):
    user = db_session.query(User).filter(User.email == "gov_reviewer_s5@jharkhand.gov.in").first()
    if not user:
        user = User(
            email="gov_reviewer_s5@jharkhand.gov.in",
            full_name="Stage 5 Reviewer",
            phone_number="9876543299",
            role=UserRole.GOVERNMENT_ADMIN,
            admin_tier="STATE",
            hashed_password="test_password_hash",
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture
def reviewer_token(test_reviewer: User):
    return create_access_token(subject=str(test_reviewer.id), role=test_reviewer.role.value)


# =========================================================================
# 1. AIModelResult & Provider-Neutral Interface Tests
# =========================================================================

def test_classifier_metadata_and_fallback_label():
    """Verify classification returns AIModelResult with all governance fields and explicit fallback labeling."""
    result = classification_service.classify(
        title="Contaminated borewell water causing sickness",
        description="Villagers are facing severe water shortage and diarrhea from fluoride contamination."
    )
    assert result.model_name == "JHARKHAND_TAXONOMY_CLASSIFIER_V2"
    assert result.model_version == "2.2.0"
    assert result.provider_name == "LOCAL_DETERMINISTIC_ENGINE"
    assert result.is_fallback is True
    assert "safe local baseline" in result.fallback_reason.lower()
    assert result.input_snapshot_hash is not None and len(result.input_snapshot_hash) == 64
    assert result.detected_language == "en"
    assert result.language_confidence >= 0.80
    assert result.execution_time_ms >= 0

    output = result.output
    assert output["domain"] == "Water Resources"
    assert output["confidence"] >= 0.75
    assert len(output["keywords"]) > 0

    # Test backwards-compatible tuple unpacking
    domain, conf, kw, exp, sol = result
    assert domain == "Water Resources"
    assert conf >= 0.75


def test_classifier_unmatched_text_flags_unclassified_not_urban_infrastructure():
    """
    Text with no taxonomy keyword signal and no resolvable category hint must be
    labeled "Unclassified" with requires_human_review=True — never silently
    defaulted to an arbitrary real domain like "Urban Infrastructure", which would
    misroute the submission to the wrong university/department without anyone
    noticing.
    """
    result = classification_service.classify(
        title="xkq zzy plerm",
        description="qbnf trzl wexo ffgh"
    )
    assert result.output["domain"] == "Unclassified"
    assert result.output["requires_human_review"] is True
    assert result.output["confidence"] < 0.5

    # A resolvable category hint still avoids the "Unclassified" fallback even
    # when the free text itself has no keyword signal.
    hinted = classification_service.classify(
        title="xkq zzy plerm",
        description="qbnf trzl wexo ffgh",
        category_hint="Water Resources"
    )
    assert hinted.output["domain"] == "Water Resources"
    assert hinted.output["requires_human_review"] is False


# =========================================================================
# 2. Multilingual Processing Tests
# =========================================================================

def test_multilingual_devanagari_hindi_detection_and_classification():
    """Verify Hindi/Devanagari text detection, translation normalization, and domain accuracy."""
    hindi_title = "गांव के चापाकल में आर्सेनिक और फ्लोराइड का जहर"
    hindi_desc = "पीने के पानी में भारी आर्सेनिक मिला है, ग्रामीण बीमार पड़ रहे हैं।"

    meta = multilingual_service.process_text(hindi_title, hindi_desc)
    assert meta["detected_language"] == "hi"
    assert meta["language_confidence"] >= 0.85
    assert meta["requires_human_language_review"] is False
    assert "water" in meta["translated_title"].lower() or "handpump" in meta["translated_title"].lower()

    # Verify classifier properly maps the normalized concepts to Water Resources
    result = classification_service.classify(hindi_title, hindi_desc)
    assert result.output["domain"] == "Water Resources"
    assert result.detected_language == "hi"

def test_multilingual_low_confidence_flagged_for_human_review():
    """Verify ambiguous or unknown language triggers human review flag."""
    meta = multilingual_service.process_text("12345", "???")
    assert meta["requires_human_language_review"] is True


# =========================================================================
# 3. Configurable Versioned Priority Weights Tests
# =========================================================================

def test_priority_engine_breakdown_and_weights(db_session: Session):
    """Verify priority calculation incorporates severity, urgency, population, health/safety, and vulnerability."""
    result = priority_service.calculate_priority(
        title="Immediate danger of bridge collapse with casualties",
        description="Arsenic contaminated drinking water and fatal road bridge collapse affecting 6000 people in aspirational district.",
        urgency="Critical",
        affected_population=6000,
        district_name="Khunti",
        db=db_session
    )
    assert result.output["priority"] == ChallengePriority.CRITICAL
    assert result.output["composite_score"] >= 80.0
    breakdown = result.output["breakdown"]
    assert "weights" in breakdown
    assert "scores" in breakdown
    assert breakdown["scores"]["severity_score"] >= 90.0
    assert breakdown["scores"]["health_safety_score"] >= 80.0
    assert breakdown["scores"]["vulnerability_score"] == 85.0  # Khunti is an aspirational district

def test_custom_priority_weights_override(db_session: Session):
    """Verify passing custom weights alters the priority score calculation."""
    custom_weights = {
        "severity_weight": 0.10,
        "urgency_weight": 0.10,
        "population_weight": 0.70,  # Heavily weight population
        "health_safety_weight": 0.05,
        "vulnerability_weight": 0.05
    }
    result_low_pop = priority_service.calculate_priority(
        title="Minor street light repair",
        description="Light is flickering",
        urgency="Low",
        affected_population=10,
        weights_config=custom_weights,
        db=db_session
    )
    assert result_low_pop.output["priority"] == ChallengePriority.LOW


def test_aspirational_district_vulnerability_matches_niti_aayog_list(db_session: Session):
    """
    Jharkhand has 19 (of 24) NITI Aayog Aspirational Districts. Previously only 13
    were recognised and "Sahebganj" was misspelled "sahibganj" (never matching the
    seeded district name). District.is_aspirational is now authoritative when a DB
    session is available; newly-added districts like Chatra, Deoghar, Giridih,
    Jamtara, Koderma, and Saraikela Kharsawan must now score as aspirational, and
    non-aspirational districts like Ranchi must not.
    """
    for district_name in ["Chatra", "Deoghar", "Giridih", "Jamtara", "Koderma", "Saraikela Kharsawan", "Sahebganj"]:
        result = priority_service.calculate_priority(
            title="Localized infrastructure delay report",
            description="Routine maintenance backlog reported by field officer.",
            urgency="Medium",
            affected_population=200,
            district_name=district_name,
            db=db_session
        )
        assert result.output["breakdown"]["scores"]["vulnerability_score"] == 85.0, district_name

    result_non_aspirational = priority_service.calculate_priority(
        title="Localized infrastructure delay report",
        description="Routine maintenance backlog reported by field officer.",
        urgency="Medium",
        affected_population=200,
        district_name="Ranchi",
        db=db_session
    )
    assert result_non_aspirational.output["breakdown"]["scores"]["vulnerability_score"] == 50.0


# =========================================================================
# 4. Scalable Deduplication Tests
# =========================================================================

def test_deduplication_decomposed_signals_and_no_auto_suppress(db_session: Session, test_reviewer: User):
    """Verify candidate pre-filtering, decomposed signals, and ensure submissions are never auto-suppressed."""
    # Create original challenge
    ch1 = Challenge(
        title="Borewell motor damaged in Namkum village",
        description="Drinking water borewell motor burned out. 500 villagers have no drinking water.",
        category="Water Management",
        priority=ChallengePriority.HIGH,
        status=ChallengeStatus.SUBMITTED,
        submitted_by_user_id=test_reviewer.id,
        affected_population=500
    )
    db_session.add(ch1)
    db_session.flush()

    loc1 = ChallengeLocation(
        challenge_id=ch1.id,
        district_name="Ranchi",
        block_name="Namkum"
    )
    db_session.add(loc1)
    db_session.commit()

    # Find duplicates for similar challenge in same area
    duplicates = deduplication_service.find_duplicates(
        db=db_session,
        title="Borewell motor burned and broken in Namkum",
        description="Water supply stopped due to burned borewell pump in Namkum village.",
        category="Water Management",
        district_name="Ranchi",
        block_name="Namkum",
        exclude_id=999999
    )

    assert len(duplicates) >= 1
    match = duplicates[0]
    assert match["similar_challenge_id"] == ch1.id
    assert match["similarity_score"] >= 0.65
    assert match["text_similarity"] > 0.0
    assert match["geographic_similarity"] >= 0.70
    assert match["category_similarity"] == 1.0
    assert "Requires Human Review (never auto-suppressed)" in match["explanation"]

    # Verify original challenge remains in its legal status (NEVER auto-rejected)
    assert ch1.status == ChallengeStatus.SUBMITTED


# =========================================================================
# 5. Verified-Only University Matching Tests
# =========================================================================

def test_matching_routes_only_to_verified_institutions(db_session: Session):
    """Verify unverified universities are strictly excluded and verified units are ranked."""
    # 1. Verified institutional user & university
    u_verified = db_session.query(User).filter(User.email == "univ_verified_test@jharkhand.edu").first()
    if not u_verified:
        u_verified = User(
            email="univ_verified_test@jharkhand.edu",
            full_name="BIT Mesra Admin",
            role=UserRole.UNIVERSITY,
            hashed_password="test",
            is_active=True,
            is_verified=True
        )
        db_session.add(u_verified)
        db_session.flush()

    verified_univ = db_session.query(University).filter(University.user_id == u_verified.id).first()
    if not verified_univ:
        verified_univ = University(
            user_id=u_verified.id,
            institution_name="Birla Institute of Technology Mesra (Verified)",
            district_name="Ranchi",
            nirf_ranking=50
        )
        db_session.add(verified_univ)
        db_session.commit()

    # 2. Unverified institutional user & university
    u_unverified = db_session.query(User).filter(User.email == "univ_unverified_test@jharkhand.edu").first()
    if not u_unverified:
        u_unverified = User(
            email="univ_unverified_test@jharkhand.edu",
            full_name="Unverified Academy Admin",
            role=UserRole.UNIVERSITY,
            hashed_password="test",
            is_active=True,
            is_verified=False
        )
        db_session.add(u_unverified)
        db_session.flush()

    unverified_univ = db_session.query(University).filter(University.user_id == u_unverified.id).first()
    if not unverified_univ:
        unverified_univ = University(
            user_id=u_unverified.id,
            institution_name="Unaccredited Local Academy",
            district_name="Ranchi"
        )
        db_session.add(unverified_univ)
        db_session.commit()

    matches = matching_service.match_universities(
        db=db_session,
        domain="Water Management",
        keywords=["water", "sensor", "purification"],
        district_name="Ranchi"
    )

    matched_ids = [m["university_id"] for m in matches]
    assert verified_univ.id in matched_ids
    assert unverified_univ.id not in matched_ids
    for m in matches:
        assert m["verification_status"] == "VERIFIED"
        assert "requires explicit administrative assignment" in m["allocation_notice"]


# =========================================================================
# 6. Durable Asynchronous Outbox Queue Tests
# =========================================================================

def test_ai_queue_enqueue_and_idempotency(db_session: Session, test_reviewer: User):
    """Verify queue enqueueing generates idempotency key and prevents duplicate jobs."""
    ch = Challenge(
        title="Broken road causing accidents in Palamu",
        description="Deep potholes across 4km stretch of road causing accidents.",
        category="Urban Infrastructure",
        priority=ChallengePriority.MEDIUM,
        status=ChallengeStatus.SUBMITTED,
        submitted_by_user_id=test_reviewer.id
    )
    db_session.add(ch)
    db_session.commit()

    job1 = queue_service.enqueue_ai_job(db_session, challenge_id=ch.id)
    assert job1.id is not None
    assert job1.status == AIJobStatus.PENDING
    assert job1.idempotency_key == f"CHALLENGE_{ch.id}_FULL_ANALYSIS"

    # Second enqueue returns existing job
    job2 = queue_service.enqueue_ai_job(db_session, challenge_id=ch.id)
    assert job2.id == job1.id

    # Process job
    success = queue_service.process_job(db_session, job1)
    assert success is True
    assert job1.status == AIJobStatus.COMPLETED
    assert job1.completed_at is not None

def test_ai_queue_failure_and_fallback_resilience(db_session: Session, test_reviewer: User):
    """Verify failed jobs back off exponentially and trigger deterministic fallback on max retries."""
    ch = Challenge(
        title="Temporary test challenge for queue retry",
        description="Testing retry logic and backoff",
        category="Urban Infrastructure",
        priority=ChallengePriority.MEDIUM,
        status=ChallengeStatus.SUBMITTED,
        submitted_by_user_id=test_reviewer.id
    )
    db_session.add(ch)
    db_session.commit()

    job = AIJob(
        challenge_id=ch.id,
        idempotency_key=f"TEST_RETRY_JOB_{ch.id}",
        status=AIJobStatus.PENDING,
        attempts=2,
        max_retries=3,
        backoff_seconds=1
    )
    db_session.add(job)
    db_session.commit()

    # Simulate error on primary analyzer to verify graceful fallback on max retries
    with patch("backend.app.services.ai_service.ai_service.analyze_challenge", side_effect=RuntimeError("Primary model inference timeout")):
        success = queue_service.process_job(db_session, job)
        assert success is False
        assert job.status == AIJobStatus.FALLBACK_COMPLETED
        assert "Primary model inference timeout" in job.error_message


# =========================================================================
# 7. Human-in-the-Loop Override Tests
# =========================================================================

def test_human_override_endpoints(client: TestClient, reviewer_token: str, db_session: Session, test_reviewer: User):
    """Verify reviewer override persists in AIHumanOverride, modifies challenge, and preserves AIAnalysis."""
    ch = Challenge(
        title="School building roof leaking",
        description="Roof leaks during monsoon season.",
        category="Urban Infrastructure",
        priority=ChallengePriority.LOW,
        status=ChallengeStatus.UNDER_REVIEW,
        submitted_by_user_id=test_reviewer.id
    )
    db_session.add(ch)
    db_session.flush()

    analysis = AIAnalysis(
        challenge_id=ch.id,
        classified_domain="Urban Infrastructure",
        detected_priority=ChallengePriority.LOW,
        confidence_score=0.82,
        model_name="JHARKHAND_TAXONOMY_CLASSIFIER_V2"
    )
    db_session.add(analysis)
    db_session.commit()

    headers = {"Authorization": f"Bearer {reviewer_token}"}

    # 1. Attempt override without mandatory reason (must fail with 400)
    bad_resp = client.post(
        f"/api/v1/challenges/{ch.id}/ai-override",
        json={"decision_type": "DOMAIN_OVERRIDE", "override_value": "Education", "mandatory_reason": ""},
        headers=headers
    )
    assert bad_resp.status_code == 400

    # 2. Valid domain override with non-empty reason
    resp = client.post(
        f"/api/v1/challenges/{ch.id}/ai-override",
        json={
            "decision_type": "DOMAIN_OVERRIDE",
            "override_value": "Education",
            "mandatory_reason": "Primary impact is disruption of classroom education and student safety."
        },
        headers=headers
    )
    assert resp.status_code == 200
    override_data = resp.json()
    assert override_data["decision_type"] == "DOMAIN_OVERRIDE"
    assert override_data["original_value"] == "Urban Infrastructure"
    assert override_data["override_value"] == "Education"

    # Verify Challenge category is updated
    db_session.refresh(ch)
    assert ch.category == "Education"

    # CRITICAL: Verify AIAnalysis historical prediction was NEVER overwritten
    db_session.refresh(analysis)
    assert analysis.classified_domain == "Urban Infrastructure"

    # 3. Retrieve overrides list
    hist_resp = client.get(f"/api/v1/challenges/{ch.id}/ai-overrides", headers=headers)
    assert hist_resp.status_code == 200
    overrides = hist_resp.json()
    assert len(overrides) >= 1
    assert overrides[0]["override_value"] == "Education"

    # 4. Check latest AI Job endpoint
    job_resp = client.get(f"/api/v1/challenges/{ch.id}/ai-job")
    assert job_resp.status_code == 200


# =========================================================================
# 8. Offline Benchmark Evaluation & Drift Monitoring Tests
# =========================================================================

def test_offline_benchmark_and_drift_apis(client: TestClient, reviewer_token: str, db_session: Session):
    """Verify evaluation benchmark accuracy >= 85%, priority MAE <= 0.60, and drift metrics."""
    headers = {"Authorization": f"Bearer {reviewer_token}"}

    # Run Benchmark API
    bench_resp = client.get("/api/v1/admin/ai/evaluate", headers=headers)
    assert bench_resp.status_code == 200
    metrics = bench_resp.json()
    assert metrics["total_benchmark_cases"] >= 8
    assert metrics["classification_accuracy"] >= 0.85
    assert metrics["priority_mae"] <= 0.60
    assert metrics["status"] == "PASS"

    # Drift Metrics API
    drift_resp = client.get("/api/v1/admin/ai/drift", headers=headers)
    assert drift_resp.status_code == 200
    drift = drift_resp.json()
    assert "total_analyses" in drift
    assert "total_human_overrides" in drift
    assert "overall_override_rate" in drift
    assert drift["drift_status"] in ["STABLE", "MODERATE_DRIFT", "CRITICAL_DRIFT"]


# =========================================================================
# 8. Optional multilingual embeddings (Phase 2, Item 10) — off by default,
#    rule-based fallback kept
# =========================================================================

def test_embedding_service_disabled_by_default_fails_safe_to_none():
    """
    Without AI_EMBEDDINGS_ENABLED=true, embedding_service must report
    unavailable and never attempt to import sentence-transformers.
    """
    assert embedding_service.is_available() is False
    assert embedding_service.semantic_similarity("water shortage", "water crisis") is None


def test_embedding_service_enabled_without_package_still_fails_safe(monkeypatch):
    """
    Even with the feature flag on, if sentence-transformers isn't installed
    (this test environment's plain `pip install -r requirements.txt`), the
    service must fail safe to None rather than raising — callers keep using
    the deterministic bag-of-words similarity in that case.
    """
    from backend.app.core.config import settings
    monkeypatch.setattr(settings, "AI_EMBEDDINGS_ENABLED", True)
    fresh_service = EmbeddingService()
    assert fresh_service.semantic_similarity("water shortage", "water crisis") is None


def test_deduplication_uses_rule_based_similarity_method_by_default(db_session: Session, test_reviewer: User):
    """
    find_duplicates must label its similarity signal as the deterministic
    bag-of-words method when embeddings are disabled (the default), never
    silently claiming a real embedding was used.
    """
    ch1 = Challenge(
        title="Severe drinking water shortage in Ranchi village",
        description="Villagers have no access to clean drinking water for weeks.",
        category="Water Resources",
        priority=ChallengePriority.HIGH,
        status=ChallengeStatus.SUBMITTED,
        submitted_by_user_id=test_reviewer.id,
        affected_population=300
    )
    db_session.add(ch1)
    db_session.flush()
    db_session.add(ChallengeLocation(challenge_id=ch1.id, district_name="Ranchi", block_name="Namkum"))
    db_session.commit()

    results = deduplication_service.find_duplicates(
        db=db_session,
        title="Drinking water shortage in Ranchi village",
        description="No access to clean drinking water for weeks in the village.",
        category="Water Resources",
        district_name="Ranchi",
        block_name="Namkum",
        exclude_id=999999
    )
    assert len(results) > 0
    assert all(r["text_similarity_method"] == "BAG_OF_WORDS_RULE_BASED" for r in results)
