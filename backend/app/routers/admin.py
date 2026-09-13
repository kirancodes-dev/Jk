import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.models.models import (
    Challenge, Project, University, IndustryPartner, Student,
    ChallengeLocation, District, ImpactMetrics, ChallengeStatus,
    ChallengePriority, StatusHistory, User
)
from backend.app.schemas.schemas import EscalateChallengeRequest
from backend.app.routers.deps import get_current_user

router = APIRouter(prefix="/admin", tags=["Government Admin"])

@router.get("/dashboard")
def get_admin_dashboard(db: Session = Depends(get_db)):
    total_challenges = db.query(Challenge).count()
    submitted = db.query(Challenge).filter(Challenge.status == ChallengeStatus.SUBMITTED).count()
    under_review = db.query(Challenge).filter(Challenge.status.in_([ChallengeStatus.UNDER_REVIEW, ChallengeStatus.AI_ANALYSIS])).count()
    assigned = db.query(Challenge).filter(Challenge.status.in_([ChallengeStatus.VALIDATED, ChallengeStatus.UNIVERSITY_ASSIGNED])).count()
    in_progress = db.query(Challenge).filter(Challenge.status.in_([
        ChallengeStatus.TEAM_FORMED, ChallengeStatus.SOLUTION_PROPOSED,
        ChallengeStatus.APPROVED, ChallengeStatus.PROTOTYPE,
        ChallengeStatus.FIELD_TESTING, ChallengeStatus.DEPLOYMENT,
        ChallengeStatus.IN_PROGRESS
    ])).count()
    resolved = db.query(Challenge).filter(Challenge.status == ChallengeStatus.RESOLVED).count()

    total_universities = db.query(University).count()
    total_industry = db.query(IndustryPartner).count()
    total_students = db.query(Student).count()
    total_projects = db.query(Project).count()

    tier_panchayat = db.query(Challenge).filter(Challenge.current_tier == "PANCHAYAT").count()
    tier_block = db.query(Challenge).filter(Challenge.current_tier == "BLOCK").count()
    tier_district = db.query(Challenge).filter(Challenge.current_tier == "DISTRICT").count()
    tier_state = db.query(Challenge).filter(Challenge.current_tier == "STATE").count()

    return {
        "total_challenges": total_challenges,
        "submitted": submitted,
        "under_review": under_review,
        "assigned": assigned,
        "in_progress": in_progress,
        "resolved": resolved,
        "total_universities": total_universities,
        "total_industry_partners": total_industry,
        "total_students": total_students,
        "total_active_projects": total_projects,
        "tiers": {
            "panchayat": tier_panchayat,
            "block": tier_block,
            "district": tier_district,
            "state": tier_state
        }
    }

@router.get("/jharkhand-map")
def get_jharkhand_map_data(db: Session = Depends(get_db)):
    districts = db.query(District).all()
    map_data = []
    
    for d in districts:
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
def get_admin_analytics(db: Session = Depends(get_db)):
    # By Category
    cats = db.query(Challenge.category, func.count(Challenge.id)).group_by(Challenge.category).all()
    by_category = {cat: cnt for cat, cnt in cats}

    # By Priority
    prios = db.query(Challenge.priority, func.count(Challenge.id)).group_by(Challenge.priority).all()
    by_priority = {p.value: cnt for p, cnt in prios}

    # By District
    dists = db.query(ChallengeLocation.district_name, func.count(ChallengeLocation.id)).group_by(ChallengeLocation.district_name).all()
    by_district = {d: cnt for d, cnt in dists}

    # By Status
    stats = db.query(Challenge.status, func.count(Challenge.id)).group_by(Challenge.status).all()
    by_status = {s.value: cnt for s, cnt in stats}

    return {
        "by_category": by_category,
        "by_priority": by_priority,
        "by_district": by_district,
        "by_status": by_status
    }

@router.get("/impact")
def get_impact_metrics(db: Session = Depends(get_db)):
    metrics = db.query(ImpactMetrics).all()
    return {
        "metrics": [
            {
                "name": m.metric_name,
                "value": m.metric_value,
                "category": m.category
            } for m in metrics
        ]
    }

@router.post("/challenges/{challenge_id}/validate")
def validate_challenge(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
        
    old_status = ch.status.value
    ch.status = ChallengeStatus.VALIDATED
    db.add(StatusHistory(
        challenge_id=ch.id,
        from_status=old_status,
        to_status="VALIDATED",
        updated_by=f"{current_user.full_name} (Govt Admin)",
        remarks="Challenge reviewed and officially validated by Jharkhand Higher & Technical Education"
    ))
    db.commit()
    return {"status": "success", "message": "Challenge officially validated"}

@router.post("/challenges/{challenge_id}/escalate")
def escalate_challenge(
    challenge_id: int,
    payload: EscalateChallengeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
        
    old_tier = ch.current_tier or "PANCHAYAT"
    target_tier = payload.target_tier.upper()
    
    tier_levels = {"PANCHAYAT": 1, "BLOCK": 2, "DISTRICT": 3, "STATE": 4}
    new_level = tier_levels.get(target_tier, 4)
    
    ch.current_tier = target_tier
    ch.escalation_level = new_level
    ch.escalated_by = current_user.full_name
    ch.escalation_remarks = payload.remarks
    
    db.add(StatusHistory(
        challenge_id=ch.id,
        from_status=ch.status.value,
        to_status=ch.status.value,
        updated_by=f"{current_user.full_name} ({old_tier} Tier)",
        remarks=f"Escalated from {old_tier} to {target_tier} Level: {payload.remarks}"
    ))
    db.commit()
    db.refresh(ch)
    return {
        "status": "success", 
        "message": f"Challenge successfully escalated from {old_tier} to {target_tier} level!",
        "current_tier": ch.current_tier,
        "escalation_level": ch.escalation_level
    }

@router.get("/reports/csv")
def export_csv_report(db: Session = Depends(get_db)):
    challenges = db.query(Challenge).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Category", "District", "Priority", "Status", "Created At"])
    for c in challenges:
        dist = c.location.district_name if c.location else "Jharkhand"
        writer.writerow([c.id, c.title, c.category, dist, c.priority.value, c.status.value, c.created_at.strftime("%Y-%m-%d")])
        
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jharkhand_sih_challenges_report.csv"}
    )
