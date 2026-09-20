from typing import List, Optional
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
from backend.app.routers.deps import get_current_user, require_roles, verify_project_membership

router = APIRouter(prefix="/verification", tags=["Deliverable & Field Verification"])


@router.post("/records", response_model=VerificationRecordOut, status_code=status.HTTP_201_CREATED)
def submit_verification_record(
    payload: VerificationRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    milestone = None
    if payload.milestone_id:
        milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == payload.milestone_id).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="Milestone not found")

    evidence_str = payload.evidence_urls
    if isinstance(evidence_str, list):
        import json
        evidence_str = json.dumps(evidence_str)

    record = VerificationRecord(
        project_id=payload.project_id,
        milestone_id=payload.milestone_id,
        verification_type=payload.verification_type,
        inspector_name=payload.inspector_name or current_user.full_name,
        inspector_role=payload.inspector_role or current_user.role.value,
        verification_status="SUBMITTED",
        evidence_urls=evidence_str,
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
    current_user: User = Depends(require_roles([UserRole.GOVERNMENT_ADMIN])),
    db: Session = Depends(get_db)
):
    record = db.query(VerificationRecord).filter(VerificationRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Verification record not found")

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

    old_status = record.verification_status
    record.verification_status = norm_decision
    record.verified_at = datetime.now(timezone.utc)
    if actual_remarks:
        record.inspection_notes = f"{record.inspection_notes or ''}\n[Gov Review]: {actual_remarks}".strip()

    # If milestone verified, automatically approve milestone
    if norm_decision == "VERIFIED" and record.milestone:
        record.milestone.status = MilestoneStatus.APPROVED
        record.milestone.completion_percentage = 100.0
        record.milestone.approved_by_faculty = True
        record.milestone.approved_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.role.value,
        action=f"VERIFICATION_{norm_decision}",
        entity_name="VerificationRecord",
        entity_id=record.id,
        old_state=old_status,
        new_state=norm_decision,
        reason=actual_remarks or f"Field audit decision by {current_user.full_name}"
    ))
    db.commit()
    db.refresh(record)
    return record
