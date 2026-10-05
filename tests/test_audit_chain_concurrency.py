"""
Concurrent writers must extend the SHA-256 audit hash chain one event at a
time: no duplicate sequence numbers (HTTP 500s on submit under load) and no
forks. Found by the load test (docs/LOAD_TEST.md).
"""
import threading

import pytest

from backend.app.core.database import SessionLocal, engine
from backend.app.services.workflow_service import WorkflowService

WRITERS = 12
EVENTS_PER_WRITER = 3


def test_concurrent_audit_appends_keep_chain_intact():
    if engine.dialect.name != "postgresql":
        pytest.skip("Concurrent chain appends are serialised with a PostgreSQL advisory lock")

    barrier = threading.Barrier(WRITERS)
    errors = []

    def writer(n: int):
        db = SessionLocal()
        try:
            barrier.wait()
            for k in range(EVENTS_PER_WRITER):
                WorkflowService._record_domain_event(
                    db, "ConcurrencyProbe", n, "PROBE", None, None, None, {"writer": n, "event": k},
                )
                db.commit()
        except Exception as exc:  # collected and asserted below
            errors.append(repr(exc))
            db.rollback()
        finally:
            db.close()

    threads = [threading.Thread(target=writer, args=(n,)) for n in range(WRITERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    db = SessionLocal()
    try:
        assert WorkflowService.verify_audit_chain(db)["is_valid"] is True
        probes = WorkflowService.verify_audit_chain(db, entity_type="ConcurrencyProbe")
        assert probes["is_valid"] is True
    finally:
        db.close()
