"""
Durable asynchronous outbox queue processor for AI analysis jobs in SIH 26043.
Implements idempotency keys, exponential backoff, dead-letter recovery, and
graceful degradation ensuring citizen challenges remain immediately usable even if AI is delayed.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.models import AIJob, AIJobStatus, Challenge, utc_now

logger = logging.getLogger("ai_queue_service")

class AIQueueService:
    def enqueue_ai_job(
        self,
        db: Session,
        challenge_id: int,
        job_type: str = "FULL_ANALYSIS",
        payload: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        backoff_seconds: int = 5
    ) -> AIJob:
        """
        Enqueues an AI analysis task in the durable outbox queue with idempotency.
        """
        idempotency_key = f"CHALLENGE_{challenge_id}_{job_type}"
        existing_job = db.query(AIJob).filter(AIJob.idempotency_key == idempotency_key).first()

        if existing_job:
            # If already pending, processing, or completed, return existing
            if existing_job.status in [AIJobStatus.PENDING, AIJobStatus.PROCESSING, AIJobStatus.COMPLETED]:
                return existing_job
            # If failed or dead-letter, allow reset and re-enqueue
            existing_job.status = AIJobStatus.PENDING
            existing_job.attempts = 0
            existing_job.next_run_at = utc_now()
            existing_job.error_message = None
            db.commit()
            db.refresh(existing_job)
            return existing_job

        new_job = AIJob(
            challenge_id=challenge_id,
            idempotency_key=idempotency_key,
            job_type=job_type,
            status=AIJobStatus.PENDING,
            payload_json=json.dumps(payload or {}),
            attempts=0,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
            next_run_at=utc_now(),
            timeout_seconds=60
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        return new_job

    def process_job(self, db: Session, job: AIJob) -> bool:
        """
        Executes a single AI job with error handling, exponential backoff, and local fallback recovery.
        """
        from backend.app.services.ai_service import ai_service

        challenge = db.query(Challenge).filter(Challenge.id == job.challenge_id).first()
        if not challenge:
            job.status = AIJobStatus.DEAD_LETTER
            job.error_message = f"Challenge #{job.challenge_id} not found."
            job.completed_at = utc_now()
            db.commit()
            return False

        job.status = AIJobStatus.PROCESSING
        db.commit()

        try:
            # Execute primary AI analysis
            ai_service.analyze_challenge(challenge, db)

            job.status = AIJobStatus.COMPLETED
            job.error_message = None
            job.completed_at = utc_now()
            db.commit()
            return True
        except Exception as exc:
            db.rollback()
            logger.exception(f"AI Job #{job.id} failed on challenge #{job.challenge_id}: {exc}")
            job.attempts += 1
            err_msg = str(exc)

            if job.attempts >= job.max_retries:
                # Max retries reached: Execute safe local fallback so submission is never stalled
                try:
                    ai_service.analyze_challenge_fallback(challenge, db, fallback_reason=f"Exceeded {job.max_retries} attempts: {err_msg}")
                    job.status = AIJobStatus.FALLBACK_COMPLETED
                    job.error_message = f"Executed deterministic fallback after error: {err_msg}"
                except Exception as fallback_exc:
                    job.status = AIJobStatus.DEAD_LETTER
                    job.error_message = f"Fatal failure and fallback error: {fallback_exc}"
                job.completed_at = utc_now()
            else:
                job.status = AIJobStatus.FAILED
                backoff = job.backoff_seconds * (2 ** (job.attempts - 1))
                job.next_run_at = utc_now() + timedelta(seconds=backoff)
                job.error_message = err_msg

            db.commit()
            return False

    def process_pending_jobs(self, db: Session, limit: int = 10) -> int:
        """
        Polls and executes pending and retryable failed AI jobs whose next_run_at <= now.
        """
        now_dt = utc_now()
        jobs = db.query(AIJob).filter(
            AIJob.status.in_([AIJobStatus.PENDING, AIJobStatus.FAILED]),
            AIJob.next_run_at <= now_dt
        ).order_by(AIJob.id.asc()).limit(limit).all()

        processed_count = 0
        for job in jobs:
            success = self.process_job(db, job)
            if success:
                processed_count += 1

        return processed_count

    def retry_job(self, db: Session, job_id: int) -> AIJob:
        """Force manual retry of a failed or dead-letter job."""
        job = db.query(AIJob).filter(AIJob.id == job_id).first()
        if not job:
            raise ValueError(f"AIJob #{job_id} not found")

        job.status = AIJobStatus.PENDING
        job.attempts = 0
        job.next_run_at = utc_now()
        job.error_message = None
        job.completed_at = None
        db.commit()
        db.refresh(job)
        return job

queue_service = AIQueueService()
ai_queue_service = queue_service
