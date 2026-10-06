"""
One-shot startup tasks for the demo deployment, run by docker-entrypoint.sh
before the API workers start (so several workers never race to seed):

  1. Apply Alembic migrations when RUN_MIGRATIONS_ON_START=true.
  2. With DEMO_MODE=true outside production, load the demo data: districts,
     universities, sample challenges and every demo account the login
     screen's persona picker offers (citizen, PRI, officer, verifier,
     university, faculty, student, industry, admin).

Every step is idempotent, so restarting the service is safe.

Run: python -m backend.app.services.demo_bootstrap
"""
import logging
import os

from backend.app.core.config import settings

logger = logging.getLogger("backend.demo_bootstrap")


def _truthy(name: str) -> bool:
    return os.getenv(name, "false").lower() in ("true", "1", "yes")


def run() -> None:
    if _truthy("RUN_MIGRATIONS_ON_START"):
        from backend.app.core.db_migrate import run_migrations
        run_migrations("head")

    if not settings.DEMO_MODE or settings.ENVIRONMENT == "production":
        logger.info("Demo seeding skipped (DEMO_MODE=%s, ENVIRONMENT=%s).", settings.DEMO_MODE, settings.ENVIRONMENT)
        return

    from backend.app.core.database import SessionLocal
    from backend.app.services.seed_data import ensure_sapthagiri_seeded, seed_database
    from backend.app.services.seed_flagship_demo import run_seed as seed_flagship_demo

    db = SessionLocal()
    try:
        seed_database(db)
        ensure_sapthagiri_seeded(db)
    finally:
        db.close()
    seed_flagship_demo()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    run()
