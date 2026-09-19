from typing import Set, Tuple, Optional, Dict
from fastapi import HTTPException, status
from backend.app.models.models import ChallengeStatus, UserRole, Challenge, StatusHistory, AuditLog
from sqlalchemy.orm import Session

# Map valid transitions: (FromStatus, ToStatus) -> Set of allowed UserRoles
ALLOWED_CHALLENGE_TRANSITIONS: Dict[Tuple[ChallengeStatus, ChallengeStatus], Set[UserRole]] = {
    # Initial automated screening
    (ChallengeStatus.SUBMITTED, ChallengeStatus.AI_ANALYSIS): {
        UserRole.GOVERNMENT_ADMIN, UserRole.CITIZEN
    },
    (ChallengeStatus.SUBMITTED, ChallengeStatus.UNDER_REVIEW): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.SUBMITTED, ChallengeStatus.VALIDATED): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.SUBMITTED, ChallengeStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.SUBMITTED, ChallengeStatus.DUPLICATE): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.SUBMITTED, ChallengeStatus.NEEDS_MORE_INFO): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.AI_ANALYSIS, ChallengeStatus.UNDER_REVIEW): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.AI_ANALYSIS, ChallengeStatus.VALIDATED): {
        UserRole.GOVERNMENT_ADMIN
    },
    # Moderation decisions
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.VALIDATED): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.UNIVERSITY_ASSIGNED): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.NEEDS_MORE_INFO): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.DUPLICATE): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN
    },
    # Resubmission after more info
    (ChallengeStatus.NEEDS_MORE_INFO, ChallengeStatus.SUBMITTED): {
        UserRole.CITIZEN, UserRole.GOVERNMENT_ADMIN
    },
    # Assignment to University
    (ChallengeStatus.VALIDATED, ChallengeStatus.UNIVERSITY_ASSIGNED): {
        UserRole.GOVERNMENT_ADMIN
    },
    # Project execution lifecycle
    (ChallengeStatus.UNIVERSITY_ASSIGNED, ChallengeStatus.TEAM_FORMED): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.TEAM_FORMED, ChallengeStatus.SOLUTION_PROPOSED): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.STUDENT, UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.TEAM_FORMED, ChallengeStatus.IN_PROGRESS): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.TEAM_FORMED, ChallengeStatus.FIELD_VERIFICATION): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.SOLUTION_PROPOSED, ChallengeStatus.APPROVED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.UNIVERSITY
    },
    (ChallengeStatus.APPROVED, ChallengeStatus.IN_PROGRESS): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.IN_PROGRESS, ChallengeStatus.PROTOTYPE): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.STUDENT, UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.PROTOTYPE, ChallengeStatus.FIELD_TESTING): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.FIELD_TESTING, ChallengeStatus.DEPLOYMENT): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.DEPLOYMENT, ChallengeStatus.FIELD_VERIFICATION): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.IN_PROGRESS, ChallengeStatus.FIELD_VERIFICATION): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN
    },
    # Formal government verification and closure
    (ChallengeStatus.FIELD_VERIFICATION, ChallengeStatus.RESOLVED): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.RESOLVED, ChallengeStatus.CLOSED): {
        UserRole.GOVERNMENT_ADMIN
    },
    # Rejection by Government at active stages
    (ChallengeStatus.VALIDATED, ChallengeStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN
    },
    (ChallengeStatus.UNIVERSITY_ASSIGNED, ChallengeStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN
    },
}

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
    ip_address: Optional[str] = None
) -> Challenge:
    """
    Validates state machine transition rules, updates status,
    records StatusHistory, and logs an immutable AuditLog record.
    """
    from_status = challenge.status
    if from_status == to_status:
        return challenge

    transition = (from_status, to_status)
    allowed_roles = ALLOWED_CHALLENGE_TRANSITIONS.get(transition)

    if not allowed_roles:
        raise StateMachineError(
            f"Illegal state transition from '{from_status.value}' to '{to_status.value}'. "
            f"This transition is not permitted by government workflow rules."
        )

    if actor_role not in allowed_roles:
        allowed_str = ", ".join([r.value for r in allowed_roles])
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Actor with role '{actor_role.value}' is not authorized to transition challenge to '{to_status.value}'. Required role: {allowed_str}."
        )

    # Apply transition
    challenge.status = to_status

    # Record historical status log
    history_entry = StatusHistory(
        challenge_id=challenge.id,
        from_status=from_status.value if from_status else None,
        to_status=to_status.value,
        updated_by=f"{actor_name} ({actor_role.value})",
        remarks=remarks or f"Transitioned from {from_status.value} to {to_status.value}"
    )
    db.add(history_entry)

    # Record immutable audit log
    audit_entry = AuditLog(
        actor_id=actor_id,
        actor_name=actor_name,
        actor_role=actor_role.value,
        action=f"CHALLENGE_STATUS_{to_status.value}",
        entity_name="Challenge",
        entity_id=challenge.id,
        old_state=from_status.value if from_status else None,
        new_state=to_status.value,
        ip_address=ip_address,
        reason=remarks
    )
    db.add(audit_entry)

    return challenge
