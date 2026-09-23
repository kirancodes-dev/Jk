from typing import Set, Tuple, Optional, Dict
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.models import ChallengeStatus, UserRole, Challenge, User
from backend.app.services.workflow_service import (
    WorkflowService,
    ALLOWED_CHALLENGE_TRANSITIONS,
    ALLOWED_MILESTONE_TRANSITIONS
)


class StateMachineError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def validate_and_apply_challenge_transition(
    db: Session,
    challenge: Challenge,
    to_status: ChallengeStatus,
    actor_id: int,
    actor_role: UserRole,
    actor_name: str,
    remarks: Optional[str] = None,
    ip_address: Optional[str] = None,
    expected_version: Optional[int] = None
) -> Challenge:
    """
    Authoritative state machine transition delegation.
    Routes all transitions through WorkflowService to ensure optimistic concurrency,
    jurisdiction validation, and cryptographic audit hash chaining.
    """
    actor = db.query(User).filter(User.id == actor_id).first()
    if not actor:
        # Create lightweight actor proxy for automated system tasks
        actor = User(
            id=actor_id,
            role=actor_role,
            full_name=actor_name,
            admin_tier="STATE",
            email="system@jharkhand.gov.in",
            hashed_password=""
        )

    try:
        return WorkflowService.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=to_status,
            actor=actor,
            expected_version=expected_version,
            remarks=remarks,
            payload={"ip_address": ip_address} if ip_address else {}
        )
    except HTTPException as e:
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            raise StateMachineError(e.detail)
        raise e
