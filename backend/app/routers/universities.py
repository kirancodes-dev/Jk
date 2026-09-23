from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import (
    University, Challenge, Project, Student, Faculty, User, UserRole,
    ChallengeStatus, StatusHistory, ChallengeAllocation, AllocationStatus,
    UniversityFacility, UniversityDistrictCoverage, UniversityCapabilityEvidence,
    Department
)
from backend.app.schemas.schemas import (
    UniversityFacilityCreate, UniversityFacilityOut, UniversityDistrictCoverageCreate,
    UniversityDistrictCoverageOut, UniversityCapabilityEvidenceCreate, UniversityCapabilityEvidenceOut,
    UniversityProfileOut, UniversityProfileUpdate, DepartmentOut, ChallengeAllocationOut,
    AllocationResponseRequest
)
from backend.app.services.workflow_service import WorkflowService
from backend.app.routers.deps import get_current_user, require_permission, require_verified_active_university

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

        results.append({
            "id": u.id,
            "institution_name": u.institution_name,
            "district_name": u.district_name,
            "city": city,
            "state": state,
            "is_active": u.is_active,
            "is_verified": u.is_verified_active,
            "address": u.address,
            "website": u.website,
            "has_incubation_center": u.has_incubation_center,
            "has_innovation_center": u.has_innovation_center,
            "nirf_ranking": u.nirf_ranking,
            "capacity_max_active_projects": u.capacity_max_active_projects,
            "expertise_areas": [e.domain for e in u.expertise_areas]
        })
    return results


# ------------------------------------------------------------------
# Verified capability profile
# ------------------------------------------------------------------

def _profile_out(u: University, db: Session) -> UniversityProfileOut:
    active_count = db.query(Project).filter(Project.university_id == u.id, Project.current_stage != "Terminated").count()
    departments_out = []
    for d in u.departments:
        departments_out.append(DepartmentOut(
            id=d.id, name=d.name, head_of_department=d.head_of_department,
            faculty_count=len(d.faculty_members), student_count=len(d.students)
        ))
    return UniversityProfileOut(
        id=u.id, institution_name=u.institution_name, district_name=u.district_name,
        address=u.address, website=u.website, nirf_ranking=u.nirf_ranking,
        is_active=u.is_active,
        verification_status=u.organization_profile.verification_status if u.organization_profile else ("VERIFIED" if u.user and u.user.is_verified else "PENDING"),
        is_verified_active=u.is_verified_active,
        capacity_max_active_projects=u.capacity_max_active_projects,
        active_projects_count=active_count,
        departments=departments_out,
        facilities=list(u.facilities),
        district_coverage=list(u.district_coverage),
        capability_evidence=list(u.capability_evidence),
        expertise_areas=[e.domain for e in u.expertise_areas]
    )


@router.get("/{university_id}/profile", response_model=UniversityProfileOut)
def get_university_profile(university_id: int, db: Session = Depends(get_db)):
    univ = db.query(University).filter(University.id == university_id).first()
    if not univ:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")
    return _profile_out(univ, db)


@router.get("/profile/me", response_model=UniversityProfileOut)
def get_my_university_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    univ = db.query(University).filter(University.user_id == current_user.id).first()
    if not univ:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University institution profile not found for authenticated account.")
    return _profile_out(univ, db)


@router.put("/profile/me", response_model=UniversityProfileOut)
def update_my_university_profile(
    payload: UniversityProfileUpdate,
    current_user: User = Depends(require_permission("profile.manage")),
    db: Session = Depends(get_db)
):
    univ = db.query(University).filter(University.user_id == current_user.id).first()
    if not univ:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University institution profile not found for authenticated account.")
    if current_user.role != UserRole.UNIVERSITY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only the institution's own account may edit its capability profile.")

    if payload.address is not None:
        univ.address = payload.address
    if payload.website is not None:
        univ.website = payload.website
    if payload.facilities_description is not None:
        univ.facilities_description = payload.facilities_description
    if payload.nirf_ranking is not None:
        univ.nirf_ranking = payload.nirf_ranking
    if payload.capacity_max_active_projects is not None:
        if payload.capacity_max_active_projects < 1:
            raise HTTPException(status_code=400, detail="Capacity must be at least 1 active project.")
        univ.capacity_max_active_projects = payload.capacity_max_active_projects

    db.commit()
    return _profile_out(univ, db)


@router.post("/facilities", response_model=UniversityFacilityOut, status_code=status.HTTP_201_CREATED)
def add_facility(
    payload: UniversityFacilityCreate,
    current_user: User = Depends(require_permission("profile.manage")),
    db: Session = Depends(get_db)
):
    univ = require_verified_active_university(current_user, db) if current_user.role == UserRole.UNIVERSITY else None
    if not univ:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only university accounts may register facilities.")
    facility = UniversityFacility(
        university_id=univ.id, facility_type=payload.facility_type, name=payload.name,
        description=payload.description, capacity_units=payload.capacity_units, is_operational=payload.is_operational
    )
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return facility


@router.post("/district-coverage", response_model=UniversityDistrictCoverageOut, status_code=status.HTTP_201_CREATED)
def add_district_coverage(
    payload: UniversityDistrictCoverageCreate,
    current_user: User = Depends(require_permission("profile.manage")),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.UNIVERSITY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only university accounts may declare district coverage.")
    univ = require_verified_active_university(current_user, db)
    coverage = UniversityDistrictCoverage(university_id=univ.id, district_name=payload.district_name, is_primary=payload.is_primary)
    db.add(coverage)
    db.commit()
    db.refresh(coverage)
    return coverage


@router.post("/capability-evidence", response_model=UniversityCapabilityEvidenceOut, status_code=status.HTTP_201_CREATED)
def add_capability_evidence(
    payload: UniversityCapabilityEvidenceCreate,
    current_user: User = Depends(require_permission("profile.manage")),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.UNIVERSITY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only university accounts may submit accreditation/capability evidence.")
    univ = db.query(University).filter(University.user_id == current_user.id).first()
    if not univ:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University institution profile not found for authenticated account.")
    evidence = UniversityCapabilityEvidence(
        university_id=univ.id, evidence_type=payload.evidence_type, title=payload.title,
        evidence_object_id=payload.evidence_object_id, issued_by=payload.issued_by, valid_until=payload.valid_until
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


# ------------------------------------------------------------------
# Assignment inbox (Stage 4 allocation workflow, HEI-facing)
# ------------------------------------------------------------------

@router.get("/assignments", response_model=List[ChallengeAllocationOut])
def get_assignment_inbox(
    current_user: User = Depends(require_permission("challenge.adopt")),
    db: Session = Depends(get_db)
):
    univ = db.query(University).filter(University.user_id == current_user.id).first()
    if not univ or not univ.organization_profile_id:
        return []
    return db.query(ChallengeAllocation).filter(
        ChallengeAllocation.assigned_to_org_id == univ.organization_profile_id
    ).order_by(ChallengeAllocation.created_at.desc()).all()


@router.post("/assignments/{allocation_id}/respond", response_model=ChallengeAllocationOut)
def respond_to_assignment(
    allocation_id: int,
    payload: AllocationResponseRequest,
    current_user: User = Depends(require_permission("challenge.adopt")),
    db: Session = Depends(get_db)
):
    """
    Formal assignment acceptance/decline with mandatory reason on decline and
    deadline enforcement on accept. A university cannot respond to another
    university's assignment (enforced in WorkflowService.respond_allocation).
    """
    if current_user.role == UserRole.UNIVERSITY:
        require_verified_active_university(current_user, db)

    allocation = WorkflowService.respond_allocation(
        db=db, allocation_id=allocation_id, actor=current_user, decision=payload.decision,
        notes=payload.notes, coi_declared=payload.coi_declared, expected_version=payload.expected_version
    )
    db.commit()
    db.refresh(allocation)
    return allocation


@router.get("/dashboard")
def get_university_dashboard(
    current_user: User = Depends(require_permission("challenge.adopt")),
    db: Session = Depends(get_db)
):
    univ = db.query(University).filter(University.user_id == current_user.id).first()
    if not univ:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University institution profile not found for authenticated account."
        )

    assigned_challenges = db.query(Challenge).filter(Challenge.assigned_university_id == univ.id).all()
    active_projects = db.query(Project).filter(Project.university_id == univ.id).all()
    student_count = db.query(Student).filter(Student.university_id == univ.id).count()
    faculty_count = db.query(Faculty).filter(Faculty.university_id == univ.id).count()
    completed_projects = [p for p in active_projects if p.progress_percentage >= 100.0]

    pending_assignments = 0
    if univ.organization_profile_id:
        pending_assignments = db.query(ChallengeAllocation).filter(
            ChallengeAllocation.assigned_to_org_id == univ.organization_profile_id,
            ChallengeAllocation.status == AllocationStatus.OFFERED
        ).count()

    return {
        "university_name": univ.institution_name,
        "is_verified_active": univ.is_verified_active,
        "capacity_max_active_projects": univ.capacity_max_active_projects,
        "assigned_challenges_count": len(assigned_challenges),
        "new_challenges_count": len([c for c in assigned_challenges if c.status == ChallengeStatus.UNIVERSITY_ASSIGNED]),
        "pending_assignments_count": pending_assignments,
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
    current_user: User = Depends(require_permission("challenge.adopt")),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    if current_user.role == UserRole.UNIVERSITY:
        univ = require_verified_active_university(current_user, db)
        if ch.assigned_university_id and ch.assigned_university_id != univ.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: This challenge was assigned to another institution."
            )
        ch.assigned_university_id = univ.id

    # Update active allocation if present
    active_alloc = db.query(ChallengeAllocation).filter(
        ChallengeAllocation.challenge_id == ch.id,
        ChallengeAllocation.status == AllocationStatus.OFFERED
    ).first()
    if active_alloc:
        active_alloc.status = AllocationStatus.ACCEPTED
        active_alloc.coi_declared = True
        active_alloc.responded_at = ch.updated_at
        active_alloc.response_notes = "Accepted by university"

    WorkflowService.transition_challenge(
        db=db,
        challenge=ch,
        to_status=ChallengeStatus.TEAM_FORMED,
        actor=current_user,
        remarks="Challenge accepted by institution. Multidisciplinary project team mobilization initiated."
    )
    db.commit()
    return {"status": "success", "message": "Challenge accepted. Ready to create project."}

@router.post("/reject-challenge/{challenge_id}")
def reject_challenge(
    challenge_id: int,
    reason: str = "Capacity constraints",
    current_user: User = Depends(require_permission("challenge.adopt")),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    if current_user.role == UserRole.UNIVERSITY:
        univ = db.query(University).filter(University.user_id == current_user.id).first()
        if not univ:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University profile not found")
        if ch.assigned_university_id != univ.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: This challenge was not assigned to your institution."
            )

    # Update active allocation if present
    active_alloc = db.query(ChallengeAllocation).filter(
        ChallengeAllocation.challenge_id == ch.id,
        ChallengeAllocation.status == AllocationStatus.OFFERED
    ).first()
    if active_alloc:
        active_alloc.status = AllocationStatus.DECLINED
        active_alloc.responded_at = ch.updated_at
        active_alloc.response_notes = reason

    ch.assigned_university_id = None
    WorkflowService.transition_challenge(
        db=db,
        challenge=ch,
        to_status=ChallengeStatus.VALIDATED,
        actor=current_user,
        remarks=f"University declined challenge: {reason}. Returned to pool for re-assignment."
    )
    db.commit()
    return {"status": "success", "message": "Challenge returned to validated pool for re-assignment."}

@router.get("/{university_id}/roster")
def get_university_roster(
    university_id: int,
    db: Session = Depends(get_db)
):
    univ = db.query(University).filter(University.id == university_id).first()
    if not univ:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")

    faculty = db.query(Faculty).filter(Faculty.university_id == university_id).all()
    students = db.query(Student).filter(Student.university_id == university_id).all()

    return {
        "faculty": [
            {
                "id": f.id,
                "name": f.user.full_name if f.user else f"Faculty #{f.id}",
                "department": f.department.name if f.department else None,
                "designation": f.designation,
                "expertise": f.expertise
            } for f in faculty
        ],
        "students": [
            {
                "id": s.id,
                "name": s.user.full_name if s.user else f"Student #{s.id}",
                "roll_number": s.roll_number,
                "degree": s.degree,
                "department": s.department.name if s.department else None,
                "skills": s.skills
            } for s in students
        ]
    }
