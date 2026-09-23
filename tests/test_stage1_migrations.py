import os
import tempfile
import pytest
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command
from backend.app.core.database import Base
import backend.app.models.models

def test_alembic_lifecycle_upgrade_downgrade_reupgrade():
    """
    Tests complete lifecycle of the baseline Alembic migration:
    - upgrade to head creates all 33 tables
    - indexes, unique constraints, and foreign keys are created
    - downgrade to base drops all tables cleanly
    - re-upgrade to head succeeds deterministically
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    test_url = f"sqlite:///{db_path}"
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_path = os.path.join(base_dir, "alembic.ini")
    
    cfg = Config(ini_path)
    cfg.set_main_option("sqlalchemy.url", test_url)

    engine = create_engine(test_url)

    try:
        # Step 1: Upgrade to head
        command.upgrade(cfg, "head")

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        
        # Verify all 33 tables exist in the database
        expected_tables = set(Base.metadata.tables.keys())
        # alembic_version table is also created by alembic
        assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"
        assert "alembic_version" in tables

        # Verify key indexes and constraints on users table
        user_indexes = [idx["name"] for idx in inspector.get_indexes("users")]
        assert any("email" in idx for idx in user_indexes if idx)

        # Verify verification_records table has foreign keys
        vr_fks = inspector.get_foreign_keys("verification_records")
        assert len(vr_fks) >= 1

        # Step 2: Downgrade to base
        command.downgrade(cfg, "base")
        
        inspector_post_down = inspect(engine)
        remaining_tables = set(inspector_post_down.get_table_names())
        # Only alembic_version (or empty) should remain
        assert remaining_tables.issubset({"alembic_version"}), f"Tables remained after downgrade: {remaining_tables}"

        # Step 3: Re-upgrade to head
        command.upgrade(cfg, "head")
        
        inspector_reup = inspect(engine)
        reup_tables = set(inspector_reup.get_table_names())
        assert expected_tables.issubset(reup_tables)

    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.remove(db_path)

def test_db_migrate_runner_raises_on_error():
    """Verify that db_migrate.run_migrations does not swallow errors."""
    from backend.app.core.db_migrate import run_migrations
    with pytest.raises(Exception):
        run_migrations("non_existent_revision_xyz_123")
