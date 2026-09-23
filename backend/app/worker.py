"""
Distributed Resilient Background Worker for SIH 26043.
Orchestrates:
1. Asynchronous AI analysis jobs (AIJob).
2. Outbox notification delivery (NotificationOutbox).
3. Dead-letter queue handling and retry backoff.
4. Visibility timeout recovery for crashed/stalled workers.
5. Concurrency locking using `SELECT ... FOR UPDATE SKIP LOCKED` to prevent duplicate processing across multiple replicas.
"""

import sys
import time
import signal
import socket
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text, or_

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine
from backend.app.models.models import AIJob, AIJobStatus, NotificationOutbox, utc_now
from backend.app.services.ai.queue_service import ai_queue_service
from backend.app.services.notification_service import notification_service
from backend.app.core.telemetry import update_queue_depth

logger = logging.getLogger("worker")
logger.setLevel(logging.INFO)


class BackgroundWorker:
    def __init__(
        self,
        worker_id: Optional[str] = None,
        poll_interval: float = 2.0,
        visibility_timeout_seconds: int = 300,
    ):
        self.worker_id = worker_id or f"worker-{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        self.poll_interval = poll_interval
        self.visibility_timeout_seconds = visibility_timeout_seconds
        self.running = False
        self._is_postgres = not settings.DATABASE_URL.startswith("sqlite")

    def signal_handler(self, signum, frame):
        """Gracefully handle termination signals."""
        logger.info(f"[{self.worker_id}] Received shutdown signal ({signum}). Finishing current cycle...")
        self.running = False

    def recover_stale_jobs(self, db: Session):
        """
        Visibility timeout recovery: Detects jobs stuck in PROCESSING / SENDING longer
        than visibility_timeout_seconds (e.g. due to node crash) and re-queues them.
        """
        stale_threshold = utc_now() - timedelta(seconds=self.visibility_timeout_seconds)

        # 1. Recover stale AI jobs
        stale_ai_jobs = db.query(AIJob).filter(
            AIJob.status == AIJobStatus.PROCESSING,
            AIJob.updated_at <= stale_threshold
        ).all()
        for job in stale_ai_jobs:
            if job.attempts >= job.max_retries:
                job.status = AIJobStatus.DEAD_LETTER
                job.error_message = f"Job exceeded visibility timeout of {self.visibility_timeout_seconds}s and reached max retries."
                logger.warning(f"[{self.worker_id}] Moved stale AIJob #{job.id} to DEAD_LETTER.")
            else:
                job.status = AIJobStatus.PENDING
                job.next_run_at = utc_now()
                logger.info(f"[{self.worker_id}] Recovered stale AIJob #{job.id} back to PENDING.")

        # 2. Recover stale Outbox notifications
        stale_outbox = db.query(NotificationOutbox).filter(
            NotificationOutbox.delivery_status == "SENDING",
            NotificationOutbox.last_attempt_at <= stale_threshold
        ).all()
        for item in stale_outbox:
            if item.retry_count >= item.max_retries:
                item.delivery_status = "FAILED"
                item.failure_reason = f"Exceeded delivery visibility timeout of {self.visibility_timeout_seconds}s."
                logger.warning(f"[{self.worker_id}] Outbox #{item.id} delivery permanently failed (stale).")
            else:
                item.delivery_status = "PENDING"
                logger.info(f"[{self.worker_id}] Recovered stale Outbox #{item.id} back to PENDING.")

        db.commit()

    def claim_ai_jobs(self, db: Session, limit: int = 5) -> List[AIJob]:
        """
        Atomically claims available pending AI jobs using SELECT FOR UPDATE SKIP LOCKED
        on PostgreSQL to guarantee zero duplication between distributed workers.
        """
        now = utc_now()
        query = db.query(AIJob).filter(
            AIJob.status.in_([AIJobStatus.PENDING, AIJobStatus.FAILED]),
            AIJob.next_run_at <= now
        ).order_by(AIJob.id.asc()).limit(limit)

        if self._is_postgres:
            query = query.with_for_update(skip_locked=True)

        jobs = query.all()
        for job in jobs:
            job.status = AIJobStatus.PROCESSING
            job.attempts += 1
            job.updated_at = now
        db.commit()
        return jobs

    def claim_outbox_items(self, db: Session, limit: int = 10) -> List[NotificationOutbox]:
        """
        Atomically claims pending notification outbox entries with concurrency locking.
        """
        query = db.query(NotificationOutbox).filter(
            NotificationOutbox.delivery_status == "PENDING"
        ).order_by(NotificationOutbox.id.asc()).limit(limit)

        if self._is_postgres:
            query = query.with_for_update(skip_locked=True)

        items = query.all()
        for item in items:
            item.delivery_status = "SENDING"
            item.last_attempt_at = utc_now()
        db.commit()
        return items

    def process_claimed_ai_jobs(self, db: Session, jobs: List[AIJob]) -> int:
        processed = 0
        for job in jobs:
            try:
                logger.info(f"[{self.worker_id}] Processing AIJob #{job.id} for Challenge #{job.challenge_id}...")
                success = ai_queue_service.process_job(db, job)
                processed += 1
                logger.info(f"[{self.worker_id}] AIJob #{job.id} outcome: {'SUCCESS' if success else 'FAILED'}")
            except Exception as e:
                logger.error(f"[{self.worker_id}] Unexpected error processing AIJob #{job.id}: {str(e)}")
                job.status = AIJobStatus.FAILED
                job.error_message = f"Worker uncaught exception: {str(e)}"
                db.commit()
        return processed

    def process_claimed_outbox_items(self, db: Session, items: List[NotificationOutbox]) -> int:
        delivered = 0
        for item in items:
            try:
                # Reset status to PENDING so notification_service.deliver_outbox_item can transition it to SENT or FAILED
                item.delivery_status = "PENDING"
                notification_service.deliver_outbox_item(db, item)
                delivered += 1
            except Exception as e:
                logger.error(f"[{self.worker_id}] Outbox #{item.id} delivery error: {str(e)}")
                item.delivery_status = "FAILED"
                item.failure_reason = f"Worker delivery exception: {str(e)}"
                db.commit()
        return delivered

    def run_cycle(self, db: Session) -> int:
        """Executes a single end-to-end worker cycle."""
        # 1. Recover any stale/abandoned jobs
        self.recover_stale_jobs(db)

        # 2. Claim & execute AI jobs
        claimed_ai = self.claim_ai_jobs(db, limit=5)
        ai_count = self.process_claimed_ai_jobs(db, claimed_ai)

        # 3. Claim & execute notifications
        claimed_outbox = self.claim_outbox_items(db, limit=10)
        outbox_count = self.process_claimed_outbox_items(db, claimed_outbox)

        # 4. Update queue depth metrics
        pending_ai = db.query(AIJob).filter(AIJob.status == AIJobStatus.PENDING).count()
        pending_outbox = db.query(NotificationOutbox).filter(NotificationOutbox.delivery_status == "PENDING").count()
        update_queue_depth("ai_jobs", pending_ai)
        update_queue_depth("notification_outbox", pending_outbox)

        return ai_count + outbox_count

    def run(self, daemon: bool = True):
        """Worker lifecycle loop."""
        self.running = True
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        logger.info(f"[{self.worker_id}] Starting background worker daemon (mode={'daemon' if daemon else 'run-once'})...")

        while self.running:
            db = SessionLocal()
            try:
                handled = self.run_cycle(db)
                if not daemon:
                    logger.info(f"[{self.worker_id}] Run-once mode finished. Handled {handled} total jobs.")
                    break
                # If no jobs were handled, sleep poll_interval; otherwise continue immediately
                if handled == 0:
                    time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"[{self.worker_id}] Worker loop error: {str(e)}")
                time.sleep(self.poll_interval)
            finally:
                db.close()

        logger.info(f"[{self.worker_id}] Background worker stopped cleanly.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Distributed Background Worker for SIH 26043")
    parser.add_argument("--run-once", action="store_true", help="Process currently pending jobs and exit")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Polling interval in seconds")
    parser.add_argument("--worker-id", type=str, default=None, help="Custom worker identifier")
    args = parser.parse_args()

    worker = BackgroundWorker(
        worker_id=args.worker_id,
        poll_interval=args.poll_interval
    )
    worker.run(daemon=not args.run_once)


if __name__ == "__main__":
    main()
