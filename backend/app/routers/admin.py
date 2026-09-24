import csv
import io
import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.models.models import (
    Challenge, Project, University, IndustryPartner, Student,
    ChallengeLocation, District, ImpactMetrics, ChallengeStatus,
    ChallengePriority, StatusHistory, User, AuditLog, UserRole,
    DomainAuditEvent, AIJob, AIPriorityWeightConfig, AIModelGovernance,
    ExportJob
)
from backend.app.schemas.schemas import (
    EscalateChallengeRequest, ValidateChallengeRequest,
    DomainAuditEventOut, AuditChainVerificationOut,
    AIJobOut, AIPriorityConfigCreate, AIPriorityConfigOut,
    KPIMetadata, KPIDrillDownResponseOut, DistrictDrillDownOut, BlockDrillDownOut,
    VerifiableAdminDashboardOut, ExportJobCreate, ExportJobOut
)
from backend.app.services.workflow_service import WorkflowService
from backend.app.services.ai.queue_service import queue_service
from backend.app.services.ai.evaluation_service import evaluation_service
from backend.app.services.analytics_service import analytics_service
from backend.app.routers.deps import (
    get_current_user, require_permission,
    verify_challenge_jurisdiction, check_jurisdiction
)

router = APIRouter(prefix="/admin", tags=["Government Admin"])


def _apply_challenge_jurisdiction_filter(query, user: User):
    """Filters a Challenge query according to government jurisdiction scoping."""
    if user.role == UserRole.GOVERNMENT_ADMIN and (not user.admin_tier or user.admin_tier.upper() == "STATE"):
        return query

    tier = (user.admin_tier or "STATE").upper()
    if tier == "STATE":
        return query

    user_dist = (user.district_name or user.jurisdiction_name or "").strip()
    user_block = (user.block_name or "").strip()
    user_panch = (user.panchayat_name or "").strip()

    query = query.join(ChallengeLocation, Challenge.id == ChallengeLocation.challenge_id)
    if tier == "DISTRICT" and user_dist:
        return query.filter(ChallengeLocation.district_name.ilike(f"%{user_dist}%"))
    elif tier == "BLOCK" and user_block:
        if user_dist:
            query = query.filter(ChallengeLocation.district_name.ilike(f"%{user_dist}%"))
        return query.filter(ChallengeLocation.block_name.ilike(f"%{user_block}%"))
    elif tier == "PANCHAYAT" and user_panch:
        if user_dist:
            query = query.filter(ChallengeLocation.district_name.ilike(f"%{user_dist}%"))
        return query.filter(ChallengeLocation.village_or_city.ilike(f"%{user_panch}%"))

    return query


@router.get("/dashboard", response_model=VerifiableAdminDashboardOut)
def get_admin_dashboard(
    current_user: User = Depends(require_permission("analytics.view")),
    db: Session = Depends(get_db)
):
    return analytics_service.get_dashboard_summary(db=db, viewer=current_user)


@router.get("/drill-down/districts", response_model=List[DistrictDrillDownOut])
def get_districts_drill_down(
    current_user: User = Depends(require_permission("analytics.view")),
    db: Session = Depends(get_db)
):
    """Canonical district drill-down with live aggregated metrics."""
    return analytics_service.get_districts_drill_down(db=db, viewer=current_user)


@router.get("/drill-down/districts/{district_name}/blocks", response_model=List[BlockDrillDownOut])
def get_blocks_drill_down(
    district_name: str,
    current_user: User = Depends(require_permission("analytics.view")),
    db: Session = Depends(get_db)
):
    """Block-level administrative drill-down for a selected district."""
    return analytics_service.get_blocks_drill_down(db=db, district_name=district_name, viewer=current_user)


@router.get("/analytics/drill-down", response_model=KPIDrillDownResponseOut)
def get_kpi_drill_down(
    metric: str = "submissions",
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_permission("analytics.view")),
    db: Session = Depends(get_db)
):
    """
    'Why this number' source record reconciliation endpoint.
    Retrieves the raw database entities contributing to a given KPI with privacy masking.
    """
    return analytics_service.get_kpi_source_records(
        db=db, metric_key=metric, viewer=current_user, limit=limit, offset=offset
    )


@router.get("/jharkhand-map")
def get_jharkhand_map_data(
    current_user: User = Depends(require_permission("analytics.view")),
    db: Session = Depends(get_db)
):
    districts = db.query(District).all()
    map_data = []

    user_tier = (current_user.admin_tier or "STATE").upper()
    user_dist = (current_user.district_name or current_user.jurisdiction_name or "").strip().lower()

    for d in districts:
        # If user has district jurisdiction, skip non-matching districts unless statewide
        if user_tier != "STATE" and current_user.role != UserRole.GOVERNMENT_ADMIN:
            if user_dist and user_dist not in d.name.lower() and d.name.lower() not in user_dist:
                continue

        count = db.query(ChallengeLocation).filter(ChallengeLocation.district_name.ilike(d.name)).count()
        challenges = db.query(Challenge).join(ChallengeLocation).filter(ChallengeLocation.district_name.ilike(d.name)).all()
        map_data.append({
            "id": d.id,
            "district_name": d.name,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "total_population": d.total_population,
            "rural_population_pct": d.rural_population_pct,
            "challenge_count": count,
            "challenges": [
                {
                    "id": c.id,
                    "title": c.title,
                    "category": c.category,
                    "priority": c.priority.value,
                    "status": c.status.value
                } for c in challenges[:5]
            ]
        })
    return map_data


@router.get("/analytics")
def get_admin_analytics(
    current_user: User = Depends(require_permission("analytics.view")),
    db: Session = Depends(get_db)
):
    return analytics_service.get_analytics_breakdown(db=db, viewer=current_user)


@router.get("/impact")
def get_impact_metrics(
    current_user: User = Depends(require_permission("analytics.view")),
    db: Session = Depends(get_db)
):
    """
    Manually-tracked impact metrics plus the live innovation outcomes (patents,
    startups, technology transfers, prototypes, pilots) computed by
    AnalyticsService — never hardcoded seed constants.
    """
    metrics = db.query(ImpactMetrics).all()
    out = [
        {"name": m.metric_name, "value": m.metric_value, "category": m.category}
        for m in metrics
    ]

    live = analytics_service.get_dashboard_summary(db=db, viewer=current_user)
    live_kpi_keys = [
        "patents_filed", "startups_incubated", "technology_transfers_completed",
        "prototypes_developed", "pilots_deployed"
    ]
    for key in live_kpi_keys:
        kpi = live["kpis"].get(key)
        if kpi:
            out.append({"name": kpi["display_title"], "value": kpi["value"], "category": "Innovation (Live)"})

    return {"metrics": out}


@router.post("/challenges/{challenge_id}/validate")
def validate_challenge(
    challenge_id: int,
    payload: Optional[ValidateChallengeRequest] = None,
    current_user: User = Depends(require_permission("challenge.validate")),
    db: Session = Depends(get_db)
):
    remarks = payload.remarks if payload else None
    expected_version = payload.expected_version if payload else None
    assigned_tier = payload.assigned_tier if payload else None

    ch = WorkflowService.validate_challenge(
        db=db,
        challenge_id=challenge_id,
        actor=current_user,
        expected_version=expected_version,
        remarks=remarks,
        assigned_tier=assigned_tier
    )
    db.commit()
    return {"status": "success", "message": "Challenge officially validated", "challenge_status": ch.status.value}


@router.post("/challenges/{challenge_id}/escalate")
def escalate_challenge(
    challenge_id: int,
    payload: EscalateChallengeRequest,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    ch = WorkflowService.escalate_tier(
        db=db,
        challenge_id=challenge_id,
        target_tier=payload.target_tier,
        remarks=payload.remarks,
        actor=current_user,
        expected_version=payload.expected_version
    )
    db.commit()
    return {
        "status": "success",
        "message": f"Challenge successfully escalated from {payload.target_tier} level!",
        "current_tier": ch.current_tier,
        "escalation_level": ch.escalation_level
    }


@router.get("/audit-events", response_model=List[DomainAuditEventOut])
def get_audit_events(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    action: Optional[str] = None,
    actor_id: Optional[int] = None,
    limit: int = 100,
    current_user: User = Depends(require_permission("audit.read")),
    db: Session = Depends(get_db)
):
    query = db.query(DomainAuditEvent)
    if entity_type:
        query = query.filter(DomainAuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(DomainAuditEvent.entity_id == entity_id)
    if action:
        query = query.filter(DomainAuditEvent.action == action)
    if actor_id:
        query = query.filter(DomainAuditEvent.actor_id == actor_id)

    events = query.order_by(DomainAuditEvent.sequence_number.desc()).limit(limit).all()
    return events


@router.get("/audit-events/verify", response_model=AuditChainVerificationOut)
def verify_audit_ledger(
    current_user: User = Depends(require_permission("audit.read")),
    db: Session = Depends(get_db)
):
    result = WorkflowService.verify_audit_chain(db)
    return AuditChainVerificationOut(**result)


@router.get("/reports/csv")
def export_csv_report(
    current_user: User = Depends(require_permission("export.create")),
    db: Session = Depends(get_db)
):
    """Immediate bounded CSV report with privacy-redacted coordinates (max 5,000 rows)."""
    payload = ExportJobCreate(export_type="CHALLENGES", export_format="CSV")
    job = analytics_service.create_and_process_export(db=db, user=current_user, payload=payload, max_rows=5000)
    if job.file_path and os.path.exists(job.file_path):
        with open(job.file_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "Error generating report"

    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jharkhand_sih_challenges_report.csv"}
    )


# ==========================================
# STAGE 10: Bounded Asynchronous Export Jobs
# ==========================================

@router.post("/exports", response_model=ExportJobOut, status_code=status.HTTP_201_CREATED)
def create_export_job(
    payload: ExportJobCreate,
    current_user: User = Depends(require_permission("export.create")),
    db: Session = Depends(get_db)
):
    """Creates and executes a bounded asynchronous export job (max 5,000 rows per batch)."""
    job = analytics_service.create_and_process_export(db=db, user=current_user, payload=payload, max_rows=5000)
    return job


@router.get("/exports", response_model=List[ExportJobOut])
def list_export_jobs(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(require_permission("export.create")),
    db: Session = Depends(get_db)
):
    """Lists export requests initiated by the user or jurisdiction."""
    query = db.query(ExportJob)
    if current_user.role != UserRole.GOVERNMENT_ADMIN:
        query = query.filter(ExportJob.user_id == current_user.id)
    return query.order_by(ExportJob.id.desc()).offset(offset).limit(limit).all()


@router.get("/exports/{job_id}", response_model=ExportJobOut)
def get_export_job(
    job_id: int,
    current_user: User = Depends(require_permission("export.create")),
    db: Session = Depends(get_db)
):
    """Retrieves metadata and generation status of an export job."""
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    if current_user.role != UserRole.GOVERNMENT_ADMIN and job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to inspect this export job")
    return job


@router.get("/exports/{job_id}/download")
def download_export_file(
    job_id: int,
    current_user: User = Depends(require_permission("export.create")),
    db: Session = Depends(get_db)
):
    """Streams the generated export file with audit logging."""
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    if current_user.role != UserRole.GOVERNMENT_ADMIN and job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to download this export")
    if job.status != "COMPLETED" or not job.file_path or not os.path.exists(job.file_path):
        raise HTTPException(status_code=400, detail="Export file is not available or job failed")

    filename = os.path.basename(job.file_path)
    return FileResponse(
        path=job.file_path,
        filename=filename,
        media_type="text/csv"
    )


@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_permission("audit.read")),
    db: Session = Depends(get_db)
):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    return logs


# ==========================================
# STAGE 5: AI Operations & Governance APIs
# ==========================================

@router.get("/ai/jobs", response_model=List[AIJobOut])
def get_ai_jobs(
    limit: int = 50,
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_permission("analytics.view")),
    db: Session = Depends(get_db)
):
    query = db.query(AIJob)
    if status_filter:
        query = query.filter(AIJob.status == status_filter)
    jobs = query.order_by(AIJob.id.desc()).limit(limit).all()
    return jobs

@router.post("/ai/jobs/{job_id}/retry", response_model=AIJobOut)
def retry_ai_job(
    job_id: int,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    try:
        job = queue_service.retry_job(db, job_id=job_id)
        # Process immediately
        queue_service.process_job(db, job)
        db.refresh(job)
        return job
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/ai/jobs/process")
def process_pending_ai_jobs(
    limit: int = 10,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    processed = queue_service.process_pending_jobs(db, limit=limit)
    return {"message": f"Successfully processed {processed} pending AI jobs", "processed_count": processed}

@router.get("/ai/priority-config", response_model=List[AIPriorityConfigOut])
def get_priority_configs(
    current_user: User = Depends(require_permission("analytics.view")),
    db: Session = Depends(get_db)
):
    return db.query(AIPriorityWeightConfig).order_by(AIPriorityWeightConfig.id.desc()).all()

@router.post("/ai/priority-config", response_model=AIPriorityConfigOut)
def create_priority_config(
    payload: AIPriorityConfigCreate,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    import json
    # Deactivate existing active configurations
    db.query(AIPriorityWeightConfig).filter(AIPriorityWeightConfig.is_active == True).update({"is_active": False})

    new_cfg = AIPriorityWeightConfig(
        config_version=payload.config_version,
        weights_json=json.dumps(payload.weights),
        description=payload.description,
        is_active=True,
        created_by_user_id=current_user.id
    )
    db.add(new_cfg)
    db.commit()
    db.refresh(new_cfg)
    return new_cfg

@router.get("/ai/evaluate")
def run_ai_benchmark(
    current_user: User = Depends(require_permission("analytics.view")),
    db: Session = Depends(get_db)
):
    metrics = evaluation_service.run_benchmark(db=db)
    return metrics

@router.get("/ai/drift")
def get_ai_drift_metrics(
    current_user: User = Depends(require_permission("analytics.view")),
    db: Session = Depends(get_db)
):
    drift = evaluation_service.compute_drift_metrics(db=db)
    return drift


