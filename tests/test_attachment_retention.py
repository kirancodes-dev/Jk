"""
Soft-deleted attachments stay restorable for ATTACHMENT_PURGE_DAYS (30), then
their stored file is deleted and the record is marked PURGED.
"""
import uuid
from datetime import timedelta

import pytest

from backend.app.core.config import settings
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.services.seed_data import seed_database
from backend.app.models.models import ChallengeAttachment, User, UserRole, utc_now
from backend.app.services.storage_service import storage_service


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    # Seed the demo data first: seed_database() skips seeding once any user
    # exists, so creating users here would starve later modules of demo accounts.
    settings.DEMO_MODE = True
    seed_database(session)
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def _attachment(db, owner, tmp_path, name):
    path = tmp_path / f"{name}.jpg"
    path.write_bytes(b"\xff\xd8\xff evidence")
    att = ChallengeAttachment(
        object_id=uuid.uuid4().hex, owner_id=owner.id, original_filename=f"{name}.jpg",
        detected_mime="image/jpeg", size_bytes=12, sha256_checksum="0" * 64, storage_key=str(path),
    )
    db.add(att)
    db.commit()
    return att, path


def test_soft_deleted_files_are_purged_after_retention_window(db, tmp_path):
    owner = User(email=f"retention-{uuid.uuid4().hex[:8]}@example.org", hashed_password="!",
                 full_name="Retention Owner", role=UserRole.CITIZEN)
    db.add(owner)
    db.commit()
    expired, expired_path = _attachment(db, owner, tmp_path, "expired")
    recent, recent_path = _attachment(db, owner, tmp_path, "recent")
    kept, kept_path = _attachment(db, owner, tmp_path, "kept")

    for att in (expired, recent):
        storage_service.soft_delete_attachment(att.object_id, owner.id, False, db)
        assert att.retention_state == "SOFT_DELETED" and att.soft_deleted_at is not None
    expired.soft_deleted_at = utc_now() - timedelta(days=31)
    recent.soft_deleted_at = utc_now() - timedelta(days=5)
    db.commit()

    purged_ids = {expired.object_id}
    assert storage_service.purge_expired_attachments(db) >= 1
    for att in (expired, recent, kept):
        db.refresh(att)

    assert expired.retention_state == "PURGED" and not expired_path.exists()
    assert recent.retention_state == "SOFT_DELETED" and recent_path.exists()
    assert kept.retention_state == "ACTIVE" and kept_path.exists()
    assert expired.object_id in purged_ids and expired.sha256_checksum == "0" * 64


def test_restore_clears_the_purge_clock(db, tmp_path):
    owner = User(email=f"restore-{uuid.uuid4().hex[:8]}@example.org", hashed_password="!",
                 full_name="Restore Owner", role=UserRole.CITIZEN)
    db.add(owner)
    db.commit()
    att, path = _attachment(db, owner, tmp_path, "restored")
    storage_service.soft_delete_attachment(att.object_id, owner.id, False, db)
    storage_service.restore_attachment(att.object_id, True, db)
    assert att.retention_state == "ACTIVE" and att.soft_deleted_at is None

    att.soft_deleted_at = None
    db.commit()
    storage_service.purge_expired_attachments(db, retention_days=0)
    db.refresh(att)
    assert att.retention_state == "ACTIVE" and path.exists()
