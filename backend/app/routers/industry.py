from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import IndustryPartner, Project, IndustryCollaboration, Challenge, ChallengeLocation, User
from backend.app.schemas.schemas import ProjectOut, IndustryCollaborationOut
from backend.app.routers.deps import get_current_user

router = APIRouter(prefix="/industry", tags=["Industry"])

@router.get("/dashboard")
def get_industry_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ind = db.query(IndustryPartner).filter(IndustryPartner.user_id == current_user.id).first()
    if not ind:
        ind = db.query(IndustryPartner).first()
        
    ind_id = ind.id if ind else 1
    collaborations = db.query(IndustryCollaboration).filter(IndustryCollaboration.industry_id == ind_id).all()
    available_projects = db.query(Project).all()
    
    return {
        "company_name": ind.company_name if ind else "Industry Partner",
        "industry_domain": ind.industry_domain if ind else "CSR & Sustainability",
        "csr_focus_areas": ind.csr_focus_areas if ind else "Water, Agriculture, Health",
        "technologies": ind.technologies if ind else "IoT, Automation",
        "available_projects_count": len(available_projects),
        "active_collaborations_count": len(collaborations),
        "collaborations": [
            {
                "id": c.id,
                "project_id": c.project_id,
                "project_name": c.project.name if c.project else "Project",
                "university_name": c.project.university.institution_name if c.project and c.project.university else "University",
                "offer_type": c.offer_type,
                "status": c.status
            } for c in collaborations
        ]
    }

@router.get("/browse-projects", response_model=List[ProjectOut])
def browse_projects(
    domain: Optional[str] = None,
    stage: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Project).join(Challenge)
    if domain and domain != "All":
        query = query.filter(Challenge.category == domain)
    if stage and stage != "All":
        query = query.filter(Project.current_stage.ilike(f"%{stage}%"))
    if district and district != "All":
        query = query.join(ChallengeLocation).filter(ChallengeLocation.district_name.ilike(f"%{district}%"))
        
    projects = query.all()
    out = []
    for p in projects:
        out.append(ProjectOut(
            id=p.id,
            challenge_id=p.challenge_id,
            challenge_title=p.challenge.title if p.challenge else "Challenge",
            university_id=p.university_id,
            university_name=p.university.institution_name if p.university else "University",
            faculty_mentor_name=p.faculty_mentor.user.full_name if p.faculty_mentor and p.faculty_mentor.user else None,
            name=p.name,
            description=p.description,
            progress_percentage=p.progress_percentage,
            current_stage=p.current_stage,
            created_at=p.created_at
        ))
    return out

from pydantic import BaseModel
from backend.app.models.models import AuditLog

class IndustrySponsorRequest(BaseModel):
    project_id: int
    amount: Optional[float] = 0.0
    sponsorship_type: Optional[str] = "GRANT"
    notes: Optional[str] = None
    offer_type: Optional[str] = "Funding"

@router.post("/sponsor")
@router.post("/collaborate")
def sponsor_or_collaborate(
    payload: IndustrySponsorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ind = db.query(IndustryPartner).filter(IndustryPartner.user_id == current_user.id).first()
    ind_id = ind.id if ind else 1

    offer_type = payload.offer_type or payload.sponsorship_type or "Funding"
    description = payload.notes or f"CSR Funding / Sponsorship: ₹{payload.amount:,.2f}" if payload.amount else "Industry Partnership"

    collab = IndustryCollaboration(
        project_id=project.id,
        industry_id=ind_id,
        offer_type=offer_type,
        description=description,
        status="Offered"
    )
    db.add(collab)

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        action="INDUSTRY_OFFER_SPONSORSHIP",
        entity_name="Project",
        entity_id=project.id,
        new_state=f"Offer: {offer_type} by Industry #{ind_id}",
        reason=description
    ))
    db.commit()
    db.refresh(collab)

    return {
        "status": "success",
        "message": f"Collaboration proposal ({offer_type}) registered successfully.",
        "collaboration_id": collab.id,
        "project_id": project.id
    }

