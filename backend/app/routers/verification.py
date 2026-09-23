import json
from typing import List, Optional, Union, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import (
    VerificationRecord, Project, ProjectMilestone, User, UserRole, AuditLog, MilestoneStatus
)
from backend.app.schemas.schemas import (
    VerificationRecordCreate, VerificationRecordOut, VerificationReviewRequest
)
from backend.app.routers.deps import (
    get_current_user, require_permission, verify_project_membership,
    verify_challenge_jurisdiction, verify_verification_submission_scope,
    verify_no_verification_conflict
)
from backend.app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/verification", tags=["Deliverable & Field Verification"])


@router.post("/records", response_model=VerificationRecordOut, status_code=status.HTTP_201_CREATED)
def submit_verification_record(
    payload: VerificationRecordCreate,
    current_user: User = Depends(require_permission("verification.submit")),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Stage 8: Validate verifier scope and jurisdiction (blocks students, industry, citizens, and project team)
    verify_verification_submission_scope(project, current_user, db)

    milestone = None
    if payload.milestone_id:
        milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == payload.milestone_id).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="Milestone not found")

    evidence_str = payload.evidence_urls
    if isinstance(evidence_str, list):
        evidence_str = json.dumps(evidence_str)

    checklist_str = payload.checklist_responses
    if isinstance(checklist_str, (dict, list)):
        checklist_str = json.dumps(checklist_str)

    device_str = payload.device_metadata
    if isinstance(device_str, (dict, list)):
        device_str = json.dumps(device_str)

    before_str = payload.before_media_urls
    if isinstance(before_str, list):
        before_str = json.dumps(before_str)

    after_str = payload.after_media_urls
    if isinstance(after_str, list):
        after_str = json.dumps(after_str)

    lab_str = payload.lab_report_references
    if isinstance(lab_str, (dict, list)):
        lab_str = json.dumps(lab_str)

    record = VerificationRecord(
        project_id=payload.project_id,
        milestone_id=payload.milestone_id,
        verification_type=payload.verification_type,
        inspector_name=payload.inspector_name or current_user.full_name,
        inspector_role=payload.inspector_role or current_user.role.value,
        inspector_user_id=current_user.id,
        inspector_organization_id=payload.inspector_organization_id,
        assignment_id=payload.assignment_id,
        verification_status="SUBMITTED",
        evidence_urls=evidence_str,
        checklist_responses=checklist_str,
        visit_timestamp=payload.visit_timestamp or datetime.now(timezone.utc),
        device_metadata=device_str,
        before_media_urls=before_str,
        after_media_urls=after_str,
        lab_report_references=lab_str,
        beneficiary_sample_size=payload.beneficiary_sample_size,
        beneficiary_feedback_summary=payload.beneficiary_feedback_summary,
        geotagged_lat=payload.geotagged_lat,
        geotagged_lng=payload.geotagged_lng,
        inspection_notes=payload.inspection_notes
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.role.value,
        action="VERIFICATION_SUBMITTED",
        entity_name="VerificationRecord",
        entity_id=record.id,
        new_state="SUBMITTED",
        reason=f"{payload.verification_type} submitted for Project #{project.id}"
    ))
    db.commit()

    return record

@router.get("/records/project/{project_id}", response_model=List[VerificationRecordOut])
def get_project_verifications(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id, current_user, db)
    return db.query(VerificationRecord).filter(
        VerificationRecord.project_id == project_id
    ).order_by(VerificationRecord.created_at.desc()).all()

@router.post("/records/{record_id}/review", response_model=VerificationRecordOut)
def review_verification_record(
    record_id: int,
    payload: Optional[VerificationReviewRequest] = None,
    decision: Optional[str] = None,
    remarks: Optional[str] = None,
    current_user: User = Depends(require_permission("verification.review")),
    db: Session = Depends(get_db)
):
    record = db.query(VerificationRecord).filter(VerificationRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Verification record not found")

    # Stage 8: Prevent self-approval, inspector self-review, and project team member conflicts
    verify_no_verification_conflict(record, current_user, db)

    # Enforce jurisdiction
    if record.project and record.project.challenge:
        verify_challenge_jurisdiction(record.project.challenge, current_user, db, action="review_verification")

    actual_decision = None
    actual_remarks = None
    if payload:
        actual_decision = payload.decision or payload.status
        actual_remarks = payload.remarks or payload.review_notes
    if not actual_decision and decision:
        actual_decision = decision
    if not actual_remarks and remarks:
        actual_remarks = remarks

    if not actual_decision:
        raise HTTPException(status_code=400, detail="Decision or status is required")

    norm_decision = actual_decision.upper()
    if norm_decision == "APPROVED":
        norm_decision = "VERIFIED"
    if norm_decision not in ["VERIFIED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Decision must be 'VERIFIED' or 'REJECTED'")

    record.reviewed_by_user_id = current_user.id
    record.review_decision = norm_decision
    record.review_notes = actual_remarks

    WorkflowService.transition_verification(
        db=db,
        verification_record=record,
        decision=norm_decision,
        actor=current_user,
        notes=actual_remarks
    )

    # If milestone verified, automatically approve milestone through workflow service
    if norm_decision == "VERIFIED" and record.milestone:
        WorkflowService.transition_milestone(
            db=db,
            milestone=record.milestone,
            to_status=MilestoneStatus.APPROVED,
            actor=current_user,
            remarks=f"Field verification #{record.id} passed: {actual_remarks or 'Verified'}"
        )

    db.commit()
    db.refresh(record)
    return record


