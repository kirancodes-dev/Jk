from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import (
    Project, ProjectMember, ProjectMilestone, ProjectTask, SolutionProposal,
    IndustryCollaboration, ProjectDocument, Challenge, University, Faculty, Student, User,
    IndustryPartner, ChallengeStatus, MilestoneStatus, StatusHistory, UserRole,
    TeamInvitation, TeamInvitationStatus, ProjectMembershipHistory, ProposalStatus,
    ReviewComment, EvidenceFile, Department, utc_now,
    AgreementStatus, FundingRecord, IPRecord, IPConsentRecord, IPConsentStatus,
    ProjectClosureRecord, OutcomeReport
)
from backend.app.schemas.schemas import (
    ProjectCreate, ProjectOut, ProjectDetailOut, ProjectMemberOut, MilestoneCreate,
    MilestoneUpdate, MilestoneOut, MilestoneSubmitRequest, MilestoneReviewRequest,
    MilestonesFinalizeResponse, TaskCreate, TaskUpdate, TaskOut, TaskReviewRequest,
    SolutionProposalCreate, SolutionProposalOut, ProposalReviewRequest, IndustryFeedbackRequest,
    IndustryCollaborationCreate, IndustryCollaborationOut, ProjectDocumentOut,
    TeamInvitationCreate, TeamInvitationRespond, TeamInvitationOut, MemberRemoveRequest,
    MembershipHistoryOut, ReviewCommentCreate, ReviewCommentOut, EvidenceFileOut,
    CollaborationOfferCreate, CollaborationReviewRequest, CollaborationAgreementOut,
    FundingRecordCreate, FundingActionRequest, FundingRecordOut,
    IPRecordCreate, IPConsentRespond, IPConsentRecordOut, IPRecordOut, ModerationActionRequest,
    ProjectClosureEvaluationOut, ProjectClosureRequest, ProjectClosureRecordOut,
    OutcomeReportCreate, OutcomeReportOut
)
from backend.app.services.notification_service import notification_service
from backend.app.services.workflow_service import WorkflowService
from backend.app.services.storage_service import storage_service
from backend.app.routers.deps import (
    get_current_user, require_permission,
    verify_project_membership, check_jurisdiction, verify_challenge_jurisdiction,
    require_verified_active_university, verify_same_university_student, verify_same_university_faculty,
    require_verified_active_partner
)

router = APIRouter(prefix="/projects", tags=["Projects"])


# ------------------------------------------------------------------
# Listing & Detail
# ------------------------------------------------------------------

@router.get("", response_model=List[ProjectOut])
def list_projects(
    response: Response,
    page: Optional[int] = Query(None, ge=1, description="Page number"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    query = db.query(Project)
    total_count = query.count()
    response.headers["X-Total-Count"] = str(total_count)

    query = query.order_by(Project.created_at.desc())
    if page and page_size:
        response.headers["X-Page"] = str(page)
        response.headers["X-Page-Size"] = str(page_size)
        response.headers["X-Total-Pages"] = str((total_count + page_size - 1) // page_size)
        query = query.offset((page - 1) * page_size).limit(page_size)

    projects = query.all()
    return [_project_out(p) for p in projects]


def _project_out(p: Project) -> ProjectOut:
    return ProjectOut(
        id=p.id,
        challenge_id=p.challenge_id,
        challenge_title=p.challenge.title if p.challenge else "Societal Challenge",
        university_id=p.university_id,
        university_name=p.university.institution_name if p.university else "University",
        faculty_mentor_name=p.faculty_mentor.user.full_name if p.faculty_mentor and p.faculty_mentor.user else None,
        faculty_mentor_status=p.faculty_mentor_status,
        name=p.name,
        description=p.description,
        progress_percentage=p.progress_percentage,
        current_stage=p.current_stage,
        milestones_locked=p.milestones_locked,
        created_at=p.created_at
    )


@router.post("", response_model=ProjectDetailOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(require_permission("project.create")),
    db: Session = Depends(get_db)
):
    challenge = db.query(Challenge).filter(Challenge.id == payload.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    univ = None
    if current_user.role == UserRole.UNIVERSITY:
        univ = require_verified_active_university(current_user, db)
        if challenge.assigned_university_id and challenge.assigned_university_id != univ.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Challenge #{challenge.id} is assigned to another higher education institution."
            )
    elif current_user.role == UserRole.GOVERNMENT_ADMIN:
        if challenge.assigned_university_id:
            univ = db.query(University).filter(University.id == challenge.assigned_university_id).first()
        if not univ:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge has not yet been assigned to an accredited university institution."
            )
        if not univ.is_verified_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Assigned institution is not a verified, active HEI."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only accredited university administrators or government officials can initiate projects."
        )

    # Stage 4 state machine gate: a project may only be created once the challenge has
    # been formally assigned and accepted through the allocation workflow — never as an
    # ad-hoc side effect that skips required transitions.
    if challenge.status not in (ChallengeStatus.UNIVERSITY_ASSIGNED, ChallengeStatus.TEAM_FORMED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Challenge must first be formally assigned and accepted (current status: '{challenge.status.value}'). "
                   "Use the government assignment workflow and /universities/accept-challenge before creating a project."
        )

    active_count = db.query(Project).filter(
        Project.university_id == univ.id,
        Project.current_stage != "Terminated"
    ).count()
    if active_count >= univ.capacity_max_active_projects:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflict: University has reached its declared capacity of {univ.capacity_max_active_projects} active projects."
        )

    # Validate every invitee BEFORE any row is persisted, so a rejected request
    # (e.g. a cross-HEI student/faculty ID) never leaves an orphan project behind.
    faculty_to_invite = None
    if payload.faculty_mentor_id:
        faculty_to_invite = db.query(Faculty).filter(Faculty.id == payload.faculty_mentor_id).first()
        verify_same_university_faculty(faculty_to_invite, univ.id)

    students_to_invite = []
    if payload.student_ids:
        for s_id in payload.student_ids:
            student = db.query(Student).filter(Student.id == s_id).first()
            verify_same_university_student(student, univ.id)
            students_to_invite.append(student)

    project = Project(
        challenge_id=payload.challenge_id,
        university_id=univ.id,
        name=payload.name,
        description=payload.description,
        objectives=payload.objectives,
        expected_outcome=payload.expected_outcome,
        required_skills=payload.required_skills,
        timeline_months=payload.timeline_months,
        progress_percentage=0.0,
        current_stage="Research & Team Formation"
    )
    db.add(project)
    db.flush()

    # Team formation happens via invitation + acceptance; never auto-add members.
    if faculty_to_invite:
        db.add(TeamInvitation(
            project_id=project.id,
            invited_by_user_id=current_user.id,
            faculty_id=faculty_to_invite.id,
            role_in_team="Faculty Mentor",
            status=TeamInvitationStatus.PENDING
        ))

    for student in students_to_invite:
        db.add(TeamInvitation(
            project_id=project.id,
            invited_by_user_id=current_user.id,
            student_id=student.id,
            department_id=student.department_id,
            role_in_team="Multidisciplinary Researcher",
            status=TeamInvitationStatus.PENDING
        ))

    # Default weighted milestone scaffold (weights sum exactly to 100%, none pre-approved)
    default_milestones = [
        ("Problem Validation & Field Survey", "Engage rural stakeholders and collect field parameters."),
        ("Technical Architecture & Design", "Draft engineering schematics and bill of materials."),
        ("Prototype Fabrication & Lab Testing", "Assemble working proof of concept in university lab."),
        ("Field Deployment & Pilot Testing", "Deploy solution in the field and evaluate impact."),
    ]
    for title, description in default_milestones:
        db.add(ProjectMilestone(
            project_id=project.id, title=title, description=description,
            completion_percentage=0.0, weight_pct=25.0, status=MilestoneStatus.NOT_STARTED
        ))

    challenge.assigned_university_id = univ.id
    WorkflowService.transition_challenge(
        db=db,
        challenge=challenge,
        to_status=ChallengeStatus.TEAM_FORMED,
        actor=current_user,
        remarks=f"Project '{project.name}' initialized. Multidisciplinary team invitations dispatched."
    )
    db.commit()
    return _build_project_detail_response(project.id, db)


def _build_project_detail_response(project_id: int, db: Session):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    members_out = []
    for m in p.members:
        if not m.is_active:
            continue
        st = m.student
        if st and st.user:
            members_out.append(ProjectMemberOut(
                id=m.id,
                student_id=st.id,
                student_name=st.user.full_name,
                department_id=m.department_id or st.department_id,
                department_name=st.department.name if st.department else None,
                role_in_team=m.role_in_team,
                skills=st.skills,
                start_date=m.start_date,
                end_date=m.end_date,
                conflict_declared=m.conflict_declared,
                is_active=m.is_active
            ))

    pending_invitations_out = [
        _invitation_out(inv) for inv in p.team_invitations if inv.status == TeamInvitationStatus.PENDING
    ]

    milestones_out = [_milestone_out(ms, db) for ms in p.milestones]

    tasks_out = []
    for t in p.tasks:
        st_name = t.assigned_student.user.full_name if t.assigned_student and t.assigned_student.user else None
        tasks_out.append(TaskOut(
            id=t.id,
            title=t.title,
            milestone_id=t.milestone_id,
            assigned_to_student_id=t.assigned_to_student_id,
            assigned_student_name=st_name,
            status=t.status,
            is_completed=t.is_completed,
            submission_notes=t.submission_notes
        ))

    proposals_out = [_proposal_out(pr) for pr in p.proposals if pr.is_current] or [_proposal_out(pr) for pr in p.proposals]

    collabs_out = [
        IndustryCollaborationOut(
            id=c.id,
            company_name=c.industry.company_name if c.industry else "Industry Partner",
            industry_domain=c.industry.industry_domain if c.industry else "Engineering",
            offer_type=c.offer_type,
            description=c.description,
            status=c.status
        ) for c in p.collaborations
    ]

    docs_out = [
        ProjectDocumentOut(
            id=d.id, project_id=d.project_id, title=d.title, doc_type=d.doc_type,
            evidence_object_id=d.evidence_object_id, uploaded_at=d.uploaded_at
        ) for d in p.documents
    ]

    return ProjectDetailOut(
        **_project_out(p).model_dump(),
        objectives=p.objectives,
        expected_outcome=p.expected_outcome,
        required_skills=p.required_skills,
        members=members_out,
        pending_invitations=pending_invitations_out,
        milestones=milestones_out,
        tasks=tasks_out,
        proposals=proposals_out,
        collaborations=collabs_out,
        documents=docs_out
    )


@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project_detail(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    return _build_project_detail_response(project_id, db)


def verify_project_access(project: Project, current_user: User):
    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        return True
    if current_user.role == UserRole.UNIVERSITY and current_user.university_profile and current_user.university_profile.id == project.university_id:
        return True
    if current_user.role == UserRole.FACULTY_MENTOR and current_user.faculty_profile and project.faculty_mentor_id == current_user.faculty_profile.id:
        return True
    if current_user.role == UserRole.STUDENT and current_user.student_profile and any(
        m.student_id == current_user.student_profile.id and m.is_active for m in project.members
    ):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to modify this project. Only assigned university members, faculty mentors, or government admins have access."
    )


def _staff_or_mentor_or_gov(project: Project, current_user: User) -> bool:
    """Authorization for actions reserved to project staff (university/mentor) or government."""
    verify_project_access(project, current_user)
    return True


# ------------------------------------------------------------------
# Documents (server-generated evidence references only)
# ------------------------------------------------------------------

@router.post("/{project_id}/documents", response_model=ProjectDocumentOut)
async def add_project_document(
    project_id: int,
    title: str = Form(...),
    doc_type: str = Form("Report"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    evidence = await storage_service.save_evidence_file(
        file=file, owner_id=current_user.id, entity_type="PROJECT_DOCUMENT",
        entity_id=project_id, db=db, project_id=project_id
    )
    doc = ProjectDocument(
        project_id=project_id,
        title=title,
        file_url=f"/api/v1/files/evidence/{evidence.object_id}",
        doc_type=doc_type,
        evidence_object_id=evidence.object_id,
        uploaded_by_user_id=current_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return ProjectDocumentOut(
        id=doc.id, project_id=doc.project_id, title=doc.title, doc_type=doc.doc_type,
        evidence_object_id=doc.evidence_object_id, uploaded_at=doc.uploaded_at
    )


# ------------------------------------------------------------------
# Team Invitations & Membership
# ------------------------------------------------------------------

def _invitation_out(inv: TeamInvitation) -> TeamInvitationOut:
    return TeamInvitationOut(
        id=inv.id,
        project_id=inv.project_id,
        student_id=inv.student_id,
        student_name=inv.student.user.full_name if inv.student and inv.student.user else None,
        faculty_id=inv.faculty_id,
        faculty_name=inv.faculty.user.full_name if inv.faculty and inv.faculty.user else None,
        department_id=inv.department_id,
        role_in_team=inv.role_in_team,
        proposed_start_date=inv.proposed_start_date,
        proposed_end_date=inv.proposed_end_date,
        status=inv.status,
        conflict_declared=inv.conflict_declared,
        conflict_notes=inv.conflict_notes,
        created_at=inv.created_at
    )


@router.post("/{project_id}/team-invitations", response_model=TeamInvitationOut, status_code=status.HTTP_201_CREATED)
def invite_team_member(
    project_id: int,
    payload: TeamInvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_access(project, current_user)

    if not payload.student_id and not payload.faculty_id:
        raise HTTPException(status_code=400, detail="Either student_id or faculty_id must be provided.")
    if payload.student_id and payload.faculty_id:
        raise HTTPException(status_code=400, detail="An invitation targets either a student or a faculty mentor, not both.")

    if payload.student_id:
        student = db.query(Student).filter(Student.id == payload.student_id).first()
        verify_same_university_student(student, project.university_id)
        already_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id, ProjectMember.student_id == student.id, ProjectMember.is_active == True
        ).first()
        if already_member:
            raise HTTPException(status_code=400, detail="Student is already an active member of this project.")
        if payload.department_id:
            dept = db.query(Department).filter(Department.id == payload.department_id).first()
            if not dept or dept.university_id != project.university_id:
                raise HTTPException(status_code=400, detail="Rejected: Department does not belong to this institution.")

    if payload.faculty_id:
        faculty = db.query(Faculty).filter(Faculty.id == payload.faculty_id).first()
        verify_same_university_faculty(faculty, project.university_id)

    invitation = TeamInvitation(
        project_id=project_id,
        invited_by_user_id=current_user.id,
        student_id=payload.student_id,
        faculty_id=payload.faculty_id,
        department_id=payload.department_id,
        role_in_team=payload.role_in_team,
        proposed_start_date=payload.proposed_start_date,
        proposed_end_date=payload.proposed_end_date,
        status=TeamInvitationStatus.PENDING
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    invitee_user_id = None
    if invitation.student and invitation.student.user:
        invitee_user_id = invitation.student.user.id
    elif invitation.faculty and invitation.faculty.user:
        invitee_user_id = invitation.faculty.user.id
    if invitee_user_id:
        notification_service.create_notification(
            db, user_id=invitee_user_id, title="Team Invitation Received",
            message=f"You have been invited to join project '{project.name}' as {invitation.role_in_team}.",
            reference_id=project.id
        )
        db.commit()

    return _invitation_out(invitation)


@router.get("/{project_id}/team-invitations", response_model=List[TeamInvitationOut])
def list_project_invitations(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    invitations = db.query(TeamInvitation).filter(TeamInvitation.project_id == project_id).order_by(TeamInvitation.created_at.desc()).all()
    return [_invitation_out(inv) for inv in invitations]


@router.post("/team-invitations/{invitation_id}/respond", response_model=TeamInvitationOut)
def respond_to_invitation(
    invitation_id: int,
    payload: TeamInvitationRespond,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invitation = db.query(TeamInvitation).filter(TeamInvitation.id == invitation_id).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # Object-level authorization: only the invited student/faculty may respond
    is_invitee = False
    if invitation.student_id and current_user.role == UserRole.STUDENT:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        is_invitee = bool(student and student.id == invitation.student_id)
    elif invitation.faculty_id and current_user.role == UserRole.FACULTY_MENTOR:
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        is_invitee = bool(faculty and faculty.id == invitation.faculty_id)

    if not is_invitee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: This invitation was not addressed to you.")

    WorkflowService.respond_team_invitation(
        db=db, invitation=invitation, actor=current_user, decision=payload.decision,
        conflict_declared=payload.conflict_declared, conflict_notes=payload.conflict_notes,
        response_notes=payload.response_notes
    )
    db.commit()
    db.refresh(invitation)
    return _invitation_out(invitation)


@router.post("/{project_id}/members/{member_id}/remove")
def remove_project_member(
    project_id: int,
    member_id: int,
    payload: MemberRemoveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_access(project, current_user)

    member = db.query(ProjectMember).filter(
        ProjectMember.id == member_id, ProjectMember.project_id == project_id, ProjectMember.is_active == True
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Active project member not found")

    if payload.replacement_student_id:
        replacement = db.query(Student).filter(Student.id == payload.replacement_student_id).first()
        verify_same_university_student(replacement, project.university_id)

    WorkflowService.remove_project_member(
        db=db, member=member, actor=current_user, reason=payload.reason,
        replacement_student_id=payload.replacement_student_id,
        replacement_role_in_team=payload.replacement_role_in_team
    )
    db.commit()
    return {"status": "success", "message": "Membership change recorded."}


@router.get("/{project_id}/members/history", response_model=List[MembershipHistoryOut])
def get_membership_history(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    history = db.query(ProjectMembershipHistory).filter(
        ProjectMembershipHistory.project_id == project_id
    ).order_by(ProjectMembershipHistory.occurred_at.desc()).all()
    return [
        MembershipHistoryOut(
            id=h.id, action=h.action.value, student_id=h.student_id,
            previous_member_student_id=h.previous_member_student_id,
            role_in_team=h.role_in_team, reason=h.reason, occurred_at=h.occurred_at
        ) for h in history
    ]


# ------------------------------------------------------------------
# Weighted Milestones
# ------------------------------------------------------------------

def _milestone_out(ms: ProjectMilestone, db: Session) -> MilestoneOut:
    evidence_count = db.query(EvidenceFile).filter(
        EvidenceFile.entity_type == "MILESTONE_DELIVERABLE",
        EvidenceFile.entity_id == ms.id,
        EvidenceFile.is_current == True  # noqa: E712
    ).count()
    return MilestoneOut(
        id=ms.id, title=ms.title, description=ms.description,
        completion_percentage=100.0 if ms.status in (MilestoneStatus.APPROVED, MilestoneStatus.COMPLETED) else 0.0,
        weight_pct=ms.weight_pct, status=ms.status, due_date=ms.due_date,
        approved_by_faculty=ms.approved_by_faculty, review_notes=ms.review_notes,
        evidence_count=evidence_count
    )


@router.post("/{project_id}/milestones", response_model=MilestoneOut)
def add_milestone(
    project_id: int,
    payload: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_access(p, current_user)
    if p.milestones_locked:
        raise HTTPException(status_code=400, detail="Milestone plan is finalized and locked. Unlock via a government-authorized change request first.")

    existing_total = sum(m.weight_pct or 0.0 for m in p.milestones)
    if existing_total + payload.weight_pct > 100.0 + 1e-6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rejected: Milestone weights must sum to 100%. Current total is {existing_total:.1f}%; this addition would exceed the cap."
        )

    ms = ProjectMilestone(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        weight_pct=payload.weight_pct,
        due_date=payload.due_date,
        status=MilestoneStatus.NOT_STARTED
    )
    db.add(ms)
    db.commit()
    db.refresh(ms)
    return _milestone_out(ms, db)


@router.patch("/{project_id}/milestones/{milestone_id}", response_model=MilestoneOut)
def update_milestone(
    project_id: int,
    milestone_id: int,
    payload: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_access(p, current_user)
    if p.milestones_locked:
        raise HTTPException(status_code=400, detail="Milestone plan is finalized and locked.")

    ms = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == milestone_id, ProjectMilestone.project_id == project_id
    ).first()
    if not ms:
        raise HTTPException(status_code=404, detail="Milestone not found")
    if ms.status != MilestoneStatus.NOT_STARTED:
        raise HTTPException(status_code=400, detail="Only NOT_STARTED milestones may be edited. Progress is driven exclusively by evidence-backed review.")

    if payload.weight_pct is not None:
        other_total = sum(m.weight_pct or 0.0 for m in p.milestones if m.id != ms.id)
        if other_total + payload.weight_pct > 100.0 + 1e-6:
            raise HTTPException(status_code=400, detail=f"Rejected: Milestone weights must sum to 100%. Other milestones already total {other_total:.1f}%.")
        ms.weight_pct = payload.weight_pct
    if payload.title is not None:
        ms.title = payload.title
    if payload.description is not None:
        ms.description = payload.description
    if payload.due_date is not None:
        ms.due_date = payload.due_date

    db.commit()
    db.refresh(ms)
    return _milestone_out(ms, db)


@router.delete("/{project_id}/milestones/{milestone_id}")
def delete_milestone(
    project_id: int,
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_access(p, current_user)
    if p.milestones_locked:
        raise HTTPException(status_code=400, detail="Milestone plan is finalized and locked.")

    ms = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == milestone_id, ProjectMilestone.project_id == project_id
    ).first()
    if not ms:
        raise HTTPException(status_code=404, detail="Milestone not found")
    if ms.status != MilestoneStatus.NOT_STARTED:
        raise HTTPException(status_code=400, detail="Only NOT_STARTED milestones may be deleted.")

    db.delete(ms)
    db.commit()
    return {"status": "success", "message": "Milestone removed"}


@router.post("/{project_id}/milestones/finalize", response_model=MilestonesFinalizeResponse)
def finalize_milestones(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_access(p, current_user)

    total = sum(m.weight_pct or 0.0 for m in p.milestones)
    if abs(total - 100.0) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rejected: Milestone weights must sum to exactly 100% before finalization (current total: {total:.2f}%)."
        )
    p.milestones_locked = True
    db.commit()
    return MilestonesFinalizeResponse(status="success", message="Milestone plan finalized and locked.", total_weight=total, locked=True)


@router.post("/{project_id}/milestones/{milestone_id}/evidence", response_model=EvidenceFileOut)
async def upload_milestone_evidence(
    project_id: int,
    milestone_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    ms = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id, ProjectMilestone.project_id == project_id).first()
    if not ms:
        raise HTTPException(status_code=404, detail="Milestone not found")

    evidence = await storage_service.save_evidence_file(
        file=file, owner_id=current_user.id, entity_type="MILESTONE_DELIVERABLE",
        entity_id=milestone_id, db=db, project_id=project_id
    )
    if ms.status == MilestoneStatus.NOT_STARTED:
        WorkflowService.transition_milestone(db=db, milestone=ms, to_status=MilestoneStatus.IN_PROGRESS, actor=current_user, remarks="Deliverable evidence uploaded")
        db.commit()
    return evidence


@router.get("/{project_id}/milestones/{milestone_id}/evidence", response_model=List[EvidenceFileOut])
def list_milestone_evidence(
    project_id: int,
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    return db.query(EvidenceFile).filter(
        EvidenceFile.entity_type == "MILESTONE_DELIVERABLE", EvidenceFile.entity_id == milestone_id
    ).order_by(EvidenceFile.version.desc()).all()


@router.post("/{project_id}/milestones/{milestone_id}/submit", response_model=MilestoneOut)
def submit_milestone(
    project_id: int,
    milestone_id: int,
    payload: MilestoneSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_access(p, current_user)

    ms = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id, ProjectMilestone.project_id == project_id).first()
    if not ms:
        raise HTTPException(status_code=404, detail="Milestone not found")

    WorkflowService.submit_milestone(db=db, milestone=ms, actor=current_user, notes=payload.notes)
    db.commit()
    db.refresh(ms)
    return _milestone_out(ms, db)


@router.post("/{project_id}/milestones/{milestone_id}/review", response_model=MilestoneOut)
def review_milestone(
    project_id: int,
    milestone_id: int,
    payload: MilestoneReviewRequest,
    current_user: User = Depends(require_permission("milestone.approve")),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    # Object-level authorization: faculty must be THIS project's mentor; university must own it.
    if current_user.role == UserRole.FACULTY_MENTOR:
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if not faculty or p.faculty_mentor_id != faculty.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You are not the assigned faculty mentor for this project.")
    elif current_user.role == UserRole.UNIVERSITY:
        univ = db.query(University).filter(University.user_id == current_user.id).first()
        if not univ or p.university_id != univ.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Project does not belong to your university.")
    elif current_user.role in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER):
        if p.challenge:
            verify_challenge_jurisdiction(p.challenge, current_user, db, action="review_milestone")

    ms = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id, ProjectMilestone.project_id == project_id).first()
    if not ms:
        raise HTTPException(status_code=404, detail="Milestone not found")

    WorkflowService.review_milestone(db=db, milestone=ms, decision=payload.decision, actor=current_user, notes=payload.notes)
    db.commit()
    db.refresh(ms)
    return _milestone_out(ms, db)


# ------------------------------------------------------------------
# Tasks
# ------------------------------------------------------------------

@router.post("/{project_id}/tasks", response_model=TaskOut)
def add_task(
    project_id: int,
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_access(p, current_user)

    if payload.assigned_to_student_id:
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id, ProjectMember.student_id == payload.assigned_to_student_id,
            ProjectMember.is_active == True
        ).first()
        if not is_member:
            raise HTTPException(status_code=400, detail="Rejected: Task can only be assigned to an active member of this project's team.")

    if payload.milestone_id:
        ms = db.query(ProjectMilestone).filter(ProjectMilestone.id == payload.milestone_id, ProjectMilestone.project_id == project_id).first()
        if not ms:
            raise HTTPException(status_code=400, detail="Rejected: Milestone does not belong to this project.")

    task = ProjectTask(
        project_id=project_id,
        milestone_id=payload.milestone_id,
        title=payload.title,
        assigned_to_student_id=payload.assigned_to_student_id,
        due_date=payload.due_date,
        status="PENDING",
        is_completed=False
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskOut(
        id=task.id, title=task.title, milestone_id=task.milestone_id,
        assigned_to_student_id=task.assigned_to_student_id, assigned_student_name=None,
        status=task.status, is_completed=task.is_completed
    )


@router.post("/{project_id}/tasks/{task_id}/evidence", response_model=EvidenceFileOut)
async def upload_task_evidence(
    project_id: int,
    task_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(ProjectTask).filter(ProjectTask.id == task_id, ProjectTask.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role != UserRole.GOVERNMENT_ADMIN:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if current_user.role == UserRole.STUDENT:
            if not student or task.assigned_to_student_id != student.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You may only submit evidence for work assigned to you.")
        else:
            verify_project_access(db.query(Project).filter(Project.id == project_id).first(), current_user)

    evidence = await storage_service.save_evidence_file(
        file=file, owner_id=current_user.id, entity_type="TASK_SUBMISSION",
        entity_id=task_id, db=db, project_id=project_id
    )
    task.status = "SUBMITTED"
    db.commit()
    return evidence


@router.post("/{project_id}/tasks/{task_id}/review")
def review_task(
    project_id: int,
    task_id: int,
    payload: TaskReviewRequest,
    current_user: User = Depends(require_permission("milestone.approve")),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role == UserRole.FACULTY_MENTOR:
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if not faculty or p.faculty_mentor_id != faculty.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You are not the assigned faculty mentor for this project.")

    task = db.query(ProjectTask).filter(ProjectTask.id == task_id, ProjectTask.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    decision = payload.decision.upper()
    if decision not in ("APPROVE", "REVISION_REQUESTED"):
        raise HTTPException(status_code=400, detail="Decision must be 'APPROVE' or 'REVISION_REQUESTED'")

    task.status = "APPROVED" if decision == "APPROVE" else "REVISION_REQUESTED"
    task.is_completed = decision == "APPROVE"
    if payload.notes:
        db.add(ReviewComment(project_id=project_id, entity_type="TASK", entity_id=task_id, author_id=current_user.id, content=payload.notes))
    db.commit()
    return {"status": "success", "message": f"Task {task.status.lower()}"}


@router.patch("/{project_id}/tasks/{task_id}")
def update_task(
    project_id: int,
    task_id: int,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_access(p, current_user)

    task = db.query(ProjectTask).filter(ProjectTask.id == task_id, ProjectTask.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if payload.submission_notes:
        task.submission_notes = payload.submission_notes
    db.commit()
    return {"status": "success", "message": "Task updated"}


# ------------------------------------------------------------------
# Versioned Solution Proposals
# ------------------------------------------------------------------

def _proposal_out(pr: SolutionProposal) -> SolutionProposalOut:
    return SolutionProposalOut(
        id=pr.id, project_id=pr.project_id, proposed_solution=pr.proposed_solution,
        technical_approach=pr.technical_approach, objectives=pr.objectives,
        feasibility_notes=pr.feasibility_notes, budget_breakdown=pr.budget_breakdown,
        required_resources=pr.required_resources, expected_impact=pr.expected_impact,
        estimated_cost=pr.estimated_cost, timeline_weeks=pr.timeline_weeks, risks=pr.risks,
        safeguarding_notes=pr.safeguarding_notes, maintenance_plan=pr.maintenance_plan,
        measurable_outcomes=pr.measurable_outcomes, status=pr.status, version=pr.version,
        is_current=pr.is_current, faculty_review_notes=pr.faculty_review_notes,
        hei_approval_notes=pr.hei_approval_notes, government_review_notes=pr.government_review_notes,
        revision_requested_reason=pr.revision_requested_reason, is_approved_by_gov=pr.is_approved_by_gov,
        submitted_at=pr.submitted_at
    )


@router.get("/{project_id}/proposals", response_model=List[SolutionProposalOut])
def list_proposals(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    proposals = db.query(SolutionProposal).filter(SolutionProposal.project_id == project_id).order_by(SolutionProposal.version.desc()).all()
    return [_proposal_out(pr) for pr in proposals]


@router.post("/{project_id}/proposals", response_model=SolutionProposalOut, status_code=status.HTTP_201_CREATED)
def submit_proposal(
    project_id: int,
    payload: SolutionProposalCreate,
    submit: bool = Query(True, description="Submit immediately (True) or save as draft (False)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role not in (UserRole.STUDENT, UserRole.FACULTY_MENTOR, UserRole.UNIVERSITY, UserRole.GOVERNMENT_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only the project team may author solution proposals.")
    verify_project_access(p, current_user)

    prior = db.query(SolutionProposal).filter(SolutionProposal.project_id == project_id, SolutionProposal.is_current == True).first()
    if prior:
        prior.is_current = False

    proposal = SolutionProposal(
        project_id=project_id,
        proposed_solution=payload.proposed_solution,
        technical_approach=payload.technical_approach,
        objectives=payload.objectives,
        feasibility_notes=payload.feasibility_notes,
        budget_breakdown=payload.budget_breakdown,
        required_resources=payload.required_resources,
        expected_impact=payload.expected_impact,
        estimated_cost=payload.estimated_cost,
        timeline_weeks=payload.timeline_weeks,
        risks=payload.risks,
        safeguarding_notes=payload.safeguarding_notes,
        maintenance_plan=payload.maintenance_plan,
        measurable_outcomes=payload.measurable_outcomes,
        status=ProposalStatus.DRAFT,
        version=(prior.version + 1) if prior else 1,
        supersedes_id=prior.id if prior else None,
        is_current=True,
        submitted_by_user_id=current_user.id
    )
    db.add(proposal)
    db.flush()

    if submit:
        WorkflowService.transition_proposal(db=db, proposal=proposal, to_status=ProposalStatus.SUBMITTED, actor=current_user, notes="Initial submission")
        if p.challenge:
            WorkflowService.transition_challenge(
                db=db, challenge=p.challenge, to_status=ChallengeStatus.SOLUTION_PROPOSED,
                actor=current_user, remarks=f"Solution proposal v{proposal.version} submitted."
            )
    db.commit()
    db.refresh(proposal)
    return _proposal_out(proposal)


@router.post("/{project_id}/proposals/{proposal_id}/review", response_model=SolutionProposalOut)
def review_proposal(
    project_id: int,
    proposal_id: int,
    payload: ProposalReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.role == UserRole.FACULTY_MENTOR:
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if not faculty or p.faculty_mentor_id != faculty.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You are not the assigned faculty mentor for this project.")
    elif current_user.role == UserRole.UNIVERSITY:
        univ = db.query(University).filter(University.user_id == current_user.id).first()
        if not univ or p.university_id != univ.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Project does not belong to your university.")
    elif current_user.role in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER):
        if p.challenge:
            verify_challenge_jurisdiction(p.challenge, current_user, db, action="review_proposal")

    proposal = db.query(SolutionProposal).filter(SolutionProposal.id == proposal_id, SolutionProposal.project_id == project_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    decision_map = {
        "FACULTY_REVIEWED": ProposalStatus.FACULTY_REVIEWED,
        "HEI_APPROVED": ProposalStatus.HEI_APPROVED,
        "GOVERNMENT_REVIEWED": ProposalStatus.GOVERNMENT_REVIEWED,
        "APPROVED": ProposalStatus.APPROVED,
        "REVISION_REQUESTED": ProposalStatus.REVISION_REQUESTED,
        "REJECTED": ProposalStatus.REJECTED,
    }
    to_status = decision_map.get(payload.decision.upper())
    if not to_status:
        raise HTTPException(status_code=400, detail=f"Invalid decision. Must be one of: {list(decision_map.keys())}")

    WorkflowService.transition_proposal(db=db, proposal=proposal, to_status=to_status, actor=current_user, notes=payload.notes)

    if to_status == ProposalStatus.APPROVED and p.challenge:
        WorkflowService.transition_challenge(
            db=db, challenge=p.challenge, to_status=ChallengeStatus.APPROVED,
            actor=current_user, remarks=f"Solution proposal v{proposal.version} approved by government."
        )

    db.commit()
    db.refresh(proposal)
    return _proposal_out(proposal)


@router.post("/{project_id}/proposals/{proposal_id}/industry-feedback", response_model=SolutionProposalOut)
def industry_feedback_on_proposal(
    project_id: int,
    proposal_id: int,
    payload: IndustryFeedbackRequest,
    current_user: User = Depends(require_permission("collaboration.create")),
    db: Session = Depends(get_db)
):
    # Object-level authorization: requires an active collaboration on this project.
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)

    proposal = db.query(SolutionProposal).filter(SolutionProposal.id == proposal_id, SolutionProposal.project_id == project_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    WorkflowService.transition_proposal(db=db, proposal=proposal, to_status=ProposalStatus.INDUSTRY_FEEDBACK, actor=current_user, notes=payload.notes)
    db.commit()
    db.refresh(proposal)
    return _proposal_out(proposal)


# ------------------------------------------------------------------
# Review Comments
# ------------------------------------------------------------------

@router.post("/{project_id}/comments", response_model=ReviewCommentOut, status_code=status.HTTP_201_CREATED)
def add_review_comment(
    project_id: int,
    payload: ReviewCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)

    entity_type = payload.entity_type.upper()
    if entity_type == "MILESTONE":
        exists = db.query(ProjectMilestone).filter(ProjectMilestone.id == payload.entity_id, ProjectMilestone.project_id == project_id).first()
    elif entity_type == "PROPOSAL":
        exists = db.query(SolutionProposal).filter(SolutionProposal.id == payload.entity_id, SolutionProposal.project_id == project_id).first()
    elif entity_type == "TASK":
        exists = db.query(ProjectTask).filter(ProjectTask.id == payload.entity_id, ProjectTask.project_id == project_id).first()
    else:
        exists = True  # DELIVERABLE / generic entity types validated loosely
    if not exists:
        raise HTTPException(status_code=400, detail="Rejected: Referenced entity does not belong to this project.")

    comment = ReviewComment(project_id=project_id, entity_type=entity_type, entity_id=payload.entity_id, author_id=current_user.id, content=payload.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return ReviewCommentOut(
        id=comment.id, entity_type=comment.entity_type, entity_id=comment.entity_id,
        author_id=comment.author_id, author_name=current_user.full_name, author_role=current_user.role.value,
        content=comment.content, created_at=comment.created_at
    )


@router.get("/{project_id}/comments", response_model=List[ReviewCommentOut])
def list_review_comments(
    project_id: int,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    query = db.query(ReviewComment).filter(ReviewComment.project_id == project_id)
    if entity_type:
        query = query.filter(ReviewComment.entity_type == entity_type.upper())
    if entity_id is not None:
        query = query.filter(ReviewComment.entity_id == entity_id)
    is_moderator = current_user.role in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.UNIVERSITY)
    if not is_moderator:
        query = query.filter(ReviewComment.is_hidden == False)  # noqa: E712
    comments = query.order_by(ReviewComment.created_at.asc()).all()
    out = []
    for c in comments:
        out.append(ReviewCommentOut(
            id=c.id, entity_type=c.entity_type, entity_id=c.entity_id, author_id=c.author_id,
            author_name=c.author.full_name if c.author else None,
            author_role=c.author.role.value if c.author else None,
            content=c.content, created_at=c.created_at
        ))
    return out


# ------------------------------------------------------------------
# Structured Testing Outcomes (Phase 2, Item 15) — gate DEPLOYMENT
# ------------------------------------------------------------------

@router.post("/{project_id}/test-reports", response_model=OutcomeReportOut, status_code=status.HTTP_201_CREATED)
def add_test_report(
    project_id: int,
    payload: OutcomeReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Records a structured field/lab/user-trial testing outcome for this project.
    At least one PASS or PARTIAL report is required before the parent challenge
    can transition to DEPLOYMENT (see WorkflowService.transition_challenge).
    """
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    report = OutcomeReport(
        project_id=project_id,
        reported_by_user_id=current_user.id,
        test_type=payload.test_type,
        outcome=payload.outcome,
        summary=payload.summary,
        tested_at=payload.tested_at or utc_now()
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return OutcomeReportOut(
        id=report.id, project_id=report.project_id, reported_by_user_id=report.reported_by_user_id,
        reported_by_name=current_user.full_name, test_type=report.test_type, outcome=report.outcome,
        summary=report.summary, tested_at=report.tested_at, created_at=report.created_at
    )


@router.get("/{project_id}/test-reports", response_model=List[OutcomeReportOut])
def list_test_reports(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    reports = db.query(OutcomeReport).filter(OutcomeReport.project_id == project_id).order_by(OutcomeReport.tested_at.desc()).all()
    return [
        OutcomeReportOut(
            id=r.id, project_id=r.project_id, reported_by_user_id=r.reported_by_user_id,
            reported_by_name=r.reported_by.full_name if r.reported_by else None,
            test_type=r.test_type, outcome=r.outcome, summary=r.summary,
            tested_at=r.tested_at, created_at=r.created_at
        ) for r in reports
    ]


@router.post("/{project_id}/test-reports/{report_id}/evidence", response_model=EvidenceFileOut)
async def upload_test_report_evidence(
    project_id: int,
    report_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Attaches supporting evidence (lab report, photo, video) to a recorded test outcome."""
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    report = db.query(OutcomeReport).filter(OutcomeReport.id == report_id, OutcomeReport.project_id == project_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test report not found")

    return await storage_service.save_evidence_file(
        file=file, owner_id=current_user.id, entity_type="TEST_REPORT",
        entity_id=report_id, db=db, project_id=project_id
    )


@router.get("/{project_id}/test-reports/{report_id}/evidence", response_model=List[EvidenceFileOut])
def list_test_report_evidence(
    project_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    return db.query(EvidenceFile).filter(
        EvidenceFile.entity_type == "TEST_REPORT", EvidenceFile.entity_id == report_id
    ).order_by(EvidenceFile.version.desc()).all()


# ------------------------------------------------------------------
# Industry Collaboration Offers (Stage 7 extends this substantially)
# ------------------------------------------------------------------

def _agreement_out(c: IndustryCollaboration) -> CollaborationAgreementOut:
    return CollaborationAgreementOut(
        id=c.id, project_id=c.project_id,
        company_name=c.industry.company_name if c.industry else "Industry Partner",
        industry_domain=c.industry.industry_domain if c.industry else "Engineering",
        offer_type=c.offer_type, description=c.description, agreement_status=c.agreement_status,
        scope=c.scope, personnel=c.personnel, in_kind_value=c.in_kind_value, cash_value=c.cash_value,
        currency=c.currency, start_date=c.start_date, end_date=c.end_date, dependencies=c.dependencies,
        data_access_level=c.data_access_level, safety_requirements=c.safety_requirements,
        deliverables=c.deliverables, milestone_id=c.milestone_id, review_notes=c.review_notes,
        conflict_check_notes=c.conflict_check_notes, conflict_declared=c.conflict_declared,
        mou_evidence_object_id=c.mou_evidence_object_id, version=c.version, created_at=c.created_at
    )


@router.post("/{project_id}/collaborations", response_model=CollaborationAgreementOut, status_code=status.HTTP_201_CREATED)
def offer_collaboration(
    project_id: int,
    payload: CollaborationOfferCreate,
    current_user: User = Depends(require_permission("collaboration.create")),
    db: Session = Depends(get_db)
):
    """Structured collaboration offer from a verified industry/startup/MSME/CSR/lab partner."""
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    ind = require_verified_active_partner(current_user, db)

    if payload.milestone_id:
        ms = db.query(ProjectMilestone).filter(ProjectMilestone.id == payload.milestone_id, ProjectMilestone.project_id == project_id).first()
        if not ms:
            raise HTTPException(status_code=400, detail="Rejected: Milestone does not belong to this project.")

    collab = IndustryCollaboration(
        project_id=project_id,
        industry_id=ind.id,
        offer_type=payload.offer_type.value,
        description=payload.description,
        status="Offered",
        agreement_status=AgreementStatus.OFFERED,
        scope=payload.scope,
        personnel=payload.personnel,
        in_kind_value=payload.in_kind_value,
        cash_value=payload.cash_value,
        currency=payload.currency,
        start_date=payload.start_date,
        end_date=payload.end_date,
        dependencies=payload.dependencies,
        data_access_level=payload.data_access_level,
        safety_requirements=payload.safety_requirements,
        deliverables=payload.deliverables,
        milestone_id=payload.milestone_id
    )
    db.add(collab)

    if p.university and p.university.user:
        notification_service.create_notification(
            db,
            user_id=p.university.user.id,
            title="Industry Collaboration Offered!",
            message=f"{ind.company_name} offered {payload.offer_type.value} for project '{p.name}'.",
            reference_id=p.id
        )
    db.commit()
    db.refresh(collab)
    return _agreement_out(collab)


@router.get("/{project_id}/collaborations", response_model=List[CollaborationAgreementOut])
def list_collaborations(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    collabs = db.query(IndustryCollaboration).filter(IndustryCollaboration.project_id == project_id).order_by(IndustryCollaboration.created_at.desc()).all()
    return [_agreement_out(c) for c in collabs]


def _get_collaboration_or_404(db: Session, project_id: int, collab_id: int) -> IndustryCollaboration:
    collab = db.query(IndustryCollaboration).filter(IndustryCollaboration.id == collab_id, IndustryCollaboration.project_id == project_id).first()
    if not collab:
        raise HTTPException(status_code=404, detail="Collaboration agreement not found")
    return collab


@router.post("/{project_id}/collaborations/{collab_id}/review", response_model=CollaborationAgreementOut)
def review_collaboration(
    project_id: int,
    collab_id: int,
    payload: CollaborationReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    collab = _get_collaboration_or_404(db, project_id, collab_id)

    # Object-level authorization: the offering partner may withdraw its own offer;
    # university/government reviewers govern the rest of the lifecycle.
    if current_user.role in (UserRole.INDUSTRY, UserRole.RESEARCH_LAB, UserRole.INNOVATION_HUB):
        ind = db.query(IndustryPartner).filter(IndustryPartner.user_id == current_user.id).first()
        if not ind or collab.industry_id != ind.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: This is not your organization's collaboration offer.")
    elif current_user.role == UserRole.UNIVERSITY:
        univ = db.query(University).filter(University.user_id == current_user.id).first()
        if not univ or p.university_id != univ.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Project does not belong to your university.")
    elif current_user.role in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER):
        if p.challenge:
            verify_challenge_jurisdiction(p.challenge, current_user, db, action="review_collaboration")

    decision_map = {
        "UNDER_REVIEW": AgreementStatus.UNDER_REVIEW, "CONFLICT_CHECK": AgreementStatus.CONFLICT_CHECK,
        "ACCEPTED": AgreementStatus.ACCEPTED, "CONTRACT_RECORDED": AgreementStatus.CONTRACT_RECORDED,
        "ACTIVE": AgreementStatus.ACTIVE, "MILESTONE_LINKED": AgreementStatus.MILESTONE_LINKED,
        "COMPLETED": AgreementStatus.COMPLETED, "DECLINED": AgreementStatus.DECLINED,
        "TERMINATED": AgreementStatus.TERMINATED,
    }
    to_status = decision_map.get(payload.decision.upper())
    if not to_status:
        raise HTTPException(status_code=400, detail=f"Invalid decision. Must be one of: {list(decision_map.keys())}")

    WorkflowService.transition_agreement(
        db=db, collaboration=collab, to_status=to_status, actor=current_user, notes=payload.notes,
        conflict_declared=payload.conflict_declared, mou_evidence_object_id=payload.mou_evidence_object_id
    )
    db.commit()
    db.refresh(collab)
    return _agreement_out(collab)


@router.post("/{project_id}/collaborations/{collab_id}/mou", response_model=CollaborationAgreementOut)
async def upload_collaboration_mou(
    project_id: int,
    collab_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Uploads the MoU/contract as typed evidence (never a client-supplied URL)."""
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    collab = _get_collaboration_or_404(db, project_id, collab_id)
    evidence = await storage_service.save_evidence_file(
        file=file, owner_id=current_user.id, entity_type="COLLABORATION_MOU", entity_id=collab_id, db=db, project_id=project_id
    )
    collab.mou_evidence_object_id = evidence.object_id
    db.commit()
    db.refresh(collab)
    return _agreement_out(collab)


# ------------------------------------------------------------------
# CSR / Funding Governance
# ------------------------------------------------------------------

def _funding_out(f: FundingRecord) -> FundingRecordOut:
    return FundingRecordOut(
        id=f.id, collaboration_id=f.collaboration_id, project_id=f.project_id, industry_id=f.industry_id,
        milestone_id=f.milestone_id, budget_line_item=f.budget_line_item, amount=f.amount, currency=f.currency,
        sanction_authority=f.sanction_authority, agreement_reference=f.agreement_reference,
        disbursement_schedule=f.disbursement_schedule, hold_state=f.hold_state,
        receipt_evidence_object_id=f.receipt_evidence_object_id, utilization_notes=f.utilization_notes,
        payment_integration_reference=f.payment_integration_reference, settlement_status=f.settlement_status,
        payment_confirmed=f.payment_confirmed, version=f.version, created_at=f.created_at
    )


@router.post("/{project_id}/collaborations/{collab_id}/funding", response_model=FundingRecordOut, status_code=status.HTTP_201_CREATED)
def create_funding_record(
    project_id: int,
    collab_id: int,
    payload: FundingRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    collab = _get_collaboration_or_404(db, project_id, collab_id)

    if current_user.role == UserRole.UNIVERSITY:
        univ = db.query(University).filter(University.user_id == current_user.id).first()
        if not univ or p.university_id != univ.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Project does not belong to your university.")
    elif current_user.role in (UserRole.INDUSTRY, UserRole.RESEARCH_LAB, UserRole.INNOVATION_HUB):
        ind = db.query(IndustryPartner).filter(IndustryPartner.user_id == current_user.id).first()
        if not ind or collab.industry_id != ind.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: This is not your organization's collaboration.")
    elif current_user.role not in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Not authorized to record funding for this collaboration.")

    if collab.agreement_status not in (AgreementStatus.ACCEPTED, AgreementStatus.CONTRACT_RECORDED, AgreementStatus.ACTIVE, AgreementStatus.MILESTONE_LINKED, AgreementStatus.COMPLETED):
        raise HTTPException(status_code=400, detail="Funding can only be recorded once the collaboration agreement has been accepted.")

    if payload.milestone_id:
        ms = db.query(ProjectMilestone).filter(ProjectMilestone.id == payload.milestone_id, ProjectMilestone.project_id == project_id).first()
        if not ms:
            raise HTTPException(status_code=400, detail="Rejected: Milestone does not belong to this project.")

    funding = FundingRecord(
        collaboration_id=collab_id, project_id=project_id, industry_id=collab.industry_id,
        milestone_id=payload.milestone_id, budget_line_item=payload.budget_line_item, amount=payload.amount,
        currency=payload.currency, sanction_authority=payload.sanction_authority,
        agreement_reference=payload.agreement_reference, disbursement_schedule=payload.disbursement_schedule,
        created_by_user_id=current_user.id
    )
    db.add(funding)
    db.commit()
    db.refresh(funding)
    return _funding_out(funding)


@router.get("/{project_id}/collaborations/{collab_id}/funding", response_model=List[FundingRecordOut])
def list_funding_records(
    project_id: int,
    collab_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    records = db.query(FundingRecord).filter(FundingRecord.collaboration_id == collab_id, FundingRecord.project_id == project_id).order_by(FundingRecord.created_at.desc()).all()
    return [_funding_out(f) for f in records]


@router.post("/{project_id}/funding/{funding_id}/receipt", response_model=FundingRecordOut)
async def upload_funding_receipt(
    project_id: int,
    funding_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    funding = db.query(FundingRecord).filter(FundingRecord.id == funding_id, FundingRecord.project_id == project_id).first()
    if not funding:
        raise HTTPException(status_code=404, detail="Funding record not found")
    evidence = await storage_service.save_evidence_file(
        file=file, owner_id=current_user.id, entity_type="CSR_RECEIPT", entity_id=funding_id, db=db, project_id=project_id
    )
    funding.receipt_evidence_object_id = evidence.object_id
    db.commit()
    db.refresh(funding)
    return _funding_out(funding)


@router.post("/{project_id}/funding/{funding_id}/action", response_model=FundingRecordOut)
def act_on_funding(
    project_id: int,
    funding_id: int,
    payload: FundingActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role == UserRole.UNIVERSITY:
        univ = db.query(University).filter(University.user_id == current_user.id).first()
        if not univ or p.university_id != univ.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Project does not belong to your university.")
    elif current_user.role in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER):
        if p.challenge:
            verify_challenge_jurisdiction(p.challenge, current_user, db, action="fund_action")
    elif current_user.role not in (UserRole.INDUSTRY, UserRole.RESEARCH_LAB, UserRole.INNOVATION_HUB):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    funding = db.query(FundingRecord).filter(FundingRecord.id == funding_id, FundingRecord.project_id == project_id).first()
    if not funding:
        raise HTTPException(status_code=404, detail="Funding record not found")

    WorkflowService.apply_funding_action(
        db=db, funding=funding, action=payload.action, actor=current_user, notes=payload.notes,
        receipt_evidence_object_id=payload.receipt_evidence_object_id,
        payment_integration_reference=payload.payment_integration_reference
    )
    db.commit()
    db.refresh(funding)
    return _funding_out(funding)


# ------------------------------------------------------------------
# Intellectual Property & Technology Transfer
# ------------------------------------------------------------------

def _ip_out(ip: IPRecord) -> IPRecordOut:
    return IPRecordOut(
        id=ip.id, project_id=ip.project_id, collaboration_id=ip.collaboration_id, record_type=ip.record_type,
        title=ip.title, description=ip.description, background_ip_notes=ip.background_ip_notes,
        foreground_ip_notes=ip.foreground_ip_notes, ownership=ip.ownership, license_terms=ip.license_terms,
        contributor_attributions=ip.contributor_attributions, publication_restrictions=ip.publication_restrictions,
        patent_reference=ip.patent_reference, software_repo_reference=ip.software_repo_reference,
        design_reference=ip.design_reference, startup_spinoff_name=ip.startup_spinoff_name,
        open_source_decision=ip.open_source_decision, government_benefit_terms=ip.government_benefit_terms,
        status=ip.status, consents=[
            IPConsentRecordOut(id=c.id, party_user_id=c.party_user_id, party_role=c.party_role, status=c.status, notes=c.notes, responded_at=c.responded_at)
            for c in ip.consents
        ], created_at=ip.created_at
    )


@router.post("/{project_id}/ip-records", response_model=IPRecordOut, status_code=status.HTTP_201_CREATED)
def create_ip_record(
    project_id: int,
    payload: IPRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_access(p, current_user)

    import json as _json
    ip = IPRecord(
        project_id=project_id, collaboration_id=payload.collaboration_id, record_type=payload.record_type,
        title=payload.title, description=payload.description, background_ip_notes=payload.background_ip_notes,
        foreground_ip_notes=payload.foreground_ip_notes, ownership=payload.ownership, license_terms=payload.license_terms,
        contributor_attributions=_json.dumps(payload.contributor_attributions) if payload.contributor_attributions else None,
        publication_restrictions=payload.publication_restrictions, patent_reference=payload.patent_reference,
        software_repo_reference=payload.software_repo_reference, design_reference=payload.design_reference,
        startup_spinoff_name=payload.startup_spinoff_name, open_source_decision=payload.open_source_decision,
        government_benefit_terms=payload.government_benefit_terms, status="PENDING_CONSENT",
        created_by_user_id=current_user.id
    )
    db.add(ip)
    db.flush()

    party_ids = set(payload.consent_party_user_ids or [])
    party_ids.add(current_user.id)
    for uid in party_ids:
        party_user = db.query(User).filter(User.id == uid).first()
        if not party_user:
            continue
        db.add(IPConsentRecord(
            ip_record_id=ip.id, party_user_id=uid, party_role=party_user.role.value,
            status=IPConsentStatus.ACCEPTED if uid == current_user.id else IPConsentStatus.PENDING,
            responded_at=utc_now() if uid == current_user.id else None
        ))

    db.commit()
    db.refresh(ip)
    return _ip_out(ip)


@router.get("/{project_id}/ip-records", response_model=List[IPRecordOut])
def list_ip_records(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)
    records = db.query(IPRecord).filter(IPRecord.project_id == project_id).order_by(IPRecord.created_at.desc()).all()
    return [_ip_out(ip) for ip in records]


@router.post("/{project_id}/ip-records/{ip_id}/consent", response_model=IPConsentRecordOut)
def respond_ip_consent(
    project_id: int,
    ip_id: int,
    payload: IPConsentRespond,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = db.query(IPRecord).filter(IPRecord.id == ip_id, IPRecord.project_id == project_id).first()
    if not ip:
        raise HTTPException(status_code=404, detail="IP record not found")
    consent = db.query(IPConsentRecord).filter(IPConsentRecord.ip_record_id == ip_id, IPConsentRecord.party_user_id == current_user.id).first()
    if not consent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You are not a listed party on this IP record.")

    WorkflowService.respond_ip_consent(db=db, consent=consent, actor=current_user, decision=payload.status, notes=payload.notes)
    db.commit()
    db.refresh(consent)
    return IPConsentRecordOut(id=consent.id, party_user_id=consent.party_user_id, party_role=consent.party_role, status=consent.status, notes=consent.notes, responded_at=consent.responded_at)


@router.get("/ip-consents/mine", response_model=List[IPConsentRecordOut])
def my_pending_ip_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consents = db.query(IPConsentRecord).filter(
        IPConsentRecord.party_user_id == current_user.id,
        IPConsentRecord.status == IPConsentStatus.PENDING
    ).order_by(IPConsentRecord.created_at.desc()).all()
    return [IPConsentRecordOut(id=c.id, party_user_id=c.party_user_id, party_role=c.party_role, status=c.status, notes=c.notes, responded_at=c.responded_at) for c in consents]


# ------------------------------------------------------------------
# Comment moderation (Stage 7)
# ------------------------------------------------------------------

@router.post("/{project_id}/comments/{comment_id}/moderate")
def moderate_comment(
    project_id: int,
    comment_id: int,
    payload: ModerationActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.UNIVERSITY):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only government or university staff may moderate communication.")
    comment = db.query(ReviewComment).filter(ReviewComment.id == comment_id, ReviewComment.project_id == project_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    action_upper = payload.action.upper()
    if action_upper == "FLAG":
        comment.is_flagged = True
    elif action_upper == "HIDE":
        comment.is_hidden = True
    elif action_upper == "RESTORE":
        comment.is_hidden = False
        comment.is_flagged = False
    else:
        raise HTTPException(status_code=400, detail="Action must be one of: FLAG, HIDE, RESTORE")

    comment.moderated_by_user_id = current_user.id
    comment.moderation_action = action_upper
    comment.moderation_notes = payload.notes
    db.commit()
    return {"status": "success", "message": f"Comment {action_upper.lower()}ed"}


# ------------------------------------------------------------------
# Stage 8: Project Closure Gate & Precondition Evaluation
# ------------------------------------------------------------------

@router.get("/{project_id}/closure-preconditions", response_model=ProjectClosureEvaluationOut)
def evaluate_project_closure_preconditions(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates all 9 preconditions required for formal, accountable project closure.
    Identifies any missing milestones, unverified deliverables, unheld funding, or missing metrics.
    """
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_project_membership(project_id=project_id, current_user=current_user, db=db)

    evaluation = WorkflowService.evaluate_closure_preconditions(db=db, project_id=project_id)
    return ProjectClosureEvaluationOut(**evaluation)


@router.post("/{project_id}/close", response_model=ProjectClosureRecordOut)
def close_project(
    project_id: int,
    payload: ProjectClosureRequest,
    current_user: User = Depends(require_permission("project.close")),
    db: Session = Depends(get_db)
):
    """
    Enforces the final project and challenge closure gate.
    Requires all 9 preconditions satisfied, authorized government actor without conflicts of interest,
    records an immutable ProjectClosureRecord, and transitions Project and Challenge status.
    """
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.role not in (UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only government officers and administrators may execute accountable closure."
        )

    if p.challenge:
        verify_challenge_jurisdiction(p.challenge, current_user, db, action="close_project")

    closure_record = WorkflowService.close_project_and_challenge(
        db=db,
        project_id=project_id,
        actor=current_user,
        payload=payload.model_dump()
    )
    return closure_record

