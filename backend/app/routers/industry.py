from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import (
    IndustryPartner, Project, IndustryCollaboration, Challenge,
    ChallengeLocation, User, UserRole, AuditLog, FundingRecord, IPConsentRecord, IPConsentStatus
)
from backend.app.schemas.schemas import (
    ProjectOut, IndustryCollaborationOut, IndustryPartnerProfileOut, IndustryPartnerProfileUpdate,
    CollaborationAgreementOut, FundingRecordOut, RedactedProjectDiscoveryOut
)
from backend.app.routers.deps import get_current_user, require_permission, require_verified_active_partner

router = APIRouter(prefix="/industry", tags=["Industry"])

@router.get("/dashboard")
def get_industry_dashboard(
    current_user: User = Depends(require_permission("collaboration.create")),
    db: Session = Depends(get_db)
):
    ind = db.query(IndustryPartner).filter(IndustryPartner.user_id == current_user.id).first()
    if not ind:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Industry partner organization profile not found for authenticated account."
        )

    collaborations = db.query(IndustryCollaboration).filter(IndustryCollaboration.industry_id == ind.id).all()
    active_agreements = [c for c in collaborations if c.agreement_status.value in ("ACTIVE", "MILESTONE_LINKED", "CONTRACT_RECORDED")]
    funding_records = db.query(FundingRecord).filter(FundingRecord.industry_id == ind.id).all()
    pending_consents = db.query(IPConsentRecord).filter(
        IPConsentRecord.party_user_id == current_user.id, IPConsentRecord.status == IPConsentStatus.PENDING
    ).count()
    available_projects = db.query(Project).count()

    return {
        "company_name": ind.company_name,
        "industry_domain": ind.industry_domain or "CSR & Sustainability",
        "partner_type": ind.partner_type.value,
        "csr_eligible": ind.csr_eligible,
        "csr_focus_areas": ind.csr_focus_areas or "Water, Agriculture, Health",
        "technologies": ind.technologies or "IoT, Automation",
        "verification_status": ind.organization_profile.verification_status if ind.organization_profile else ("VERIFIED" if current_user.is_verified else "PENDING"),
        "is_verified_active": ind.is_verified_active,
        "available_projects_count": available_projects,
        "active_collaborations_count": len(active_agreements),
        "total_funding_records": len(funding_records),
        "pending_ip_consents_count": pending_consents,
        "collaborations": [
            {
                "id": c.id,
                "project_id": c.project_id,
                "project_name": c.project.name if c.project else "Project",
                "university_name": c.project.university.institution_name if c.project and c.project.university else "University",
                "offer_type": c.offer_type,
                "status": c.agreement_status.value
            } for c in collaborations
        ]
    }


@router.get("/profile/me", response_model=IndustryPartnerProfileOut)
def get_my_partner_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ind = db.query(IndustryPartner).filter(IndustryPartner.user_id == current_user.id).first()
    if not ind:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Industry partner organization profile not found for authenticated account.")
    return IndustryPartnerProfileOut(
        id=ind.id, company_name=ind.company_name, industry_domain=ind.industry_domain, partner_type=ind.partner_type,
        legal_identity=ind.legal_identity, registration_number=ind.registration_number, csr_eligible=ind.csr_eligible,
        authorized_representative_name=ind.authorized_representative_name,
        authorized_representative_designation=ind.authorized_representative_designation,
        domains=ind.domains, capacity_description=ind.capacity_description, geographic_coverage=ind.geographic_coverage,
        compliance_documents=ind.compliance_documents, is_active=ind.is_active,
        verification_status=ind.organization_profile.verification_status if ind.organization_profile else ("VERIFIED" if current_user.is_verified else "PENDING"),
        is_verified_active=ind.is_verified_active
    )


@router.put("/profile/me", response_model=IndustryPartnerProfileOut)
def update_my_partner_profile(
    payload: IndustryPartnerProfileUpdate,
    current_user: User = Depends(require_permission("profile.manage")),
    db: Session = Depends(get_db)
):
    if current_user.role not in (UserRole.INDUSTRY, UserRole.RESEARCH_LAB, UserRole.INNOVATION_HUB):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only partner accounts may edit their capability profile.")
    ind = db.query(IndustryPartner).filter(IndustryPartner.user_id == current_user.id).first()
    if not ind:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Industry partner organization profile not found for authenticated account.")

    import json as _json
    if payload.partner_type is not None:
        ind.partner_type = payload.partner_type
    if payload.legal_identity is not None:
        ind.legal_identity = payload.legal_identity
    if payload.registration_number is not None:
        ind.registration_number = payload.registration_number
    if payload.csr_eligible is not None:
        ind.csr_eligible = payload.csr_eligible
    if payload.authorized_representative_name is not None:
        ind.authorized_representative_name = payload.authorized_representative_name
    if payload.authorized_representative_designation is not None:
        ind.authorized_representative_designation = payload.authorized_representative_designation
    if payload.domains is not None:
        ind.domains = payload.domains
    if payload.capacity_description is not None:
        ind.capacity_description = payload.capacity_description
    if payload.geographic_coverage is not None:
        ind.geographic_coverage = _json.dumps(payload.geographic_coverage)
    if payload.compliance_documents is not None:
        ind.compliance_documents = _json.dumps(payload.compliance_documents)
    if payload.notification_preferences is not None:
        ind.notification_preferences = _json.dumps(payload.notification_preferences)
    ind.version = (ind.version or 1) + 1

    db.commit()
    db.refresh(ind)
    return IndustryPartnerProfileOut(
        id=ind.id, company_name=ind.company_name, industry_domain=ind.industry_domain, partner_type=ind.partner_type,
        legal_identity=ind.legal_identity, registration_number=ind.registration_number, csr_eligible=ind.csr_eligible,
        authorized_representative_name=ind.authorized_representative_name,
        authorized_representative_designation=ind.authorized_representative_designation,
        domains=ind.domains, capacity_description=ind.capacity_description, geographic_coverage=ind.geographic_coverage,
        compliance_documents=ind.compliance_documents, is_active=ind.is_active,
        verification_status=ind.organization_profile.verification_status if ind.organization_profile else "PENDING",
        is_verified_active=ind.is_verified_active
    )


@router.get("/browse-projects", response_model=List[ProjectOut])
def browse_projects(
    domain: Optional[str] = None,
    stage: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Legacy summary listing (kept for compatibility). Prefer /industry/discovery for the redacted view."""
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


@router.get("/discovery", response_model=List[RedactedProjectDiscoveryOut])
def discover_projects(
    domain: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Safe, read-only public project discovery view for potential industry/CSR/startup
    partners. Redacts sensitive information (no student names, no objectives, no
    proposals, no evidence, no documents) and bands progress instead of exposing an
    exact percentage.
    """
    query = db.query(Project).join(Challenge)
    if domain and domain != "All":
        query = query.filter(Challenge.category == domain)
    if district and district != "All":
        query = query.join(ChallengeLocation).filter(ChallengeLocation.district_name.ilike(f"%{district}%"))

    def _band(pct: float) -> str:
        if pct >= 100:
            return "100%"
        lower = int(pct // 25) * 25
        return f"{lower}-{lower + 25}%"

    out = []
    for p in query.all():
        out.append(RedactedProjectDiscoveryOut(
            id=p.id,
            challenge_title=p.challenge.title if p.challenge else "Societal Challenge",
            university_name=p.university.institution_name if p.university else "University",
            domain=p.challenge.category if p.challenge else "General",
            current_stage=p.current_stage,
            district_name=p.challenge.location.district_name if p.challenge and p.challenge.location else None,
            progress_band=_band(p.progress_percentage or 0.0),
            seeking_support_types=[]
        ))
    return out


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
    current_user: User = Depends(require_permission("funding.propose")),
    db: Session = Depends(get_db)
):
    """
    Legacy quick-sponsor endpoint. Creates a structured OFFERED collaboration
    (never immediately "Active" or funded) — the full review/acceptance/funding
    workflow still governs it via /projects/{id}/collaborations/{id}/review.
    """
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    ind = require_verified_active_partner(current_user, db)

    offer_type = payload.offer_type or payload.sponsorship_type or "Funding"
    description = payload.notes or (f"CSR Funding / Sponsorship: ₹{payload.amount:,.2f}" if payload.amount else "Industry Partnership")

    collab = IndustryCollaboration(
        project_id=project.id,
        industry_id=ind.id,
        offer_type=offer_type,
        description=description,
        status="Offered",
        cash_value=payload.amount,
        scope=description
    )
    db.add(collab)

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        action="INDUSTRY_OFFER_SPONSORSHIP",
        entity_name="Project",
        entity_id=project.id,
        new_state=f"Offer: {offer_type} by Industry #{ind.id}",
        reason=description
    ))
    db.commit()
    db.refresh(collab)

    return {
        "status": "success",
        "message": f"Collaboration proposal ({offer_type}) registered successfully and awaits university/government review.",
        "collaboration_id": collab.id,
        "project_id": project.id
    }
