"""
Seeds a realistic dataset for the load test (docs/LOAD_TEST.md).

Creates load-test citizen accounts and ~1,200 challenges spread across all
24 Jharkhand districts and 11 domains, with locations, AI analyses and status
history, on top of the normal and flagship demo seeds (all demo roles). Report texts are the 440 labelled
reports in scripts/ai_eval/train_dev.jsonl, so titles and descriptions read
like real submissions (English, Hindi, Hinglish, SMS-style).

Refuses to run unless DEMO_MODE=true and ENVIRONMENT is not production, the
same guard as the demo seeder. Re-running is safe: it only tops up to the
requested counts.

Run:
  DATABASE_URL=postgresql://... DEMO_MODE=true ENVIRONMENT=development \
  PYTHONPATH=. python scripts/seed_load_test_data.py --challenges 1200 --citizens 50
"""
import argparse
import json
import random
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, ".")

from backend.app.core.config import settings  # noqa: E402
from backend.app.core.database import SessionLocal  # noqa: E402
from backend.app.core.security import get_password_hash  # noqa: E402
from backend.app.models.models import (  # noqa: E402
    AIAnalysis, Challenge, ChallengeLocation, ChallengePriority, ChallengeStatus, Citizen,
    District, StatusHistory, University, User, UserRole, utc_now,
)
from backend.app.services.ai.classification_service import classification_service  # noqa: E402
from backend.app.services.seed_data import ensure_sapthagiri_seeded, seed_database  # noqa: E402
from backend.app.services.seed_flagship_demo import run_seed as seed_flagship_demo  # noqa: E402

# Seeded rows are tagged by idempotency key, so re-runs only top up.
SEED_KEY_PREFIX = "loadtest-seed-"
# example.org is reserved for documentation (RFC 2606) and passes email validation.
CITIZEN_EMAIL = "loadtest.citizen{:03d}@loadtest.example.org"
REPORTS = Path(__file__).resolve().parent / "ai_eval" / "train_dev.jsonl"

# Rough shape of a live pilot queue: most reports are early in the pipeline.
STATUS_WEIGHTS = [
    (ChallengeStatus.SUBMITTED, 22), (ChallengeStatus.AI_ANALYSIS, 8),
    (ChallengeStatus.UNDER_REVIEW, 15), (ChallengeStatus.NEEDS_MORE_INFO, 4),
    (ChallengeStatus.VALIDATED, 12), (ChallengeStatus.UNIVERSITY_ASSIGNED, 8),
    (ChallengeStatus.TEAM_FORMED, 4), (ChallengeStatus.IN_PROGRESS, 8),
    (ChallengeStatus.FIELD_TESTING, 3), (ChallengeStatus.RESOLVED, 8),
    (ChallengeStatus.CLOSED, 4), (ChallengeStatus.REJECTED, 3), (ChallengeStatus.DUPLICATE, 1),
]
ASSIGNED = {
    ChallengeStatus.UNIVERSITY_ASSIGNED, ChallengeStatus.TEAM_FORMED, ChallengeStatus.IN_PROGRESS,
    ChallengeStatus.FIELD_TESTING, ChallengeStatus.RESOLVED, ChallengeStatus.CLOSED,
}
TIERS = [("PANCHAYAT", 1, 55), ("BLOCK", 2, 25), ("DISTRICT", 3, 15), ("STATE", 4, 5)]
URGENCY_TO_PRIORITY = {
    "Low": ChallengePriority.LOW, "Medium": ChallengePriority.MEDIUM,
    "High": ChallengePriority.HIGH, "Critical": ChallengePriority.CRITICAL,
}


def ensure_citizens(db, count: int, password: str):
    hashed = get_password_hash(password)
    citizens = []
    for i in range(1, count + 1):
        email = CITIZEN_EMAIL.format(i)
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, hashed_password=hashed, full_name=f"Load Test Citizen {i:03d}",
                        role=UserRole.CITIZEN, is_active=True, is_verified=True)
            db.add(user)
            db.flush()
        citizen = db.query(Citizen).filter(Citizen.user_id == user.id).first()
        if not citizen:
            citizen = Citizen(user_id=user.id)
            db.add(citizen)
            db.flush()
        citizens.append((user, citizen))
    db.commit()
    return citizens


def seed_challenges(db, target: int, citizens, rng: random.Random) -> int:
    existing = db.query(Challenge).filter(Challenge.idempotency_key.like(f"{SEED_KEY_PREFIX}%")).count()
    if existing >= target:
        return 0
    reports = [json.loads(line) for line in REPORTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    districts = db.query(District).order_by(District.id).all()
    universities = db.query(University).all()
    statuses, status_w = zip(*STATUS_WEIGHTS)
    now = utc_now()

    created = 0
    for n in range(existing, target):
        report = reports[n % len(reports)]
        district = districts[n % len(districts)]
        user, citizen = citizens[n % len(citizens)]
        status = rng.choices(statuses, status_w)[0]
        tier, level, _ = rng.choices(TIERS, [t[2] for t in TIERS])[0]
        urgency = rng.choices(["Low", "Medium", "High", "Critical"], [20, 45, 25, 10])[0]
        created_at = now - timedelta(days=rng.uniform(0, 180), minutes=rng.randint(0, 1440))
        classified = classification_service.classify(report["title"], report["description"], report["domain"]).output

        challenge = Challenge(
            title=f"{report['title']} ({district.name})"[:255],
            description=report["description"],
            category=report["domain"],
            urgency=urgency,
            priority=URGENCY_TO_PRIORITY[urgency],
            expected_impact=f"Relief for affected households in {district.name} district.",
            status=status,
            current_tier=tier,
            escalation_level=level,
            citizen_id=citizen.id,
            submitted_by_user_id=user.id,
            submitter_role=UserRole.CITIZEN.value,
            assigned_university_id=rng.choice(universities).id if status in ASSIGNED and universities else None,
            affected_population=rng.choice([25, 60, 120, 300, 800, 1500, 4000]),
            source_type=rng.choice(["MOBILE_APP", "WEB_PORTAL", "FIELD_VISIT"]),
            idempotency_key=f"{SEED_KEY_PREFIX}{n:05d}",
            submission_language="hi" if report["lang"].startswith("hi") else "en",
            consent_given=True,
            created_at=created_at,
            updated_at=created_at,
        )
        challenge.location = ChallengeLocation(
            district_id=district.id,
            district_name=district.name,
            block_name=f"{district.name} Block {n % 7 + 1}",
            village_or_city=f"Village {n % 97 + 1}",
            latitude=round(district.latitude + rng.uniform(-0.15, 0.15), 6),
            longitude=round(district.longitude + rng.uniform(-0.15, 0.15), 6),
        )
        challenge.ai_analysis = AIAnalysis(
            cleaned_text=report["description"][:500],
            classified_domain=classified["domain"],
            detected_priority=URGENCY_TO_PRIORITY[urgency],
            extracted_keywords=", ".join(classified["keywords"]),
            required_expertise=", ".join(classified["expertise"]),
            recommended_solution=classified["solution"],
            confidence_score=classified["confidence"],
            requires_human_review=classified["requires_human_review"],
        )
        challenge.status_history = [StatusHistory(
            from_status="SUBMITTED", to_status=status.value, updated_by="Load-test seed",
            remarks="Seeded for load testing", changed_at=created_at,
        )]
        db.add(challenge)
        created += 1
        if created % 200 == 0:
            db.commit()
    db.commit()
    return created


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--challenges", type=int, default=1200)
    parser.add_argument("--citizens", type=int, default=50)
    parser.add_argument("--password", default="password123", help="password for the load-test citizens")
    parser.add_argument("--seed", type=int, default=26043, help="random seed, for a reproducible dataset")
    args = parser.parse_args()

    if settings.ENVIRONMENT == "production" or not settings.DEMO_MODE:
        sys.exit("Refusing to seed: requires DEMO_MODE=true and a non-production ENVIRONMENT.")

    db = SessionLocal()
    try:
        seed_database(db)
        ensure_sapthagiri_seeded(db)
        seed_flagship_demo()  # officer, verifier and PRI demo accounts
        citizens = ensure_citizens(db, args.citizens, args.password)
        created = seed_challenges(db, args.challenges, citizens, random.Random(args.seed))
        total = db.query(Challenge).count()
        districts = db.query(ChallengeLocation.district_name).distinct().count()
        print(f"Created {created} load-test challenges; database now holds {total} challenges "
              f"across {districts} districts and {args.citizens} load-test citizens.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
