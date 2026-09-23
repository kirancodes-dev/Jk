from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import Faculty, Project, ProjectMilestone, MilestoneStatus, User, UserRole, University, TeamInvitation, TeamInvitationStatus
from backend.app.schemas.schemas import ProjectOut, TeamInvitationOut
from backend.app.routers.deps import get_current_user, require_permission
from backend.app.routers.projects import _invitation_out, _project_out

router = APIRouter(prefix="/faculty", tags=["Faculty"])

@router.get("/dashboard")
def get_faculty_dashboard(
    current_user: User = Depends(require_permission("project.mentor")),
    db: Session = Depends(get_db)
):
    faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty mentor profile not found for authenticated account."
        )

    projects = db.query(Project).filter(Project.faculty_mentor_id == faculty.id).all()

    project_ids = [p.id for p in projects]
    pending_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id.in_(project_ids),
        ProjectMilestone.status == MilestoneStatus.SUBMITTED
    ).all() if project_ids else []

    pending_invitations = db.query(TeamInvitation).filter(
        TeamInvitation.faculty_id == faculty.id,
        TeamInvitation.status == TeamInvitationStatus.PENDING
    ).all()

    total_students = sum(len([m for m in p.members if m.is_active]) for p in projects)

    return {
        "faculty_name": faculty.user.full_name if faculty.user else "Faculty Mentor",
        "designation": faculty.designation or "Professor",
        "expertise": faculty.expertise or "Engineering",
        "mentored_projects_count": len(projects),
        "total_mentored_students": total_students,
        "pending_milestones_count": len(pending_milestones),
        "pending_invitations_count": len(pending_invitations),
        "projects": [
            {
                "id": p.id,
                "challenge_id": p.challenge_id,
                "name": p.name,
                "challenge_title": p.challenge.title if p.challenge else "Challenge",
                "progress_percentage": p.progress_percentage,
                "current_stage": p.current_stage,
                "student_count": len([m for m in p.members if m.is_active])
            } for p in projects
        ],
        "pending_milestones": [
            {
                "id": ms.id,
                "project_id": ms.project_id,
                "title": ms.title,
                "weight_pct": ms.weight_pct,
                "status": ms.status.value
            } for ms in pending_milestones
        ],
        "pending_invitations": [_invitation_out(inv) for inv in pending_invitations]
    }


@router.get("/team-invitations", response_model=List[TeamInvitationOut])
def get_faculty_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
    if not faculty:
        return []
    invitations = db.query(TeamInvitation).filter(TeamInvitation.faculty_id == faculty.id).order_by(TeamInvitation.created_at.desc()).all()
    return [_invitation_out(inv) for inv in invitations]


@router.get("/mentored-projects", response_model=List[ProjectOut])
def get_mentored_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
    if not faculty:
        return []
    projects = db.query(Project).filter(Project.faculty_mentor_id == faculty.id).all()
    return [_project_out(p) for p in projects]


@router.post("/approve-milestone/{milestone_id}")
def approve_milestone(
    milestone_id: int,
    current_user: User = Depends(require_permission("milestone.approve")),
    db: Session = Depends(get_db)
):
    """
    Legacy convenience endpoint. Prefer POST /projects/{project_id}/milestones/{id}/review,
    which enforces evidence-backed submission and mandatory review comments.
    """
    ms = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    if not ms:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")
    if ms.status != MilestoneStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Milestone must be SUBMITTED with deliverable evidence before approval (current status: {ms.status.value})."
        )

    project = db.query(Project).filter(Project.id == ms.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.FACULTY_MENTOR:
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if not faculty or project.faculty_mentor_id != faculty.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You are not the assigned faculty mentor for this project."
            )
    elif current_user.role == UserRole.UNIVERSITY:
        univ = db.query(University).filter(University.user_id == current_user.id).first()
        if not univ or project.university_id != univ.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Project does not belong to your university."
            )

    from backend.app.services.workflow_service import WorkflowService
    WorkflowService.review_milestone(db=db, milestone=ms, decision="APPROVE", actor=current_user, notes="Approved by faculty mentor")
    db.commit()
    return {"status": "success", "message": f"Milestone '{ms.title}' approved by faculty mentor"}
