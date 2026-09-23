import json
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.models.models import (
    CitizenFeedback, Challenge, Citizen, User, UserRole, Project,
    University, IndustryPartner, ChallengeStatus, District, AuditLog,
    OutcomeMetric, ChallengeLocation, ProjectClosureRecord, utc_now
)
from backend.app.schemas.schemas import (
    CitizenFeedbackCreate, CitizenFeedbackOut, CitizenFeedbackModerationRequest,
    CitizenFeedbackAppealRequest, OutcomeMetricCreate, OutcomeMetricUpdate,
    OutcomeMetricVerifyRequest, OutcomeMetricOut
)
from backend.app.routers.deps import (
    get_current_user, require_permission, verify_citizen_feedback_eligibility,
    verify_project_membership, verify_challenge_jurisdiction
)
from backend.app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/impact", tags=["Impact Measurement & Citizen Feedback"])

# ------------------------------------------------------------------
# Citizen Feedback & Beneficiary Validation
# ------------------------------------------------------------------

@router.post("/feedback", response_model=CitizenFeedbackOut, status_code=status.HTTP_201_CREATED)
def submit_citizen_feedback(
    payload: CitizenFeedbackCreate,
    current_user: User = Depends(require_permission("challenge.feedback")),
    db: Session = Depends(get_db)
):
    challenge = db.query(Challenge).filter(Challenge.id == payload.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Stage 8: Validate citizen/beneficiary eligibility (blocks arbitrary unrelated citizens or officers)
    verify_citizen_feedback_eligibility(challenge, current_user, db, payload.invitation_token)

    citizen = db.query(Citizen).filter(Citizen.user_id == current_user.id).first()
    if not citizen:
        user_district = current_user.district_name or (challenge.location.district_name if challenge.location else "Ranchi")
        citizen = Citizen(user_id=current_user.id, district_name=user_district)
        db.add(citizen)
        db.commit()
        db.refresh(citizen)

    target_version = payload.challenge_version or (challenge.version or 1)

    # Stage 8: Prevent duplicate responses for the same challenge version
    existing = db.query(CitizenFeedback).filter(
        CitizenFeedback.challenge_id == payload.challenge_id,
        (CitizenFeedback.user_id == current_user.id) | (CitizenFeedback.citizen_id == citizen.id),
        CitizenFeedback.challenge_version == target_version
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflict: Citizen feedback has already been submitted for challenge version {target_version}."
        )

    feedback = CitizenFeedback(
        challenge_id=payload.challenge_id,
        citizen_id=citizen.id,
        user_id=current_user.id,
        challenge_version=target_version,
        rating=payload.rating,
        is_issue_resolved=payload.is_issue_resolved,
        satisfaction_score=payload.satisfaction_score,
        comments=payload.comments,
        original_comments=payload.comments,
        evidence_photo_url=payload.evidence_photo_url,
        beneficiary_verification_type=payload.beneficiary_verification_type or "ORIGINAL_REPORTER",
        invitation_token=payload.invitation_token,
        is_public=payload.is_public if payload.is_public is not None else True,
        accessibility_needs=payload.accessibility_needs,
        language=payload.language or "en",
        moderation_status="APPROVED",
        appeal_status="NONE",
        submitted_at=utc_now()
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.role.value,
        action="CITIZEN_FEEDBACK_SUBMITTED",
        entity_name="CitizenFeedback",
        entity_id=feedback.id,
        new_state=f"Rating: {payload.rating}/5, Resolved: {payload.is_issue_resolved}",
        reason=f"Citizen validation feedback on Challenge #{challenge.id} (v{target_version})"
    ))
    db.commit()

    return feedback


@router.get("/feedback/challenge/{challenge_id}", response_model=List[CitizenFeedbackOut])
def get_challenge_feedback(
    challenge_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(CitizenFeedback).filter(CitizenFeedback.challenge_id == challenge_id)
    # If not government officer/admin, only show public, approved feedback
    if not current_user or current_user.role not in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER):
        query = query.filter(CitizenFeedback.is_public == True, CitizenFeedback.moderation_status == "APPROVED")
    return query.order_by(CitizenFeedback.submitted_at.desc()).all()


@router.post("/feedback/{feedback_id}/moderate", response_model=CitizenFeedbackOut)
def moderate_citizen_feedback(
    feedback_id: int,
    payload: CitizenFeedbackModerationRequest,
    current_user: User = Depends(require_permission("feedback.moderate")),
    db: Session = Depends(get_db)
):
    feedback = db.query(CitizenFeedback).filter(CitizenFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback record not found")

    old_status = feedback.moderation_status
    feedback.moderation_status = payload.moderation_status
    feedback.moderation_reason = payload.moderation_reason
    feedback.moderated_by_user_id = current_user.id

    if payload.moderation_status == "REDACTED" and payload.redacted_comments:
        feedback.comments = payload.redacted_comments
    elif payload.moderation_status == "FLAGGED":
        feedback.is_public = False

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.role.value,
        action="FEEDBACK_MODERATED",
        entity_name="CitizenFeedback",
        entity_id=feedback.id,
        old_state=old_status,
        new_state=payload.moderation_status,
        reason=payload.moderation_reason
    ))
    db.commit()
    db.refresh(feedback)
    return feedback


@router.post("/feedback/{feedback_id}/appeal", response_model=CitizenFeedbackOut)
def appeal_feedback_moderation(
    feedback_id: int,
    payload: CitizenFeedbackAppealRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feedback = db.query(CitizenFeedback).filter(CitizenFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback record not found")

    citizen = db.query(Citizen).filter(Citizen.user_id == current_user.id).first()
    is_owner = (feedback.user_id == current_user.id) or (citizen and feedback.citizen_id == citizen.id)
    if not is_owner and current_user.role != UserRole.GOVERNMENT_ADMIN:
        raise HTTPException(status_code=403, detail="Forbidden: You can only appeal moderation on your own feedback.")

    feedback.appeal_status = "PENDING"
    feedback.appeal_reason = payload.appeal_reason

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.role.value,
        action="FEEDBACK_APPEAL_SUBMITTED",
        entity_name="CitizenFeedback",
        entity_id=feedback.id,
        new_state="APPEAL_PENDING",
        reason=payload.appeal_reason
    ))
    db.commit()
    db.refresh(feedback)
    return feedback


# ------------------------------------------------------------------
# Structured Outcome Metrics (Stage 8)
# ------------------------------------------------------------------

@router.post("/projects/{project_id}/outcome-metrics", response_model=OutcomeMetricOut, status_code=status.HTTP_201_CREATED)
def create_outcome_metric(
    project_id: int,
    payload: OutcomeMetricCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    verify_project_membership(project_id, current_user, db)

    metric = OutcomeMetric(
        project_id=project.id,
        challenge_id=project.challenge_id,
        metric_name=payload.metric_name,
        metric_definition=payload.metric_definition,
        metric_type=payload.metric_type,
        unit_of_measure=payload.unit_of_measure,
        baseline_value=payload.baseline_value,
        baseline_date=payload.baseline_date or utc_now(),
        baseline_source=payload.baseline_source,
        target_value=payload.target_value,
        target_date=payload.target_date,
        collection_method=payload.collection_method,
        sample_size=payload.sample_size,
        uncertainty_margin=payload.uncertainty_margin,
        responsible_org_name=payload.responsible_org_name or (project.university.institution_name if project.university else None),
        responsible_user_id=current_user.id,
        district_name=payload.district_name or (project.challenge.location.district_name if project.challenge and project.challenge.location else None),
        block_name=payload.block_name or (project.challenge.location.block_name if project.challenge and project.challenge.location else None),
        verification_status="REPORTED"
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.get("/projects/{project_id}/outcome-metrics", response_model=List[OutcomeMetricOut])
def get_project_outcome_metrics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id, current_user, db)
    return db.query(OutcomeMetric).filter(
        OutcomeMetric.project_id == project_id
    ).order_by(OutcomeMetric.created_at.asc()).all()


@router.put("/projects/{project_id}/outcome-metrics/{metric_id}", response_model=OutcomeMetricOut)
def update_outcome_metric(
    project_id: int,
    metric_id: int,
    payload: OutcomeMetricUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id, current_user, db)
    metric = db.query(OutcomeMetric).filter(
        OutcomeMetric.id == metric_id,
        OutcomeMetric.project_id == project_id
    ).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Outcome metric not found")

    if payload.actual_value is not None:
        metric.actual_value = payload.actual_value
    if payload.actual_date is not None:
        metric.actual_date = payload.actual_date
    elif payload.actual_value and not metric.actual_date:
        metric.actual_date = utc_now()
    if payload.actual_source is not None:
        metric.actual_source = payload.actual_source
    if payload.collection_method is not None:
        metric.collection_method = payload.collection_method
    if payload.sample_size is not None:
        metric.sample_size = payload.sample_size
    if payload.uncertainty_margin is not None:
        metric.uncertainty_margin = payload.uncertainty_margin
    if payload.evidence_references is not None:
        ev_refs = payload.evidence_references
        metric.evidence_references = json.dumps(ev_refs) if isinstance(ev_refs, list) else ev_refs
    if payload.verification_status is not None:
        metric.verification_status = payload.verification_status

    db.commit()
    db.refresh(metric)
    return metric


@router.post("/projects/{project_id}/outcome-metrics/{metric_id}/verify", response_model=OutcomeMetricOut)
def verify_outcome_metric(
    project_id: int,
    metric_id: int,
    payload: OutcomeMetricVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only government officers, admins, or independent research labs/hubs may verify metrics
    if current_user.role not in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.RESEARCH_LAB, UserRole.INNOVATION_HUB):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only authorized government officers or independent evaluators can verify outcome metrics."
        )

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Prevent conflict of interest: project team cannot self-verify metrics
    if project.faculty_mentor and project.faculty_mentor.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="Conflict of interest: Project faculty mentor cannot verify outcome metrics.")

    metric = db.query(OutcomeMetric).filter(
        OutcomeMetric.id == metric_id,
        OutcomeMetric.project_id == project_id
    ).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Outcome metric not found")

    metric.verification_status = payload.verification_status
    metric.verified_by_user_id = current_user.id
    metric.verified_at = utc_now()

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.role.value,
        action="OUTCOME_METRIC_VERIFIED",
        entity_name="OutcomeMetric",
        entity_id=metric.id,
        new_state=payload.verification_status,
        reason=payload.verification_notes or f"Metric {metric.metric_name} verified"
    ))

    db.commit()
    db.refresh(metric)
    return metric


# ------------------------------------------------------------------
# Post-Deployment Regression Escalation
# ------------------------------------------------------------------

@router.post("/challenges/{challenge_id}/escalate-regression")
def escalate_challenge_regression(
    challenge_id: int,
    reason: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reopens a resolved or closed challenge when post-deployment regression occurs
    or when citizen validation reports that the underlying issue remains unresolved.
    """
    reopened = WorkflowService.reopen_or_escalate_challenge(
        db=db,
        challenge_id=challenge_id,
        actor=current_user,
        reason=reason
    )
    return {
        "status": "ESCALATED",
        "challenge_id": reopened.id,
        "challenge_status": reopened.status.value,
        "message": f"Challenge #{reopened.id} has been reopened for remediation."
    }


# ------------------------------------------------------------------
# Real-Time Data-Driven Telemetry
# ------------------------------------------------------------------

@router.get("/metrics")
def get_data_driven_impact_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Computes real-time, data-driven impact metrics from actual DB records.
    Distinguishes outcome verification tiers (reported, estimated, measured, independently verified).
    Zero hardcoded values (no 'or 4.5' rating, no static 'districts_covered: 24').
    """
    total_challenges = db.query(func.count(Challenge.id)).scalar() or 0
    resolved_challenges = db.query(func.count(Challenge.id)).filter(
        Challenge.status.in_([ChallengeStatus.RESOLVED, ChallengeStatus.CLOSED])
    ).scalar() or 0
    active_projects = db.query(func.count(Project.id)).scalar() or 0
    total_universities = db.query(func.count(University.id)).scalar() or 0
    total_industry = db.query(func.count(IndustryPartner.id)).scalar() or 0

    # Aggregated population positively impacted from verified resolved challenges
    affected_pop_sum = db.query(func.sum(Challenge.affected_population)).filter(
        Challenge.status.in_([ChallengeStatus.RESOLVED, ChallengeStatus.CLOSED])
    ).scalar() or 0

    # Average citizen satisfaction from real approved feedback (returns 0.0 if no feedback yet)
    raw_avg = db.query(func.avg(CitizenFeedback.rating)).filter(
        CitizenFeedback.moderation_status == "APPROVED"
    ).scalar()
    avg_rating = round(float(raw_avg), 1) if raw_avg is not None else 0.0

    # Dynamic count of distinct districts with registered challenges
    districts_count = db.query(func.count(func.distinct(ChallengeLocation.district_name))).scalar() or 0

    # Verification tier breakdown of outcome metrics
    tiers = {
        "reported": db.query(func.count(OutcomeMetric.id)).filter(OutcomeMetric.verification_status == "REPORTED").scalar() or 0,
        "estimated": db.query(func.count(OutcomeMetric.id)).filter(OutcomeMetric.verification_status == "ESTIMATED").scalar() or 0,
        "measured": db.query(func.count(OutcomeMetric.id)).filter(OutcomeMetric.verification_status == "MEASURED").scalar() or 0,
        "independently_verified": db.query(func.count(OutcomeMetric.id)).filter(OutcomeMetric.verification_status == "INDEPENDENTLY_VERIFIED").scalar() or 0,
    }

    unresolved_feedback_count = db.query(func.count(CitizenFeedback.id)).filter(
        CitizenFeedback.is_issue_resolved == False
    ).scalar() or 0

    return {
        "citizens_benefited": int(affected_pop_sum),
        "total_challenges": int(total_challenges),
        "total_challenges_reported": int(total_challenges),
        "challenges_resolved": int(resolved_challenges),
        "resolution_rate_pct": round((resolved_challenges / total_challenges * 100) if total_challenges > 0 else 0.0, 1),
        "active_academic_projects": int(active_projects),
        "participating_universities": int(total_universities),
        "industry_partners": int(total_industry),
        "average_citizen_satisfaction": avg_rating,
        "citizen_satisfaction_avg": avg_rating,
        "districts_covered": int(districts_count),
        "outcome_metrics_breakdown": tiers,
        "total_outcome_metrics": sum(tiers.values()),
        "unresolved_citizen_reports": int(unresolved_feedback_count)
    }

