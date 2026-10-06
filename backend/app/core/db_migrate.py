import logging
import os
import sys
from alembic.config import Config
from alembic import command
from backend.app.core.config import settings

logger = logging.getLogger("backend.migrations")

def get_alembic_config() -> Config:
    """Constructs an Alembic Config pointing to the project alembic.ini."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ini_path = os.path.join(base_dir, "alembic.ini")
    if not os.path.exists(ini_path):
        raise FileNotFoundError(f"alembic.ini not found at expected path: {ini_path}")
    
    # Leave sqlalchemy.url at alembic.ini's placeholder so alembic/env.py uses the
    # application engine (built from settings.DATABASE_URL), which pins the
    # psycopg2 driver and the UTC session time zone. Passing the raw
    # "postgresql://" URL here made SQLAlchemy 2.1 pick psycopg (v3), which is not
    # installed, so migrations on container start failed.
    return Config(ini_path)

def run_migrations(target_revision: str = "head"):
    """
    Executes database migrations via Alembic.
    Raises an exception on failure without swallowing errors.
    """
    logger.info(f"Applying database migrations to revision: {target_revision} on {settings.ENVIRONMENT} environment...")
    try:
        cfg = get_alembic_config()
        command.upgrade(cfg, target_revision)
        logger.info(f"Database migrations successfully applied to {target_revision}.")
    except Exception as e:
        logger.error(f"Database migration failed: {type(e).__name__}: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    target = sys.argv[1] if len(sys.argv) > 1 else "head"
    try:
        run_migrations(target)
        print(f"[✓] Database schema migration to '{target}' completed successfully.")
    except Exception as ex:
        print(f"[✗] Migration failed: {ex}", file=sys.stderr)
        sys.exit(1)

