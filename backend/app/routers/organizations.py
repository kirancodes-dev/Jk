from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import OrganizationProfile, User, UserRole, AuditLog, AccountStatus, University, IndustryPartner
from backend.app.schemas.schemas import (
    OrganizationProfileCreate, OrganizationProfileOut, OrganizationVerifyRequest
)
from backend.app.routers.deps import get_current_user, require_permission, check_jurisdiction

router = APIRouter(prefix="/organizations", tags=["Organization Verification"])

@router.post("/register", response_model=OrganizationProfileOut, status_code=status.HTTP_201_CREATED)
def register_organization(
    payload: OrganizationProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit institutional profile for government accreditation and verification."""
    existing = db.query(OrganizationProfile).filter(OrganizationProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An organization profile has already been registered for this account."
        )

    profile = OrganizationProfile(
        user_id=current_user.id,
        legal_name=payload.legal_name,
        org_type=payload.org_type.upper(),
        reg_number=payload.reg_number,
        official_email=payload.official_email,
        official_domain=payload.official_domain,
        district_name=payload.district_name,
        address=payload.address,
        contact_person=payload.contact_person,
        phone_number=payload.phone_number,
        website=payload.website,
        verification_status="PENDING",
        submitted_documents=payload.submitted_documents
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Log audit entry
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.role.value,
        action="ORGANIZATION_REGISTERED",
        entity_name="OrganizationProfile",
        entity_id=profile.id,
        new_state="PENDING",
        reason=f"Registration submitted by {payload.legal_name}"
    ))
    db.commit()

    return profile

@router.get("/me", response_model=OrganizationProfileOut)
def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(OrganizationProfile).filter(OrganizationProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No organization profile found for this account.")
    return profile

@router.get("", response_model=List[OrganizationProfileOut])
def list_organizations(
    status_filter: Optional[str] = None,
    org_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(OrganizationProfile)
    if status_filter and status_filter != "All":
        query = query.filter(OrganizationProfile.verification_status == status_filter.upper())
    if org_type and org_type != "All":
        query = query.filter(OrganizationProfile.org_type == org_type.upper())
    return query.order_by(OrganizationProfile.created_at.desc()).all()

@router.post("/{org_id}/verify", response_model=OrganizationProfileOut)
def verify_organization(
    org_id: int,
    payload: OrganizationVerifyRequest,
    current_user: User = Depends(require_permission("organization.verify")),
    db: Session = Depends(get_db)
):
    """Authorized government verifier decision for an institution/organization profile."""
    profile = db.query(OrganizationProfile).filter(OrganizationProfile.id == org_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Enforce jurisdiction
    allowed, reason = check_jurisdiction(current_user, target_district=profile.district_name)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: {reason}"
        )

    old_status = profile.verification_status
    new_status = payload.status.upper()
    if new_status not in ["VERIFIED", "REJECTED", "UNDER_REVIEW", "SUSPENDED"]:
        raise HTTPException(status_code=400, detail="Invalid verification status")

    profile.verification_status = new_status
    profile.rejection_reason = payload.rejection_reason if new_status == "REJECTED" else None
    profile.verified_by_user_id = current_user.id
    profile.verified_at = datetime.now(timezone.utc)

    # Synchronize linked User account state
    if profile.user:
        if new_status == "VERIFIED":
            profile.user.is_verified = True
            profile.user.account_status = AccountStatus.ACTIVE
        elif new_status in ("REJECTED", "SUSPENDED"):
            profile.user.is_verified = False
            profile.user.account_status = AccountStatus.SUSPENDED

    # Link/synchronize the University capability profile (Stage 6): only a verified,
    # active HEI may adopt or receive assignments.
    if profile.org_type == "UNIVERSITY" and profile.user:
        univ = db.query(University).filter(University.user_id == profile.user.id).first()
        if univ:
            univ.organization_profile_id = profile.id
            if new_status in ("REJECTED", "SUSPENDED"):
                univ.is_active = False
            elif new_status == "VERIFIED":
                univ.is_active = True

    # Link/synchronize the industry/startup/MSME/CSR/lab capability profile (Stage 7):
    # only a verified, active partner may offer or accept collaborations.
    if profile.org_type in ("INDUSTRY", "STARTUP", "MSME", "CSR", "CSR_FOUNDATION", "LAB", "RESEARCH_LAB", "INNOVATION_HUB") and profile.user:
        partner = db.query(IndustryPartner).filter(IndustryPartner.user_id == profile.user.id).first()
        if partner:
            partner.organization_profile_id = profile.id
            if new_status in ("REJECTED", "SUSPENDED"):
                partner.is_active = False
                partner.suspended_reason = payload.rejection_reason
            elif new_status == "VERIFIED":
                partner.is_active = True
                partner.suspended_reason = None

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.role.value,
        action=f"ORGANIZATION_{new_status}",
        entity_name="OrganizationProfile",
        entity_id=profile.id,
        old_state=old_status,
        new_state=new_status,
        reason=payload.rejection_reason or f"Government verification by {current_user.full_name}"
    ))
    db.commit()
    db.refresh(profile)
    return profile

