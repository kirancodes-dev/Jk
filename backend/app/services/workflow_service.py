import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple, Set
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.models import (
    Challenge, ChallengeStatus, User, UserRole, Project, ProjectMilestone, MilestoneStatus,
    VerificationRecord, ChallengeAllocation, AllocationStatus, DomainAuditEvent,
    StatusHistory, AuditLog, University, OrganizationProfile, utc_now,
    SolutionProposal, ProposalStatus, TeamInvitation, TeamInvitationStatus,
    ProjectMember, ProjectMembershipHistory, MembershipAction, Student, Faculty,
    EvidenceFile, ReviewComment, IndustryCollaboration, AgreementStatus,
    FundingRecord, FundingHoldState, IPConsentRecord, IPConsentStatus, IPRecord,
    OutcomeMetric, ProjectClosureRecord, OutcomeReport, ReportedOutcome
)
from backend.app.services.finance_integration_service import finance_integration_service
from backend.app.routers.deps import verify_challenge_jurisdiction

VALID_REJECTION_REASONS = {
    "OUT_OF_JURISDICTION",
    "DUPLICATE",
    "INSUFFICIENT_INFORMATION",
    "COMMERCIALLY_VIABLE_EXISTING_SERVICE",
    "NOT_A_COMMUNITY_ISSUE",
    "POLICY_EXCLUSION",
    "OTHER"
}

ALLOWED_CHALLENGE_TRANSITIONS: Dict[Tuple[ChallengeStatus, ChallengeStatus], Set[UserRole]] = {
    # Screening & Intake
    (ChallengeStatus.SUBMITTED, ChallengeStatus.AI_ANALYSIS): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.CITIZEN,
        UserRole.COMMUNITY_ORG, UserRole.PRI, UserRole.ULB
    },
    (ChallengeStatus.SUBMITTED, ChallengeStatus.UNDER_REVIEW): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.SUBMITTED, ChallengeStatus.VALIDATED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.SUBMITTED, ChallengeStatus.NEEDS_MORE_INFO): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.SUBMITTED, ChallengeStatus.DUPLICATE): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.SUBMITTED, ChallengeStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.AI_ANALYSIS, ChallengeStatus.UNDER_REVIEW): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.AI_ANALYSIS, ChallengeStatus.VALIDATED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.AI_ANALYSIS, ChallengeStatus.NEEDS_MORE_INFO): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.AI_ANALYSIS, ChallengeStatus.DUPLICATE): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.AI_ANALYSIS, ChallengeStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    # Moderation Decisions
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.VALIDATED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.NEEDS_MORE_INFO): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.DUPLICATE): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.UNIVERSITY_ASSIGNED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.PAUSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    # Information Request & Clarification Resubmission
    (ChallengeStatus.NEEDS_MORE_INFO, ChallengeStatus.UNDER_REVIEW): {
        UserRole.CITIZEN, UserRole.COMMUNITY_ORG, UserRole.PRI, UserRole.ULB,
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.NEEDS_MORE_INFO, ChallengeStatus.SUBMITTED): {
        UserRole.CITIZEN, UserRole.COMMUNITY_ORG, UserRole.PRI, UserRole.ULB,
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.NEEDS_MORE_INFO, ChallengeStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    # Assignment to Academic Institutions
    (ChallengeStatus.SUBMITTED, ChallengeStatus.UNIVERSITY_ASSIGNED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.AI_ANALYSIS, ChallengeStatus.UNIVERSITY_ASSIGNED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.UNDER_REVIEW, ChallengeStatus.UNIVERSITY_ASSIGNED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.VALIDATED, ChallengeStatus.UNIVERSITY_ASSIGNED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.VALIDATED, ChallengeStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.VALIDATED, ChallengeStatus.PAUSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    # University Team Formation & Solution Lifecycle
    (ChallengeStatus.UNIVERSITY_ASSIGNED, ChallengeStatus.TEAM_FORMED): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.UNIVERSITY_ASSIGNED, ChallengeStatus.VALIDATED): {
        UserRole.UNIVERSITY, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.UNIVERSITY_ASSIGNED, ChallengeStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.UNIVERSITY_ASSIGNED, ChallengeStatus.PAUSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    (ChallengeStatus.TEAM_FORMED, ChallengeStatus.SOLUTION_PROPOSED): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.STUDENT,
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.TEAM_FORMED, ChallengeStatus.IN_PROGRESS): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.TEAM_FORMED, ChallengeStatus.FIELD_VERIFICATION): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.TEAM_FORMED, ChallengeStatus.PAUSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    (ChallengeStatus.SOLUTION_PROPOSED, ChallengeStatus.APPROVED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.UNIVERSITY
    },
    (ChallengeStatus.SOLUTION_PROPOSED, ChallengeStatus.TEAM_FORMED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.SOLUTION_PROPOSED, ChallengeStatus.PAUSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    (ChallengeStatus.APPROVED, ChallengeStatus.IN_PROGRESS): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.APPROVED, ChallengeStatus.PROTOTYPE): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.STUDENT,
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.APPROVED, ChallengeStatus.PAUSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    (ChallengeStatus.IN_PROGRESS, ChallengeStatus.PROTOTYPE): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.STUDENT,
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.IN_PROGRESS, ChallengeStatus.FIELD_TESTING): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.IN_PROGRESS, ChallengeStatus.DEPLOYMENT): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.IN_PROGRESS, ChallengeStatus.FIELD_VERIFICATION): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.IN_PROGRESS, ChallengeStatus.PAUSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    (ChallengeStatus.PROTOTYPE, ChallengeStatus.FIELD_TESTING): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.PROTOTYPE, ChallengeStatus.PAUSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    (ChallengeStatus.FIELD_TESTING, ChallengeStatus.DEPLOYMENT): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.FIELD_TESTING, ChallengeStatus.PAUSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    (ChallengeStatus.DEPLOYMENT, ChallengeStatus.FIELD_VERIFICATION): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.DEPLOYMENT, ChallengeStatus.PAUSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    # Verification, Resolution, Impact Audit & Closure
    (ChallengeStatus.FIELD_VERIFICATION, ChallengeStatus.RESOLVED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.FIELD_VERIFICATION, ChallengeStatus.CLOSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.FIELD_VERIFICATION, ChallengeStatus.DEPLOYMENT): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.FIELD_VERIFICATION, ChallengeStatus.PAUSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.DEPLOYMENT, ChallengeStatus.RESOLVED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.DEPLOYMENT, ChallengeStatus.CLOSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.IN_PROGRESS, ChallengeStatus.RESOLVED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.IN_PROGRESS, ChallengeStatus.CLOSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    (ChallengeStatus.RESOLVED, ChallengeStatus.IMPACT_AUDITED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.RESOLVED, ChallengeStatus.CLOSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.RESOLVED, ChallengeStatus.REOPENED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.CITIZEN,
        UserRole.COMMUNITY_ORG, UserRole.PRI, UserRole.ULB
    },

    (ChallengeStatus.IMPACT_AUDITED, ChallengeStatus.CLOSED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    # Reopening & Appeals
    (ChallengeStatus.CLOSED, ChallengeStatus.REOPENED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.CITIZEN,
        UserRole.COMMUNITY_ORG, UserRole.PRI, UserRole.ULB
    },
    (ChallengeStatus.REJECTED, ChallengeStatus.REOPENED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.CITIZEN,
        UserRole.COMMUNITY_ORG, UserRole.PRI, UserRole.ULB
    },
    (ChallengeStatus.DUPLICATE, ChallengeStatus.REOPENED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.CITIZEN,
        UserRole.COMMUNITY_ORG, UserRole.PRI, UserRole.ULB
    },
    (ChallengeStatus.REJECTED, ChallengeStatus.UNDER_REVIEW): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.CITIZEN,
        UserRole.COMMUNITY_ORG, UserRole.PRI, UserRole.ULB
    },
    (ChallengeStatus.DUPLICATE, ChallengeStatus.UNDER_REVIEW): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.CITIZEN,
        UserRole.COMMUNITY_ORG, UserRole.PRI, UserRole.ULB
    },
    (ChallengeStatus.REOPENED, ChallengeStatus.UNDER_REVIEW): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.REOPENED, ChallengeStatus.VALIDATED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },

    # Pause & Resume
    (ChallengeStatus.PAUSED, ChallengeStatus.UNDER_REVIEW): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.PAUSED, ChallengeStatus.VALIDATED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.PAUSED, ChallengeStatus.UNIVERSITY_ASSIGNED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.PAUSED, ChallengeStatus.TEAM_FORMED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.PAUSED, ChallengeStatus.IN_PROGRESS): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.PAUSED, ChallengeStatus.PROTOTYPE): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.PAUSED, ChallengeStatus.FIELD_TESTING): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ChallengeStatus.PAUSED, ChallengeStatus.DEPLOYMENT): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
}

ALLOWED_MILESTONE_TRANSITIONS: Dict[Tuple[MilestoneStatus, MilestoneStatus], Set[UserRole]] = {
    (MilestoneStatus.NOT_STARTED, MilestoneStatus.IN_PROGRESS): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.STUDENT, UserRole.GOVERNMENT_ADMIN
    },
    (MilestoneStatus.IN_PROGRESS, MilestoneStatus.SUBMITTED): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.STUDENT, UserRole.GOVERNMENT_ADMIN
    },
    (MilestoneStatus.SUBMITTED, MilestoneStatus.APPROVED): {
        UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (MilestoneStatus.SUBMITTED, MilestoneStatus.IN_PROGRESS): {
        UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (MilestoneStatus.SUBMITTED, MilestoneStatus.REVISION_REQUESTED): {
        UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.UNIVERSITY
    },
    (MilestoneStatus.REVISION_REQUESTED, MilestoneStatus.IN_PROGRESS): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.STUDENT, UserRole.GOVERNMENT_ADMIN
    },
    (MilestoneStatus.REVISION_REQUESTED, MilestoneStatus.SUBMITTED): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR, UserRole.STUDENT, UserRole.GOVERNMENT_ADMIN
    },
    (MilestoneStatus.APPROVED, MilestoneStatus.COMPLETED): {
        UserRole.FACULTY_MENTOR, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.UNIVERSITY
    },
}

ALLOWED_PROPOSAL_TRANSITIONS: Dict[Tuple[ProposalStatus, ProposalStatus], Set[UserRole]] = {
    (ProposalStatus.DRAFT, ProposalStatus.SUBMITTED): {
        UserRole.STUDENT, UserRole.FACULTY_MENTOR, UserRole.UNIVERSITY
    },
    (ProposalStatus.SUBMITTED, ProposalStatus.FACULTY_REVIEWED): {UserRole.FACULTY_MENTOR},
    (ProposalStatus.SUBMITTED, ProposalStatus.REVISION_REQUESTED): {
        UserRole.FACULTY_MENTOR, UserRole.UNIVERSITY, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ProposalStatus.SUBMITTED, ProposalStatus.REJECTED): {UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER},
    (ProposalStatus.FACULTY_REVIEWED, ProposalStatus.HEI_APPROVED): {UserRole.UNIVERSITY},
    (ProposalStatus.FACULTY_REVIEWED, ProposalStatus.REVISION_REQUESTED): {
        UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR
    },
    (ProposalStatus.FACULTY_REVIEWED, ProposalStatus.REJECTED): {UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.UNIVERSITY},
    (ProposalStatus.HEI_APPROVED, ProposalStatus.GOVERNMENT_REVIEWED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ProposalStatus.HEI_APPROVED, ProposalStatus.REVISION_REQUESTED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ProposalStatus.GOVERNMENT_REVIEWED, ProposalStatus.INDUSTRY_FEEDBACK): {
        UserRole.INDUSTRY, UserRole.RESEARCH_LAB, UserRole.INNOVATION_HUB
    },
    (ProposalStatus.GOVERNMENT_REVIEWED, ProposalStatus.APPROVED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ProposalStatus.GOVERNMENT_REVIEWED, ProposalStatus.REVISION_REQUESTED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ProposalStatus.GOVERNMENT_REVIEWED, ProposalStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ProposalStatus.INDUSTRY_FEEDBACK, ProposalStatus.APPROVED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ProposalStatus.INDUSTRY_FEEDBACK, ProposalStatus.REVISION_REQUESTED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.UNIVERSITY
    },
    (ProposalStatus.INDUSTRY_FEEDBACK, ProposalStatus.REJECTED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER
    },
    (ProposalStatus.APPROVED, ProposalStatus.ARCHIVED): {
        UserRole.GOVERNMENT_ADMIN, UserRole.UNIVERSITY
    },
    (ProposalStatus.REJECTED, ProposalStatus.ARCHIVED): {UserRole.GOVERNMENT_ADMIN},
}

PARTNER_ROLES = {UserRole.INDUSTRY, UserRole.RESEARCH_LAB, UserRole.INNOVATION_HUB}
REVIEWER_ROLES = {UserRole.UNIVERSITY, UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER}

ALLOWED_AGREEMENT_TRANSITIONS: Dict[Tuple[AgreementStatus, AgreementStatus], Set[UserRole]] = {
    (AgreementStatus.OFFERED, AgreementStatus.UNDER_REVIEW): REVIEWER_ROLES,
    (AgreementStatus.OFFERED, AgreementStatus.DECLINED): REVIEWER_ROLES | PARTNER_ROLES,
    (AgreementStatus.UNDER_REVIEW, AgreementStatus.CONFLICT_CHECK): REVIEWER_ROLES,
    (AgreementStatus.UNDER_REVIEW, AgreementStatus.DECLINED): REVIEWER_ROLES,
    (AgreementStatus.CONFLICT_CHECK, AgreementStatus.ACCEPTED): REVIEWER_ROLES,
    (AgreementStatus.CONFLICT_CHECK, AgreementStatus.DECLINED): REVIEWER_ROLES,
    (AgreementStatus.ACCEPTED, AgreementStatus.CONTRACT_RECORDED): REVIEWER_ROLES,
    (AgreementStatus.ACCEPTED, AgreementStatus.TERMINATED): REVIEWER_ROLES,
    (AgreementStatus.CONTRACT_RECORDED, AgreementStatus.ACTIVE): REVIEWER_ROLES,
    (AgreementStatus.CONTRACT_RECORDED, AgreementStatus.TERMINATED): REVIEWER_ROLES,
    (AgreementStatus.ACTIVE, AgreementStatus.MILESTONE_LINKED): REVIEWER_ROLES | {UserRole.FACULTY_MENTOR},
    (AgreementStatus.ACTIVE, AgreementStatus.COMPLETED): REVIEWER_ROLES,
    (AgreementStatus.ACTIVE, AgreementStatus.TERMINATED): REVIEWER_ROLES,
    (AgreementStatus.MILESTONE_LINKED, AgreementStatus.COMPLETED): REVIEWER_ROLES,
    (AgreementStatus.MILESTONE_LINKED, AgreementStatus.TERMINATED): REVIEWER_ROLES,
}


class WorkflowService:
    @classmethod
    def _canonical_timestamp_iso(cls, dt: Optional[datetime]) -> str:
        """Returns deterministic UTC ISO-8601 string compatible with DB datetime serialization."""
        if not dt:
            return ""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    @classmethod
    def _check_and_increment_version(cls, entity: Any, expected_version: Optional[int] = None) -> None:
        """
        Enforces optimistic concurrency control.
        Raises 409 Conflict if expected_version does not match current entity version.
        Increments entity.version on success.
        """
        current_version = getattr(entity, "version", 1) or 1
        if expected_version is not None and expected_version != current_version:
            reload_url = None
            if isinstance(entity, Challenge):
                reload_url = f"/api/v1/challenges/{entity.id}"
            elif isinstance(entity, Project):
                reload_url = f"/api/v1/projects/{entity.id}"

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "VERSION_CONFLICT",
                    "message": f"Entity version mismatch: expected {expected_version}, found {current_version}. Please reload the resource before submitting changes.",
                    "current_version": current_version,
                    "reload_url": reload_url
                }
            )
        entity.version = current_version + 1

    @classmethod
    def _record_domain_event(
        cls,
        db: Session,
        entity_type: str,
        entity_id: int,
        action: str,
        previous_state: Optional[str],
        new_state: Optional[str],
        actor: Optional[User],
        payload: Dict[str, Any],
        notes: Optional[str] = None,
        reason_code: Optional[str] = None,
        is_internal: bool = False,
        jurisdiction_level: Optional[str] = None,
        jurisdiction_value: Optional[str] = None,
    ) -> DomainAuditEvent:
        """
        Appends an immutable, SHA-256 hash-chained domain audit event to the ledger.
        """
        # Flush any pending events in the session so sequence number and hash chaining are exact
        db.flush()
        last_event = db.query(DomainAuditEvent).order_by(desc(DomainAuditEvent.sequence_number)).first()
        prev_event_hash = last_event.event_hash if last_event else ("0" * 64)
        new_seq = (last_event.sequence_number + 1) if last_event else 1

        payload_json = json.dumps(payload or {}, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()

        now = utc_now()
        ts_str = cls._canonical_timestamp_iso(now)
        actor_id_str = str(actor.id) if actor else ""
        content_string = f"{prev_event_hash}|{new_seq}|{entity_type}|{entity_id}|{action}|{previous_state or ''}|{new_state or ''}|{payload_hash}|{actor_id_str}|{ts_str}"
        event_hash = hashlib.sha256(content_string.encode('utf-8')).hexdigest()

        event = DomainAuditEvent(
            sequence_number=new_seq,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            previous_state=previous_state,
            new_state=new_state,
            actor_id=actor.id if actor else None,
            actor_role=actor.role.value if actor else "SYSTEM",
            jurisdiction_level=jurisdiction_level or (actor.admin_tier if actor else None),
            jurisdiction_value=jurisdiction_value or (actor.district_name if actor else None),
            reason_code=reason_code,
            notes=notes,
            payload_json=payload_json,
            payload_hash=payload_hash,
            prev_event_hash=prev_event_hash,
            event_hash=event_hash,
            is_internal=is_internal,
            created_at=now
        )
        db.add(event)
        db.flush()

        # Mirror to legacy tables for query compatibility
        if entity_type == "Challenge" and previous_state != new_state:
            db.add(StatusHistory(
                challenge_id=entity_id,
                from_status=previous_state,
                to_status=new_state or previous_state or "UNKNOWN",
                updated_by=f"{actor.full_name if actor else 'System'} ({actor.role.value if actor else 'SYSTEM'})",
                remarks=notes or f"Transitioned to {new_state}"
            ))

        db.add(AuditLog(
            actor_id=actor.id if actor else None,
            actor_name=actor.full_name if actor else "System",
            actor_role=actor.role.value if actor else "SYSTEM",
            action=action,
            entity_name=entity_type,
            entity_id=entity_id,
            old_state=previous_state,
            new_state=new_state,
            reason=notes
        ))

        return event

    @classmethod
    def verify_audit_chain(
        cls,
        db: Session,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Cryptographically verifies the SHA-256 hash chain of the domain audit log.
        Returns whether the chain is unbroken and identifies any tampered sequence.
        """
        query = db.query(DomainAuditEvent).order_by(DomainAuditEvent.sequence_number.asc())
        if entity_type:
            query = query.filter(DomainAuditEvent.entity_type == entity_type)
        if entity_id:
            query = query.filter(DomainAuditEvent.entity_id == entity_id)

        events = query.all()
        if not events:
            return {"is_valid": True, "verified_count": 0, "tampered_sequence": None, "reason": None}

        # Global sequence verification
        # Fetch all global events to ensure absolute chain verification
        all_events = db.query(DomainAuditEvent).order_by(DomainAuditEvent.sequence_number.asc()).all()
        expected_prev_hash = "0" * 64

        for ev in all_events:
            # 1. Verify payload hash
            computed_payload_hash = hashlib.sha256(ev.payload_json.encode('utf-8')).hexdigest()
            if computed_payload_hash != ev.payload_hash:
                return {
                    "is_valid": False,
                    "verified_count": ev.sequence_number - 1,
                    "tampered_sequence": ev.sequence_number,
                    "reason": f"Payload hash mismatch at sequence #{ev.sequence_number}"
                }

            # 2. Verify previous event link
            if ev.prev_event_hash != expected_prev_hash:
                return {
                    "is_valid": False,
                    "verified_count": ev.sequence_number - 1,
                    "tampered_sequence": ev.sequence_number,
                    "reason": f"Chain link broken at sequence #{ev.sequence_number}. Expected prev {expected_prev_hash}, found {ev.prev_event_hash}"
                }

            # 3. Verify event hash
            actor_id_str = str(ev.actor_id) if ev.actor_id else ""
            ts_str = cls._canonical_timestamp_iso(ev.created_at)
            content_string = f"{ev.prev_event_hash}|{ev.sequence_number}|{ev.entity_type}|{ev.entity_id}|{ev.action}|{ev.previous_state or ''}|{ev.new_state or ''}|{ev.payload_hash}|{actor_id_str}|{ts_str}"
            computed_event_hash = hashlib.sha256(content_string.encode('utf-8')).hexdigest()
            if computed_event_hash != ev.event_hash:
                return {
                    "is_valid": False,
                    "verified_count": ev.sequence_number - 1,
                    "tampered_sequence": ev.sequence_number,
                    "reason": f"Event hash mismatch at sequence #{ev.sequence_number}"
                }

            expected_prev_hash = ev.event_hash

        return {
            "is_valid": True,
            "verified_count": len(all_events),
            "tampered_sequence": None,
            "reason": None
        }

    @classmethod
    def sanitize_history_for_public(cls, events: List[DomainAuditEvent]) -> List[Dict[str, Any]]:
        """
        Redacts sensitive government officer notes and confidential review rationale for public viewers.
        """
        sanitized = []
        for ev in events:
            notes = ev.notes
            if ev.is_internal:
                notes = "[Confidential Administrative Review]"
            sanitized.append({
                "sequence_number": ev.sequence_number,
                "action": ev.action,
                "previous_state": ev.previous_state,
                "new_state": ev.new_state,
                "actor_role": ev.actor_role,
                "timestamp": cls._canonical_timestamp_iso(ev.created_at) if ev.created_at else None,
                "notes": notes,
                "event_hash": ev.event_hash
            })
        return sanitized

    @classmethod
    def transition_challenge(
        cls,
        db: Session,
        challenge: Challenge,
        to_status: ChallengeStatus,
        actor: Optional[User] = None,
        expected_version: Optional[int] = None,
        remarks: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        is_internal: bool = False
    ) -> Challenge:
        """
        Validates transition rules, enforces jurisdiction, updates status, and appends to hash chain.
        """
        if actor is None:
            actor = challenge.submitted_by_user or User(
                id=challenge.submitted_by_user_id or 1,
                role=UserRole.GOVERNMENT_ADMIN,
                full_name="Automated System Worker",
                admin_tier="STATE"
            )

        # 1. Enforce optimistic concurrency first
        cls._check_and_increment_version(challenge, expected_version)

        from_status = challenge.status
        if from_status == to_status:
            return challenge

        transition = (from_status, to_status)
        allowed_roles = ALLOWED_CHALLENGE_TRANSITIONS.get(transition)
        if not allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Illegal state transition from '{from_status.value}' to '{to_status.value}'. This transition is not permitted by government workflow rules."
            )

        if actor.role not in allowed_roles:
            allowed_str = ", ".join([r.value for r in allowed_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Actor with role '{actor.role.value}' is not authorized to transition challenge to '{to_status.value}'. Required role: {allowed_str}."
            )

        # Enforce jurisdiction for government actors
        if actor.role in {UserRole.GOVERNMENT_OFFICER, UserRole.GOVERNMENT_ADMIN}:
            verify_challenge_jurisdiction(challenge, actor, db, action=f"transition_to_{to_status.value.lower()}")

        # Deployment gate: at least one recorded field/lab/user-trial test outcome
        # (PASS or PARTIAL) across the challenge's project(s) is required before a
        # prototype can be deployed — a challenge can no longer reach DEPLOYMENT on
        # milestone/status progression alone.
        if to_status == ChallengeStatus.DEPLOYMENT and not is_internal:
            project_ids = [p.id for p in challenge.projects]
            has_passing_test = bool(project_ids) and db.query(OutcomeReport).filter(
                OutcomeReport.project_id.in_(project_ids),
                OutcomeReport.outcome.in_([ReportedOutcome.PASS, ReportedOutcome.PARTIAL])
            ).first()
            if not has_passing_test:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Deployment requires at least one recorded field/lab/user-trial test outcome "
                           "(PASS or PARTIAL) for this project. Submit a test report before deploying."
                )

        challenge.status = to_status

        # Append domain event
        cls._record_domain_event(
            db=db,
            entity_type="Challenge",
            entity_id=challenge.id,
            action=f"TRANSITION_{to_status.value}",
            previous_state=from_status.value if from_status else None,
            new_state=to_status.value,
            actor=actor,
            payload=payload or {},
            notes=remarks,
            is_internal=is_internal,
            jurisdiction_level=challenge.current_tier,
            jurisdiction_value=challenge.location.district_name if challenge.location else None
        )
        return challenge

    @classmethod
    def accept_for_review(
        cls,
        db: Session,
        challenge_id: int,
        actor: User,
        expected_version: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        verify_challenge_jurisdiction(challenge, actor, db, action="accept_review")
        return cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.UNDER_REVIEW,
            actor=actor,
            expected_version=expected_version,
            remarks=notes or "Accepted by government review queue for triage",
            payload={"action": "ACCEPT_REVIEW"}
        )

    @classmethod
    def request_more_information(
        cls,
        db: Session,
        challenge_id: int,
        actor: User,
        clarification_items: List[str],
        expected_version: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        verify_challenge_jurisdiction(challenge, actor, db, action="request_info")
        return cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.NEEDS_MORE_INFO,
            actor=actor,
            expected_version=expected_version,
            remarks=notes or "Additional clarification requested from submitter",
            payload={"clarification_items": clarification_items, "notes": notes}
        )

    @classmethod
    def submit_clarification(
        cls,
        db: Session,
        challenge_id: int,
        actor: User,
        responses: Dict[str, Any],
        additional_attachments: Optional[List[str]] = None,
        expected_version: Optional[int] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        return cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.UNDER_REVIEW,
            actor=actor,
            expected_version=expected_version,
            remarks="Clarification provided by submitter; resubmitted for review",
            payload={"responses": responses, "attachments": additional_attachments or []}
        )

    @classmethod
    def validate_challenge(
        cls,
        db: Session,
        challenge_id: int,
        actor: User,
        expected_version: Optional[int] = None,
        remarks: Optional[str] = None,
        assigned_tier: Optional[str] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        verify_challenge_jurisdiction(challenge, actor, db, action="validate")
        if assigned_tier:
            challenge.current_tier = assigned_tier.upper()
        return cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.VALIDATED,
            actor=actor,
            expected_version=expected_version,
            remarks=remarks or f"Challenge reviewed and officially validated by {actor.full_name}",
            payload={"assigned_tier": challenge.current_tier, "remarks": remarks}
        )

    @classmethod
    def reject_challenge(
        cls,
        db: Session,
        challenge_id: int,
        actor: User,
        reason: str,
        reason_code: Optional[str] = "OTHER",
        expected_version: Optional[int] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        verify_challenge_jurisdiction(challenge, actor, db, action="reject")

        norm_code = (reason_code or "OTHER").upper()
        if norm_code not in VALID_REJECTION_REASONS:
            norm_code = "OTHER"

        challenge.moderation_reason = f"[{norm_code}] {reason}"
        challenge.moderated_by = actor.full_name
        challenge.moderated_at = utc_now()

        return cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.REJECTED,
            actor=actor,
            expected_version=expected_version,
            remarks=reason,
            payload={"reason_code": norm_code, "reason": reason}
        )

    @classmethod
    def confirm_duplicate(
        cls,
        db: Session,
        challenge_id: int,
        canonical_challenge_id: int,
        actor: User,
        expected_version: Optional[int] = None,
        remarks: Optional[str] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        if challenge.id == canonical_challenge_id:
            raise HTTPException(status_code=400, detail="Challenge cannot be marked as duplicate of itself")

        canonical = db.query(Challenge).filter(Challenge.id == canonical_challenge_id).first()
        if not canonical:
            raise HTTPException(status_code=404, detail="Canonical challenge not found")

        verify_challenge_jurisdiction(challenge, actor, db, action="mark_duplicate")
        challenge.moderation_reason = f"Duplicate of #{canonical.id} ({canonical.title})"
        challenge.moderated_by = actor.full_name
        challenge.moderated_at = utc_now()

        return cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.DUPLICATE,
            actor=actor,
            expected_version=expected_version,
            remarks=remarks or f"Duplicate of #{canonical.id}: {canonical.title}",
            payload={"canonical_challenge_id": canonical.id, "canonical_title": canonical.title}
        )

    @classmethod
    def keep_separate(
        cls,
        db: Session,
        challenge_id: int,
        compared_challenge_id: int,
        actor: User,
        justification: str,
        expected_version: Optional[int] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        verify_challenge_jurisdiction(challenge, actor, db, action="keep_separate")
        cls._check_and_increment_version(challenge, expected_version)

        cls._record_domain_event(
            db=db,
            entity_type="Challenge",
            entity_id=challenge.id,
            action="DISMISS_DUPLICATE_CANDIDATE",
            previous_state=challenge.status.value,
            new_state=challenge.status.value,
            actor=actor,
            payload={"compared_challenge_id": compared_challenge_id, "justification": justification},
            notes=f"Dismissed duplicate candidate #{compared_challenge_id}: {justification}",
            is_internal=True
        )
        return challenge

    @classmethod
    def assign_challenge(
        cls,
        db: Session,
        challenge_id: int,
        actor: User,
        university_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        deadline_days: int = 14,
        capacity_notes: Optional[str] = None,
        remarks: Optional[str] = None,
        expected_version: Optional[int] = None
    ) -> ChallengeAllocation:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        verify_challenge_jurisdiction(challenge, actor, db, action="assign_challenge")

        # Resolve organization and university
        target_org_id = organization_id
        target_univ_id = university_id

        if not target_org_id and target_univ_id:
            univ = db.query(University).filter(University.id == target_univ_id).first()
            if not univ:
                raise HTTPException(status_code=404, detail="University not found")
            if univ.user:
                org_prof = db.query(OrganizationProfile).filter(OrganizationProfile.user_id == univ.user.id).first()
                if org_prof:
                    target_org_id = org_prof.id
        elif target_org_id and not target_univ_id:
            org_prof = db.query(OrganizationProfile).filter(OrganizationProfile.id == target_org_id).first()
            if org_prof and org_prof.user:
                univ = db.query(University).filter(University.user_id == org_prof.user.id).first()
                if univ:
                    target_univ_id = univ.id

        if challenge.assigned_university_id and target_univ_id and challenge.assigned_university_id != target_univ_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Conflict: Challenge #{challenge_id} is already assigned to university #{challenge.assigned_university_id}. Conflicting assignment rejected."
            )

        if not target_org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign challenge: the target institution has no registered and verified organization profile. "
                       "Government accreditation verification must be completed via /organizations before assignment."
            )

        # Gate: only verified, active, capacity-available HEIs may receive an assignment
        org_prof = db.query(OrganizationProfile).filter(OrganizationProfile.id == target_org_id).first()
        if not org_prof or org_prof.verification_status != "VERIFIED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Target organization is not a government-verified institution. Assignment rejected."
            )
        if target_univ_id:
            univ = db.query(University).filter(University.id == target_univ_id).first()
            if not univ or not univ.is_verified_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Target university is not a verified, active HEI. Assignment rejected."
                )
            active_count = db.query(Project).filter(
                Project.university_id == univ.id,
                Project.current_stage != "Terminated"
            ).count()
            if active_count >= univ.capacity_max_active_projects:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Conflict: University has reached its declared capacity of {univ.capacity_max_active_projects} active projects."
                )

        # Supersede any previous offered allocations
        prior_active = db.query(ChallengeAllocation).filter(
            ChallengeAllocation.challenge_id == challenge.id,
            ChallengeAllocation.status == AllocationStatus.OFFERED
        ).all()
        for prev in prior_active:
            prev.status = AllocationStatus.SUPERSEDED

        deadline_at = utc_now() + timedelta(days=deadline_days)
        reassigned_from_id = prior_active[0].id if prior_active else None

        allocation = ChallengeAllocation(
            challenge_id=challenge.id,
            assigned_by_user_id=actor.id,
            assigned_to_org_id=target_org_id,
            status=AllocationStatus.OFFERED,
            allocated_at=utc_now(),
            deadline_at=deadline_at,
            capacity_assessment=capacity_notes,
            reassigned_from_allocation_id=reassigned_from_id
        )
        db.add(allocation)
        db.flush()

        if target_univ_id:
            challenge.assigned_university_id = target_univ_id

        cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.UNIVERSITY_ASSIGNED,
            actor=actor,
            expected_version=expected_version,
            remarks=remarks or f"Formally allocated to organization #{target_org_id}",
            payload={
                "allocation_id": allocation.id,
                "organization_id": target_org_id,
                "university_id": target_univ_id,
                "deadline_at": deadline_at.isoformat(),
                "capacity_notes": capacity_notes
            }
        )
        return allocation

    @classmethod
    def respond_allocation(
        cls,
        db: Session,
        allocation_id: int,
        actor: User,
        decision: str,
        notes: Optional[str] = None,
        coi_declared: bool = False,
        expected_version: Optional[int] = None
    ) -> ChallengeAllocation:
        allocation = db.query(ChallengeAllocation).filter(ChallengeAllocation.id == allocation_id).first()
        if not allocation:
            raise HTTPException(status_code=404, detail="Allocation record not found")

        # Verify authority: user must belong to assigned organization or be admin
        org = allocation.assigned_to_org
        if actor.role != UserRole.GOVERNMENT_ADMIN and (not org or org.user_id != actor.id):
            # Check university profile association
            if actor.university_profile:
                org_check = db.query(OrganizationProfile).filter(OrganizationProfile.user_id == actor.id).first()
                if not org_check or org_check.id != allocation.assigned_to_org_id:
                    raise HTTPException(status_code=403, detail="User is not authorized to respond for this organization allocation.")
            else:
                raise HTTPException(status_code=403, detail="User is not authorized to respond for this organization allocation.")

        decision_upper = decision.upper()
        if decision_upper not in {"ACCEPT", "DECLINE"}:
            raise HTTPException(status_code=400, detail="Decision must be either 'ACCEPT' or 'DECLINE'.")

        challenge = allocation.challenge
        cls._check_and_increment_version(challenge, expected_version)

        allocation.responded_at = utc_now()
        allocation.response_notes = notes

        if decision_upper == "ACCEPT":
            if allocation.deadline_at:
                deadline = allocation.deadline_at
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                if utc_now() > deadline:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Assignment response deadline ({cls._canonical_timestamp_iso(allocation.deadline_at)}) has passed. "
                               "This assignment can no longer be accepted; request government reassignment."
                    )
            if not coi_declared:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Conflict of interest (CoI) declaration is mandatory before accepting societal challenge allocation."
                )
            allocation.status = AllocationStatus.ACCEPTED
            allocation.coi_declared = True

            cls._record_domain_event(
                db=db,
                entity_type="ChallengeAllocation",
                entity_id=allocation.id,
                action="ALLOCATION_ACCEPTED",
                previous_state=AllocationStatus.OFFERED.value,
                new_state=AllocationStatus.ACCEPTED.value,
                actor=actor,
                payload={"allocation_id": allocation.id, "coi_declared": True, "notes": notes},
                notes=notes or "Allocation accepted by recipient institution"
            )
        else:
            if not notes or not notes.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A decline reason is mandatory when declining a challenge assignment."
                )
            allocation.status = AllocationStatus.DECLINED
            challenge.assigned_university_id = None

            # Revert challenge to VALIDATED
            challenge.status = ChallengeStatus.VALIDATED
            cls._record_domain_event(
                db=db,
                entity_type="Challenge",
                entity_id=challenge.id,
                action="ALLOCATION_DECLINED",
                previous_state=ChallengeStatus.UNIVERSITY_ASSIGNED.value,
                new_state=ChallengeStatus.VALIDATED.value,
                actor=actor,
                payload={"allocation_id": allocation.id, "reason": notes},
                notes=f"Allocation declined by institution: {notes}"
            )

        return allocation

    @classmethod
    def escalate_tier(
        cls,
        db: Session,
        challenge_id: int,
        target_tier: str,
        remarks: str,
        actor: User,
        expected_version: Optional[int] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        verify_challenge_jurisdiction(challenge, actor, db, action="escalate")

        target_tier_upper = target_tier.upper()
        tier_levels = {"PANCHAYAT": 1, "BLOCK": 2, "DISTRICT": 3, "STATE": 4}
        if target_tier_upper not in tier_levels:
            raise HTTPException(status_code=400, detail=f"Invalid escalation tier '{target_tier}'. Must be one of: {list(tier_levels.keys())}")

        old_tier = challenge.current_tier or "PANCHAYAT"
        new_level = tier_levels[target_tier_upper]

        cls._check_and_increment_version(challenge, expected_version)
        challenge.current_tier = target_tier_upper
        challenge.escalation_level = new_level
        challenge.escalated_by = actor.full_name
        challenge.escalation_remarks = remarks

        cls._record_domain_event(
            db=db,
            entity_type="Challenge",
            entity_id=challenge.id,
            action="CHALLENGE_ESCALATED",
            previous_state=old_tier,
            new_state=target_tier_upper,
            actor=actor,
            payload={"old_tier": old_tier, "new_tier": target_tier_upper, "remarks": remarks},
            notes=f"Escalated from {old_tier} to {target_tier_upper}: {remarks}"
        )
        return challenge

    @classmethod
    def pause_challenge(
        cls,
        db: Session,
        challenge_id: int,
        reason: str,
        actor: User,
        expected_version: Optional[int] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        verify_challenge_jurisdiction(challenge, actor, db, action="pause")
        return cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.PAUSED,
            actor=actor,
            expected_version=expected_version,
            remarks=reason,
            payload={"pause_reason": reason}
        )

    @classmethod
    def resume_challenge(
        cls,
        db: Session,
        challenge_id: int,
        actor: User,
        remarks: Optional[str] = None,
        expected_version: Optional[int] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        verify_challenge_jurisdiction(challenge, actor, db, action="resume")

        # Determine target state to resume to (default to UNDER_REVIEW or VALIDATED)
        to_status = ChallengeStatus.UNDER_REVIEW
        if challenge.assigned_university_id:
            to_status = ChallengeStatus.UNIVERSITY_ASSIGNED

        return cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=to_status,
            actor=actor,
            expected_version=expected_version,
            remarks=remarks or "Challenge resumed from paused state",
            payload={"resumed_to": to_status.value}
        )

    @classmethod
    def reopen_challenge(
        cls,
        db: Session,
        challenge_id: int,
        reason: str,
        actor: User,
        expected_version: Optional[int] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        if actor.role in {UserRole.GOVERNMENT_OFFICER, UserRole.GOVERNMENT_ADMIN}:
            verify_challenge_jurisdiction(challenge, actor, db, action="reopen")

        return cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.REOPENED,
            actor=actor,
            expected_version=expected_version,
            remarks=reason,
            payload={"reopen_reason": reason}
        )

    @classmethod
    def appeal_challenge(
        cls,
        db: Session,
        challenge_id: int,
        grounds: str,
        actor: User,
        evidence: Optional[List[str]] = None
    ) -> Challenge:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")

        if challenge.status not in {ChallengeStatus.REJECTED, ChallengeStatus.DUPLICATE}:
            raise HTTPException(
                status_code=400,
                detail=f"Appeals can only be lodged against REJECTED or DUPLICATE challenges (current status: {challenge.status.value})."
            )

        # Transition back to UNDER_REVIEW with appeal record
        return cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.UNDER_REVIEW,
            actor=actor,
            remarks=f"Citizen appeal lodged: {grounds}",
            payload={"grounds": grounds, "evidence": evidence or []}
        )

    @classmethod
    def transition_project(
        cls,
        db: Session,
        project: Project,
        to_stage: str,
        actor: User,
        expected_version: Optional[int] = None,
        remarks: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> Project:
        from_stage = project.current_stage
        cls._check_and_increment_version(project, expected_version)
        project.current_stage = to_stage

        cls._record_domain_event(
            db=db,
            entity_type="Project",
            entity_id=project.id,
            action=f"PROJECT_STAGE_{to_stage.upper().replace(' ', '_')}",
            previous_state=from_stage,
            new_state=to_stage,
            actor=actor,
            payload=payload or {},
            notes=remarks or f"Project transitioned from {from_stage} to {to_stage}"
        )
        return project

    @classmethod
    def transition_milestone(
        cls,
        db: Session,
        milestone: ProjectMilestone,
        to_status: MilestoneStatus,
        actor: User,
        expected_version: Optional[int] = None,
        remarks: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> ProjectMilestone:
        from_status = milestone.status
        if from_status == to_status:
            return milestone

        transition = (from_status, to_status)
        allowed_roles = ALLOWED_MILESTONE_TRANSITIONS.get(transition)
        if allowed_roles and actor.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Actor role '{actor.role.value}' not authorized to transition milestone to '{to_status.value}'."
            )

        cls._check_and_increment_version(milestone, expected_version)
        milestone.status = to_status
        if to_status == MilestoneStatus.APPROVED:
            milestone.approved_by_faculty = True
            milestone.approved_at = utc_now()
        elif to_status == MilestoneStatus.COMPLETED:
            milestone.completion_percentage = 100.0

        cls._record_domain_event(
            db=db,
            entity_type="ProjectMilestone",
            entity_id=milestone.id,
            action=f"MILESTONE_{to_status.value}",
            previous_state=from_status.value if from_status else None,
            new_state=to_status.value,
            actor=actor,
            payload=payload or {},
            notes=remarks or f"Milestone #{milestone.id} status updated to {to_status.value}"
        )
        return milestone

    @classmethod
    def transition_verification(
        cls,
        db: Session,
        verification_record: VerificationRecord,
        decision: str,
        actor: User,
        expected_version: Optional[int] = None,
        notes: Optional[str] = None
    ) -> VerificationRecord:
        decision_upper = decision.upper()
        if decision_upper not in {"VERIFIED", "REJECTED"}:
            raise HTTPException(status_code=400, detail="Verification decision must be 'VERIFIED' or 'REJECTED'.")

        from_status = verification_record.verification_status
        cls._check_and_increment_version(verification_record, expected_version)

        verification_record.verification_status = decision_upper
        verification_record.verified_at = utc_now()
        verification_record.inspection_notes = notes

        cls._record_domain_event(
            db=db,
            entity_type="VerificationRecord",
            entity_id=verification_record.id,
            action=f"VERIFICATION_{decision_upper}",
            previous_state=from_status,
            new_state=decision_upper,
            actor=actor,
            payload={"decision": decision_upper, "notes": notes},
            notes=notes or f"Verification decision: {decision_upper}"
        )
        return verification_record

    # ------------------------------------------------------------------
    # Stage 6: Weighted milestone progress, deliverable review workflow
    # ------------------------------------------------------------------

    @classmethod
    def recalculate_project_progress(cls, db: Session, project: Project) -> Project:
        """
        Derives project.progress_percentage exclusively from approved/completed weighted
        milestones. Never accepts a client-supplied percentage.
        """
        milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project.id).all()
        earned = sum(
            (m.weight_pct or 0.0) for m in milestones
            if m.status in (MilestoneStatus.APPROVED, MilestoneStatus.COMPLETED)
        )
        project.progress_percentage = round(min(earned, 100.0), 2)
        return project

    @classmethod
    def submit_milestone(
        cls,
        db: Session,
        milestone: ProjectMilestone,
        actor: User,
        notes: Optional[str] = None
    ) -> ProjectMilestone:
        """A milestone can only be submitted once it has at least one current evidence file."""
        has_evidence = db.query(EvidenceFile).filter(
            EvidenceFile.entity_type == "MILESTONE_DELIVERABLE",
            EvidenceFile.entity_id == milestone.id,
            EvidenceFile.is_current == True  # noqa: E712
        ).first()
        if not has_evidence:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one deliverable evidence file must be uploaded before this milestone can be submitted for review."
            )
        return cls.transition_milestone(
            db=db,
            milestone=milestone,
            to_status=MilestoneStatus.SUBMITTED,
            actor=actor,
            remarks=notes or "Milestone submitted with evidence for faculty review"
        )

    @classmethod
    def review_milestone(
        cls,
        db: Session,
        milestone: ProjectMilestone,
        decision: str,
        actor: User,
        notes: str
    ) -> ProjectMilestone:
        """
        Faculty/government review decision on a submitted milestone. Requires a mandatory
        review comment; approval recalculates project progress from weighted milestones.
        """
        decision_upper = decision.upper()
        target_map = {
            "APPROVE": MilestoneStatus.APPROVED,
            "APPROVED": MilestoneStatus.APPROVED,
            "REVISION_REQUESTED": MilestoneStatus.REVISION_REQUESTED,
            "REJECTED": MilestoneStatus.REVISION_REQUESTED,
        }
        to_status = target_map.get(decision_upper)
        if not to_status:
            raise HTTPException(status_code=400, detail="Decision must be one of: APPROVE, REVISION_REQUESTED")

        milestone.review_notes = notes
        milestone.reviewed_by_user_id = actor.id

        db.add(ReviewComment(
            project_id=milestone.project_id,
            entity_type="MILESTONE",
            entity_id=milestone.id,
            author_id=actor.id,
            content=notes
        ))

        cls.transition_milestone(
            db=db,
            milestone=milestone,
            to_status=to_status,
            actor=actor,
            remarks=notes
        )

        project = db.query(Project).filter(Project.id == milestone.project_id).first()
        if project:
            cls.recalculate_project_progress(db, project)
        return milestone

    # ------------------------------------------------------------------
    # Stage 6: Versioned solution proposal workflow
    # ------------------------------------------------------------------

    @classmethod
    def transition_proposal(
        cls,
        db: Session,
        proposal: SolutionProposal,
        to_status: ProposalStatus,
        actor: User,
        notes: str
    ) -> SolutionProposal:
        from_status = proposal.status
        if from_status == to_status:
            return proposal

        allowed_roles = ALLOWED_PROPOSAL_TRANSITIONS.get((from_status, to_status))
        if not allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Illegal proposal transition from '{from_status.value}' to '{to_status.value}'."
            )
        if actor.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Actor role '{actor.role.value}' is not authorized to transition proposal to '{to_status.value}'."
            )

        proposal.status = to_status
        proposal.updated_at = utc_now()
        if to_status == ProposalStatus.FACULTY_REVIEWED:
            proposal.faculty_review_notes = notes
        elif to_status == ProposalStatus.HEI_APPROVED:
            proposal.hei_approval_notes = notes
            proposal.hei_approved_by_user_id = actor.id
        elif to_status == ProposalStatus.GOVERNMENT_REVIEWED:
            proposal.government_review_notes = notes
            proposal.government_reviewed_by_user_id = actor.id
        elif to_status == ProposalStatus.REVISION_REQUESTED:
            proposal.revision_requested_reason = notes
        elif to_status == ProposalStatus.APPROVED:
            proposal.government_review_notes = notes
            proposal.government_reviewed_by_user_id = actor.id
            proposal.is_approved_by_gov = True

        db.add(ReviewComment(
            project_id=proposal.project_id,
            entity_type="PROPOSAL",
            entity_id=proposal.id,
            author_id=actor.id,
            content=notes
        ))

        cls._record_domain_event(
            db=db,
            entity_type="SolutionProposal",
            entity_id=proposal.id,
            action=f"PROPOSAL_{to_status.value}",
            previous_state=from_status.value,
            new_state=to_status.value,
            actor=actor,
            payload={"notes": notes, "version": proposal.version},
            notes=notes
        )
        return proposal

    # ------------------------------------------------------------------
    # Stage 6: Team invitations & membership lifecycle
    # ------------------------------------------------------------------

    @classmethod
    def respond_team_invitation(
        cls,
        db: Session,
        invitation: TeamInvitation,
        actor: User,
        decision: str,
        conflict_declared: bool = False,
        conflict_notes: Optional[str] = None,
        response_notes: Optional[str] = None
    ) -> TeamInvitation:
        decision_upper = decision.upper()
        if decision_upper not in {"ACCEPT", "DECLINE"}:
            raise HTTPException(status_code=400, detail="Decision must be 'ACCEPT' or 'DECLINE'.")
        if invitation.status != TeamInvitationStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Invitation is no longer pending (current status: {invitation.status.value}).")

        invitation.responded_at = utc_now()
        invitation.response_notes = response_notes
        invitation.conflict_declared = conflict_declared
        invitation.conflict_notes = conflict_notes

        if decision_upper == "DECLINE":
            invitation.status = TeamInvitationStatus.DECLINED
            cls._record_domain_event(
                db=db, entity_type="TeamInvitation", entity_id=invitation.id,
                action="INVITATION_DECLINED", previous_state="PENDING", new_state="DECLINED",
                actor=actor, payload={"notes": response_notes}, notes=response_notes
            )
            return invitation

        invitation.status = TeamInvitationStatus.ACCEPTED

        if invitation.student_id:
            member = ProjectMember(
                project_id=invitation.project_id,
                student_id=invitation.student_id,
                department_id=invitation.department_id,
                role_in_team=invitation.role_in_team,
                invitation_id=invitation.id,
                start_date=invitation.proposed_start_date or utc_now(),
                end_date=invitation.proposed_end_date,
                conflict_declared=conflict_declared,
                conflict_notes=conflict_notes,
                is_active=True
            )
            db.add(member)
            db.add(ProjectMembershipHistory(
                project_id=invitation.project_id,
                student_id=invitation.student_id,
                action=MembershipAction.ADDED,
                role_in_team=invitation.role_in_team,
                actor_id=actor.id,
                reason="Team invitation accepted"
            ))
        elif invitation.faculty_id:
            project = db.query(Project).filter(Project.id == invitation.project_id).first()
            if project:
                project.faculty_mentor_id = invitation.faculty_id
                project.faculty_mentor_status = "ACCEPTED"
            db.add(ProjectMembershipHistory(
                project_id=invitation.project_id,
                faculty_id=invitation.faculty_id,
                action=MembershipAction.ADDED,
                role_in_team="Faculty Mentor",
                actor_id=actor.id,
                reason="Mentorship invitation accepted"
            ))

        cls._record_domain_event(
            db=db, entity_type="TeamInvitation", entity_id=invitation.id,
            action="INVITATION_ACCEPTED", previous_state="PENDING", new_state="ACCEPTED",
            actor=actor, payload={"notes": response_notes, "conflict_declared": conflict_declared}, notes=response_notes
        )
        return invitation

    @classmethod
    def remove_project_member(
        cls,
        db: Session,
        member: ProjectMember,
        actor: User,
        reason: str,
        replacement_student_id: Optional[int] = None,
        replacement_role_in_team: Optional[str] = None
    ) -> None:
        member.is_active = False
        member.end_date = utc_now()

        action = MembershipAction.REPLACED if replacement_student_id else MembershipAction.REMOVED
        db.add(ProjectMembershipHistory(
            project_id=member.project_id,
            student_id=member.student_id,
            action=action,
            previous_member_student_id=member.student_id if replacement_student_id else None,
            role_in_team=member.role_in_team,
            actor_id=actor.id,
            reason=reason
        ))

        if replacement_student_id:
            new_member = ProjectMember(
                project_id=member.project_id,
                student_id=replacement_student_id,
                department_id=member.department_id,
                role_in_team=replacement_role_in_team or member.role_in_team,
                start_date=utc_now(),
                is_active=True
            )
            db.add(new_member)

        cls._record_domain_event(
            db=db, entity_type="ProjectMember", entity_id=member.id,
            action=f"MEMBER_{action.value}", previous_state="ACTIVE", new_state=action.value,
            actor=actor, payload={"reason": reason, "replacement_student_id": replacement_student_id}, notes=reason
        )

    # ------------------------------------------------------------------
    # Stage 7: Industry / CSR agreement, funding governance, IP consent
    # ------------------------------------------------------------------

    @classmethod
    def transition_agreement(
        cls,
        db: Session,
        collaboration: IndustryCollaboration,
        to_status: AgreementStatus,
        actor: User,
        notes: str,
        conflict_declared: Optional[bool] = None,
        mou_evidence_object_id: Optional[str] = None
    ) -> IndustryCollaboration:
        from_status = collaboration.agreement_status
        if from_status == to_status:
            return collaboration

        allowed_roles = ALLOWED_AGREEMENT_TRANSITIONS.get((from_status, to_status))
        if not allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Illegal agreement transition from '{from_status.value}' to '{to_status.value}'."
            )
        if actor.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Actor role '{actor.role.value}' is not authorized to transition this agreement to '{to_status.value}'."
            )

        collaboration.agreement_status = to_status
        collaboration.status = to_status.value  # keep legacy free-text mirror in sync
        collaboration.reviewed_by_user_id = actor.id
        collaboration.review_notes = notes
        collaboration.updated_at = utc_now()
        collaboration.version = (collaboration.version or 1) + 1

        if to_status == AgreementStatus.CONFLICT_CHECK and conflict_declared is not None:
            collaboration.conflict_declared = conflict_declared
            collaboration.conflict_check_notes = notes
        if to_status == AgreementStatus.CONTRACT_RECORDED:
            collaboration.mou_evidence_object_id = mou_evidence_object_id
        if to_status == AgreementStatus.ACCEPTED:
            collaboration.accepted_at = utc_now()
        if to_status == AgreementStatus.TERMINATED:
            collaboration.terminated_reason = notes

        db.add(ReviewComment(
            project_id=collaboration.project_id,
            entity_type="COLLABORATION",
            entity_id=collaboration.id,
            author_id=actor.id,
            content=notes
        ))

        cls._record_domain_event(
            db=db,
            entity_type="IndustryCollaboration",
            entity_id=collaboration.id,
            action=f"AGREEMENT_{to_status.value}",
            previous_state=from_status.value,
            new_state=to_status.value,
            actor=actor,
            payload={"notes": notes, "conflict_declared": conflict_declared},
            notes=notes
        )
        return collaboration

    @classmethod
    def apply_funding_action(
        cls,
        db: Session,
        funding: FundingRecord,
        action: str,
        actor: User,
        notes: Optional[str] = None,
        receipt_evidence_object_id: Optional[str] = None,
        payment_integration_reference: Optional[str] = None
    ) -> FundingRecord:
        """
        Governs the CSR/funding ledger state machine: PENDING -> HELD (approval) ->
        RELEASED (requires utilization evidence and, if milestone-linked, an approved
        milestone) -> REVERSED. Never marks a payment confirmed without the finance
        integration explicitly confirming it.
        """
        action_upper = action.upper()
        from_state = funding.hold_state

        if action_upper == "APPROVE":
            if actor.role not in REVIEWER_ROLES:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only government or university reviewers may approve funding.")
            if from_state != FundingHoldState.PENDING:
                raise HTTPException(status_code=400, detail=f"Funding must be PENDING to approve (current: {from_state.value}).")
            funding.approved_by_user_id = actor.id
            funding.approved_at = utc_now()
            funding.hold_state = FundingHoldState.HELD
            funding.settlement_status = "APPROVED_PENDING_RELEASE"

        elif action_upper == "HOLD":
            if actor.role not in REVIEWER_ROLES:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only government or university reviewers may place a hold.")
            funding.hold_state = FundingHoldState.HELD
            funding.settlement_status = "HELD"

        elif action_upper == "RELEASE":
            if actor.role not in REVIEWER_ROLES:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only government or university reviewers may release funds.")
            if from_state != FundingHoldState.HELD:
                raise HTTPException(status_code=400, detail=f"Funding must be HELD before release (current: {from_state.value}).")
            if funding.milestone_id:
                milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == funding.milestone_id).first()
                if not milestone or milestone.status not in (MilestoneStatus.APPROVED, MilestoneStatus.COMPLETED):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Rejected: The linked milestone condition has not been approved yet. Funds cannot be released."
                    )
            if not receipt_evidence_object_id and not funding.receipt_evidence_object_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rejected: Utilization/receipt evidence is required before release."
                )
            if receipt_evidence_object_id:
                funding.receipt_evidence_object_id = receipt_evidence_object_id

            settlement = finance_integration_service.confirm_settlement(
                funding_record_id=funding.id, amount=funding.amount, currency=funding.currency,
                reference=payment_integration_reference
            )
            funding.hold_state = FundingHoldState.RELEASED
            funding.payment_confirmed = settlement.confirmed
            funding.settlement_status = settlement.status
            funding.payment_integration_reference = payment_integration_reference or funding.payment_integration_reference

        elif action_upper == "REVERSE":
            if actor.role != UserRole.GOVERNMENT_ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only a government administrator may reverse a funding entry.")
            if from_state not in (FundingHoldState.HELD, FundingHoldState.RELEASED):
                raise HTTPException(status_code=400, detail=f"Cannot reverse funding in state '{from_state.value}'.")
            funding.hold_state = FundingHoldState.REVERSED
            funding.payment_confirmed = False
            funding.settlement_status = "REVERSED"

        else:
            raise HTTPException(status_code=400, detail="Action must be one of: APPROVE, HOLD, RELEASE, REVERSE")

        if notes:
            funding.utilization_notes = notes
        funding.updated_at = utc_now()
        funding.version = (funding.version or 1) + 1

        db.add(ReviewComment(
            project_id=funding.project_id,
            entity_type="FUNDING",
            entity_id=funding.id,
            author_id=actor.id,
            content=notes or f"Funding action: {action_upper}"
        ))

        cls._record_domain_event(
            db=db,
            entity_type="FundingRecord",
            entity_id=funding.id,
            action=f"FUNDING_{action_upper}",
            previous_state=from_state.value,
            new_state=funding.hold_state.value,
            actor=actor,
            payload={"notes": notes, "settlement_status": funding.settlement_status, "payment_confirmed": funding.payment_confirmed},
            notes=notes
        )
        return funding

    @classmethod
    def respond_ip_consent(
        cls,
        db: Session,
        consent: IPConsentRecord,
        actor: User,
        decision: str,
        notes: Optional[str] = None
    ) -> IPConsentRecord:
        decision_upper = decision.upper()
        if decision_upper not in {"ACCEPTED", "REJECTED"}:
            raise HTTPException(status_code=400, detail="Consent decision must be 'ACCEPTED' or 'REJECTED'.")
        if consent.party_user_id != actor.id and actor.role != UserRole.GOVERNMENT_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You may only respond to your own IP consent request.")

        consent.status = IPConsentStatus(decision_upper)
        consent.notes = notes
        consent.responded_at = utc_now()

        ip_record = db.query(IPRecord).filter(IPRecord.id == consent.ip_record_id).first()
        if ip_record:
            all_consents = db.query(IPConsentRecord).filter(IPConsentRecord.ip_record_id == ip_record.id).all()
            if decision_upper == "REJECTED":
                ip_record.status = "REJECTED"
            elif all(c.status == IPConsentStatus.ACCEPTED for c in all_consents):
                ip_record.status = "APPROVED"

        cls._record_domain_event(
            db=db,
            entity_type="IPConsentRecord",
            entity_id=consent.id,
            action=f"IP_CONSENT_{decision_upper}",
            previous_state=IPConsentStatus.PENDING.value,
            new_state=decision_upper,
            actor=actor,
            payload={"notes": notes},
            notes=notes
        )
        return consent

    # ------------------------------------------------------------------
    # Stage 8: Evidence-based field verification, metrics, and closure
    # ------------------------------------------------------------------

    @classmethod
    def evaluate_closure_preconditions(cls, db: Session, project_id: int) -> Dict[str, Any]:
        """
        Evaluates the 9 mandatory preconditions for project and challenge closure:
        1. Approved solution proposal
        2. Weighted milestones total 100%
        3. All milestones approved
        4. Deliverable evidence complete for all milestones
        5. Funding obligations settled (no pending tranches)
        6. Field verification approved
        7. Baseline, target, and actual outcome metrics measured & verified
        8. IP and data obligations cleared
        9. Maintenance & handover plan provided
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        preconditions = []
        missing = []

        # 1. Approved Proposal
        proposal = db.query(SolutionProposal).filter(
            SolutionProposal.project_id == project.id,
            SolutionProposal.status == ProposalStatus.APPROVED
        ).first()
        has_proposal = proposal is not None
        preconditions.append({
            "key": "approved_proposal",
            "title": "Approved Solution Proposal",
            "satisfied": has_proposal,
            "details": f"Proposal v{proposal.version} approved" if has_proposal else "No approved solution proposal found"
        })
        if not has_proposal:
            missing.append("approved_proposal")

        # 2. Weighted Milestones Total 100%
        milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project.id).all()
        total_weight = sum((m.weight_pct or 0.0) for m in milestones)
        weights_100 = len(milestones) > 0 and abs(total_weight - 100.0) < 0.01
        preconditions.append({
            "key": "milestones_weight_100",
            "title": "Milestones Total 100% Weight",
            "satisfied": weights_100,
            "details": f"Total milestone weight is {total_weight}% (target 100%)" if milestones else "No milestones defined"
        })
        if not weights_100:
            missing.append("milestones_weight_100")

        # 3. All Milestones Approved / Completed
        unapproved_milestones = [m for m in milestones if m.status not in (MilestoneStatus.APPROVED, MilestoneStatus.COMPLETED)]
        all_milestones_approved = len(milestones) > 0 and len(unapproved_milestones) == 0
        preconditions.append({
            "key": "milestones_approved",
            "title": "All Milestones Approved",
            "satisfied": all_milestones_approved,
            "details": f"All {len(milestones)} milestones approved" if all_milestones_approved else f"{len(unapproved_milestones)} milestones not yet approved"
        })
        if not all_milestones_approved:
            missing.append("milestones_approved")

        # 4. Deliverable Evidence for All Milestones
        milestones_without_evidence = []
        for m in milestones:
            ev = db.query(EvidenceFile).filter(
                EvidenceFile.entity_type == "MILESTONE_DELIVERABLE",
                EvidenceFile.entity_id == m.id,
                EvidenceFile.is_current == True
            ).first()
            if not ev:
                milestones_without_evidence.append(m.id)
        evidence_complete = len(milestones) > 0 and len(milestones_without_evidence) == 0
        preconditions.append({
            "key": "deliverable_evidence",
            "title": "Deliverable Evidence Complete",
            "satisfied": evidence_complete,
            "details": "All milestones have deliverable evidence files" if evidence_complete else f"Milestones missing evidence: {milestones_without_evidence}"
        })
        if not evidence_complete:
            missing.append("deliverable_evidence")

        # 5. Funding Obligations Settled
        pending_funding = db.query(FundingRecord).filter(
            FundingRecord.project_id == project.id,
            FundingRecord.hold_state == FundingHoldState.PENDING
        ).all()
        funding_settled = len(pending_funding) == 0
        preconditions.append({
            "key": "funding_settled",
            "title": "Funding Obligations Settled",
            "satisfied": funding_settled,
            "details": "All funding lines resolved/held" if funding_settled else f"{len(pending_funding)} funding tranches still pending approval"
        })
        if not funding_settled:
            missing.append("funding_settled")

        # 6. Field Verification Approved
        verified_records = db.query(VerificationRecord).filter(
            VerificationRecord.project_id == project.id,
            VerificationRecord.verification_status == "VERIFIED"
        ).all()
        has_field_verification = len(verified_records) > 0
        preconditions.append({
            "key": "field_verification",
            "title": "Field Verification Approved",
            "satisfied": has_field_verification,
            "details": f"{len(verified_records)} field verification records verified" if has_field_verification else "No approved field verification record found"
        })
        if not has_field_verification:
            missing.append("field_verification")

        # 7. Baseline/Target/Actual Outcome Metrics Recorded & Verified
        outcome_metrics = db.query(OutcomeMetric).filter(OutcomeMetric.project_id == project.id).all()
        metrics_complete = len(outcome_metrics) > 0 and all(
            m.actual_value is not None and m.verification_status in ("VERIFIED", "INDEPENDENTLY_VERIFIED", "MEASURED")
            for m in outcome_metrics
        )
        preconditions.append({
            "key": "outcome_metrics",
            "title": "Baseline, Target & Actual Outcome Metrics",
            "satisfied": metrics_complete,
            "details": f"{len(outcome_metrics)} outcome metrics measured & verified" if metrics_complete else (
                "No outcome metrics recorded" if not outcome_metrics else "Some metrics missing actual values or verification"
            )
        })
        if not metrics_complete:
            missing.append("outcome_metrics")

        # 8. IP and Data Obligations Cleared
        ip_records = db.query(IPRecord).filter(IPRecord.project_id == project.id).all()
        ip_cleared = True
        ip_details = "No IP records registered or all IP consents accepted"
        if ip_records:
            for ip_rec in ip_records:
                consents = db.query(IPConsentRecord).filter(IPConsentRecord.ip_record_id == ip_rec.id).all()
                if any(c.status != IPConsentStatus.ACCEPTED for c in consents):
                    ip_cleared = False
                    ip_details = f"IP record '{ip_rec.title}' has pending/rejected consents"
                    break
        preconditions.append({
            "key": "ip_obligations",
            "title": "IP and Data Obligations Cleared",
            "satisfied": ip_cleared,
            "details": ip_details
        })
        if not ip_cleared:
            missing.append("ip_obligations")

        # 9. Maintenance & Handover Plan
        has_handover_plan = bool(proposal and proposal.maintenance_plan and len(proposal.maintenance_plan.strip()) >= 10)
        preconditions.append({
            "key": "maintenance_handover_plan",
            "title": "Risk & Maintenance Handover Plan",
            "satisfied": has_handover_plan,
            "details": "Maintenance plan documented in proposal" if has_handover_plan else "Maintenance and handover plan required at closure"
        })
        if not has_handover_plan:
            missing.append("maintenance_handover_plan")

        ready = len(missing) == 0
        return {
            "project_id": project.id,
            "challenge_id": project.challenge_id,
            "ready_for_closure": ready,
            "preconditions": preconditions,
            "missing_preconditions": missing
        }

    @classmethod
    def close_project_and_challenge(
        cls,
        db: Session,
        project_id: int,
        actor: User,
        payload: Dict[str, Any],
        expected_version: Optional[int] = None
    ) -> ProjectClosureRecord:
        """
        Accountable Project and Challenge closure gate.
        Validates all 9 preconditions, ensures conflict-free authorized actor, creates
        an immutable ProjectClosureRecord, and transitions Project and Challenge status.
        """
        if actor.role not in {UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only government officers or administrators are authorized to execute accountable project closure."
            )

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        challenge = db.query(Challenge).filter(Challenge.id == project.challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Associated challenge not found")

        # Evaluate preconditions
        evaluation = cls.evaluate_closure_preconditions(db, project.id)

        # Allow maintenance_handover_plan from closure payload to satisfy precondition if missing in proposal
        maintenance_plan = payload.get("maintenance_handover_plan", "").strip()
        if "maintenance_handover_plan" in evaluation["missing_preconditions"] and len(maintenance_plan) >= 20:
            evaluation["missing_preconditions"].remove("maintenance_handover_plan")
            for p in evaluation["preconditions"]:
                if p["key"] == "maintenance_handover_plan":
                    p["satisfied"] = True
                    p["details"] = "Supplied in closure decision"
            if len(evaluation["missing_preconditions"]) == 0:
                evaluation["ready_for_closure"] = True

        if not evaluation["ready_for_closure"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Project cannot be closed: One or more closure preconditions are not satisfied.",
                    "missing_preconditions": evaluation["missing_preconditions"],
                    "evaluation": evaluation
                }
            )

        closure_decision = payload.get("decision", "APPROVED_CLOSED")
        closure_remarks = payload.get("closure_remarks", "Project successfully closed following verified preconditions.")

        # Create immutable ProjectClosureRecord
        closure_record = ProjectClosureRecord(
            project_id=project.id,
            challenge_id=project.challenge_id,
            closed_by_user_id=actor.id,
            closure_decision=closure_decision,
            preconditions_snapshot_json=json.dumps(evaluation),
            ip_cleared=payload.get("ip_cleared", True),
            ip_handover_details=payload.get("ip_handover_details"),
            maintenance_handover_plan=maintenance_plan,
            handover_recipient_org=payload.get("handover_recipient_org", "Government of Jharkhand"),
            closure_remarks=closure_remarks,
            closed_at=utc_now()
        )
        db.add(closure_record)

        # 1. Transition Project to Completed stage
        cls.transition_project(
            db=db,
            project=project,
            to_stage="Completed",
            actor=actor,
            expected_version=expected_version,
            remarks=closure_remarks,
            payload={"closure_decision": closure_decision, "closure_record_id": closure_record.id}
        )

        # 2. Transition Challenge to RESOLVED if needed, then to CLOSED via state machine
        if challenge.status != ChallengeStatus.CLOSED:
            if challenge.status not in (ChallengeStatus.RESOLVED, ChallengeStatus.IMPACT_AUDITED):
                cls.transition_challenge(
                    db=db,
                    challenge=challenge,
                    to_status=ChallengeStatus.RESOLVED,
                    actor=actor,
                    remarks=f"Challenge resolved by project #{project.id} completion",
                    payload={"project_id": project.id}
                )
            cls.transition_challenge(
                db=db,
                challenge=challenge,
                to_status=ChallengeStatus.CLOSED,
                actor=actor,
                remarks=closure_remarks,
                payload={"closure_record_id": closure_record.id, "project_id": project.id}
            )

        db.commit()
        db.refresh(closure_record)
        return closure_record

    @classmethod
    def reopen_or_escalate_challenge(
        cls,
        db: Session,
        challenge_id: int,
        actor: User,
        reason: str,
        expected_version: Optional[int] = None
    ) -> Challenge:
        """
        Escalates a regression or unresolved issue post-closure, transitioning
        Challenge back to REOPENED and Project back to 'Post-Deployment Remediation'.
        """
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")

        # Allow citizen submitter, government, or community org to escalate regression
        if actor.role in {UserRole.GOVERNMENT_OFFICER, UserRole.GOVERNMENT_ADMIN}:
            verify_challenge_jurisdiction(challenge, actor, db, action="reopen")
        elif actor.role == UserRole.CITIZEN:
            is_owner = (challenge.submitted_by_user_id == actor.id) or (challenge.citizen and challenge.citizen.user_id == actor.id)
            if not is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Citizens may only report regression or reopen challenges they originally submitted."
                )

        # Reopen challenge
        updated_challenge = cls.transition_challenge(
            db=db,
            challenge=challenge,
            to_status=ChallengeStatus.REOPENED,
            actor=actor,
            expected_version=expected_version,
            remarks=f"Post-closure regression reported: {reason}",
            payload={"regression_reason": reason}
        )

        # Also find active or completed project linked to challenge and update stage to 'Post-Deployment Remediation'
        project = db.query(Project).filter(Project.challenge_id == challenge.id).order_by(Project.id.desc()).first()
        if project:
            cls.transition_project(
                db=db,
                project=project,
                to_stage="Post-Deployment Remediation",
                actor=actor,
                remarks=f"Reopened due to post-deployment issue: {reason}",
                payload={"challenge_id": challenge.id, "reason": reason}
            )

        db.commit()
        db.refresh(updated_challenge)
        return updated_challenge

