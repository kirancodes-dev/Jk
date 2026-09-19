from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import (
    University, Challenge, Project, Student, Faculty, User, UserRole,
    ChallengeStatus, StatusHistory
)
from backend.app.routers.deps import get_current_user

router = APIRouter(prefix="/universities", tags=["Universities"])

@router.get("")
def list_universities(db: Session = Depends(get_db)):
    univs = db.query(University).all()
    results = []
    for u in univs:
        city = u.district_name
        state = "Jharkhand"
        if u.address:
            addr_lower = u.address.lower()
            if "karnataka" in addr_lower or "bengaluru" in addr_lower or "bangalore" in addr_lower:
                state = "Karnataka"
            elif "jharkhand" in addr_lower:
                state = "Jharkhand"
            elif "bihar" in addr_lower:
                state = "Bihar"
            elif "delhi" in addr_lower:
                state = "Delhi"
            elif "maharashtra" in addr_lower:
                state = "Maharashtra"

        is_verified = True
        if u.user and hasattr(u.user, "is_verified"):
            is_verified = bool(u.user.is_verified)

        results.append({
            "id": u.id,
            "institution_name": u.institution_name,
            "district_name": u.district_name,
            "city": city,
            "state": state,
            "is_verified": is_verified,
            "address": u.address,
            "website": u.website,
            "has_incubation_center": u.has_incubation_center,
            "has_innovation_center": u.has_innovation_center,
            "nirf_ranking": u.nirf_ranking,
            "expertise_areas": [e.domain for e in u.expertise_areas]
        })
    return results

@router.get("/dashboard")
def get_university_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    univ = db.query(University).filter(University.user_id == current_user.id).first()
    if not univ:
        # Fallback to first university for demo ease
        univ = db.query(University).first()
        
    univ_id = univ.id if univ else 1
    
    assigned_challenges = db.query(Challenge).filter(Challenge.assigned_university_id == univ_id).all()
    active_projects = db.query(Project).filter(Project.university_id == univ_id).all()
    student_count = db.query(Student).filter(Student.university_id == univ_id).count()
    faculty_count = db.query(Faculty).filter(Faculty.university_id == univ_id).count()
    completed_projects = [p for p in active_projects if p.progress_percentage >= 100.0]
    
    return {
        "university_name": univ.institution_name if univ else "University",
        "assigned_challenges_count": len(assigned_challenges),
        "new_challenges_count": len([c for c in assigned_challenges if c.status == ChallengeStatus.UNIVERSITY_ASSIGNED]),
        "active_projects_count": len(active_projects),
        "completed_projects_count": len(completed_projects),
        "student_teams_count": len(active_projects),
        "student_count": student_count,
        "faculty_mentors_count": faculty_count,
        "assigned_challenges": [
            {
                "id": c.id,
                "title": c.title,
                "category": c.category,
                "priority": c.priority.value,
                "status": c.status.value,
                "district_name": c.location.district_name if c.location else "Jharkhand"
            } for c in assigned_challenges
        ]
    }

@router.post("/accept-challenge/{challenge_id}")
def accept_challenge(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
        
    ch.status = ChallengeStatus.TEAM_FORMED
    db.add(StatusHistory(
        challenge_id=ch.id,
        from_status="UNIVERSITY_ASSIGNED",
        to_status="TEAM_FORMED",
        updated_by=f"{current_user.full_name} (University)",
        remarks="Challenge accepted by institution. Multidisciplinary project team mobilization initiated."
    ))
    db.commit()
    return {"status": "success", "message": "Challenge accepted. Ready to create project."}

@router.post("/reject-challenge/{challenge_id}")
def reject_challenge(
    challenge_id: int,
    reason: str = "Capacity constraints",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    old_status = ch.status.value
    ch.assigned_university_id = None
    ch.status = ChallengeStatus.VALIDATED
    
    db.add(StatusHistory(
        challenge_id=ch.id,
        from_status=old_status,
        to_status="VALIDATED",
        updated_by=f"{current_user.full_name} (University)",
        remarks=f"University declined challenge: {reason}. Returned to pool for re-assignment."
    ))
    db.commit()
    return {"status": "success", "message": "Challenge returned to validated pool for re-assignment."}
