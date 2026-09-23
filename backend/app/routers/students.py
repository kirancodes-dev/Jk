from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import (
    Student, Project, ProjectMember, ProjectTask, User, UserRole,
    TeamInvitation, TeamInvitationStatus, EvidenceFile
)
from backend.app.schemas.schemas import ProjectOut, TaskOut, TaskUpdate, TeamInvitationOut
from backend.app.routers.deps import get_current_user, require_permission
from backend.app.routers.projects import _invitation_out, _project_out

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/dashboard")
def get_student_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found for authenticated account."
        )

    memberships = db.query(ProjectMember).filter(ProjectMember.student_id == student.id, ProjectMember.is_active == True).all()
    project_ids = [m.project_id for m in memberships]

    projects = db.query(Project).filter(Project.id.in_(project_ids)).all() if project_ids else []
    tasks = db.query(ProjectTask).filter(ProjectTask.assigned_to_student_id == student.id).all()

    pending_tasks = [t for t in tasks if not t.is_completed]
    completed_tasks = [t for t in tasks if t.is_completed]

    pending_invitations = db.query(TeamInvitation).filter(
        TeamInvitation.student_id == student.id,
        TeamInvitation.status == TeamInvitationStatus.PENDING
    ).all()

    return {
        "student_name": student.user.full_name if student.user else "Student",
        "roll_number": student.roll_number or "BTECH/2023",
        "degree": student.degree or "B.Tech",
        "skills": student.skills.split(",") if student.skills else ["Python", "IoT", "Flutter"],
        "active_projects_count": len(projects),
        "pending_tasks_count": len(pending_tasks),
        "completed_tasks_count": len(completed_tasks),
        "pending_invitations_count": len(pending_invitations),
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "challenge_title": p.challenge.title if p.challenge else "Societal Problem",
                "progress_percentage": p.progress_percentage,
                "current_stage": p.current_stage
            } for p in projects
        ],
        "tasks": [
            {
                "id": t.id,
                "project_id": t.project_id,
                "title": t.title,
                "project_name": t.project.name if t.project else "Project",
                "status": t.status,
                "is_completed": t.is_completed,
                "submission_notes": t.submission_notes
            } for t in tasks
        ],
        "pending_invitations": [_invitation_out(inv) for inv in pending_invitations]
    }


@router.get("/team-invitations", response_model=List[TeamInvitationOut])
def get_student_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        return []
    invitations = db.query(TeamInvitation).filter(TeamInvitation.student_id == student.id).order_by(TeamInvitation.created_at.desc()).all()
    return [_invitation_out(inv) for inv in invitations]


@router.get("/my-projects", response_model=List[ProjectOut])
def get_my_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        return []

    memberships = db.query(ProjectMember).filter(ProjectMember.student_id == student.id, ProjectMember.is_active == True).all()
    project_ids = [m.project_id for m in memberships]

    projects = db.query(Project).filter(Project.id.in_(project_ids)).all() if project_ids else []
    return [_project_out(p) for p in projects]


@router.get("/my-tasks", response_model=List[TaskOut])
def get_my_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        return []
    tasks = db.query(ProjectTask).filter(ProjectTask.assigned_to_student_id == student.id).all()
    out = []
    for t in tasks:
        out.append(TaskOut(
            id=t.id,
            title=t.title,
            milestone_id=t.milestone_id,
            assigned_to_student_id=t.assigned_to_student_id,
            assigned_student_name=t.assigned_student.user.full_name if t.assigned_student and t.assigned_student.user else None,
            status=t.status,
            is_completed=t.is_completed,
            submission_notes=t.submission_notes
        ))
    return out

@router.post("/submit-task/{task_id}")
def submit_task_work(
    task_id: int,
    payload: TaskUpdate,
    current_user: User = Depends(require_permission("task.complete")),
    db: Session = Depends(get_db)
):
    """
    Records submission notes for a task. Typed evidence must be uploaded first via
    POST /projects/{project_id}/tasks/{task_id}/evidence — this endpoint does not
    accept arbitrary file URLs.
    """
    task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Object-level authorization: ensure student is assigned to task or project member
    if current_user.role != UserRole.GOVERNMENT_ADMIN:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only registered students can submit task work")

        is_assigned = (task.assigned_to_student_id == student.id)
        is_project_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == task.project_id,
            ProjectMember.student_id == student.id,
            ProjectMember.is_active == True
        ).first()

        if not (is_assigned or is_project_member):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You are not assigned to this task or this project's research team"
            )

    has_evidence = db.query(EvidenceFile).filter(
        EvidenceFile.entity_type == "TASK_SUBMISSION",
        EvidenceFile.entity_id == task.id,
        EvidenceFile.is_current == True
    ).first()
    if not has_evidence:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload typed evidence via /projects/{project_id}/tasks/{task_id}/evidence before marking this task submitted."
        )

    task.status = "SUBMITTED"
    if payload.submission_notes:
        task.submission_notes = payload.submission_notes

    db.commit()
    return {"status": "success", "message": "Work submitted successfully for mentor review"}
