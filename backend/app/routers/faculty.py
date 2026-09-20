from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import Faculty, Project, ProjectMilestone, MilestoneStatus, User
from backend.app.schemas.schemas import ProjectOut
from backend.app.routers.deps import get_current_user

router = APIRouter(prefix="/faculty", tags=["Faculty"])

@router.get("/dashboard")
def get_faculty_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
    if not faculty:
        faculty = db.query(Faculty).first()
        
    faculty_id = faculty.id if faculty else 1
    projects = db.query(Project).filter(Project.faculty_mentor_id == faculty_id).all()
    
    project_ids = [p.id for p in projects]
    pending_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id.in_(project_ids),
        ProjectMilestone.approved_by_faculty == False,
        ProjectMilestone.completion_percentage > 0
    ).all() if project_ids else []
    
    total_students = sum(len(p.members) for p in projects)
    
    return {
        "faculty_name": faculty.user.full_name if faculty and faculty.user else "Faculty Mentor",
        "designation": faculty.designation if faculty else "Professor",
        "expertise": faculty.expertise if faculty else "Engineering",
        "mentored_projects_count": len(projects),
        "total_mentored_students": total_students,
        "pending_milestones_count": len(pending_milestones),
        "projects": [
            {
                "id": p.id,
                "challenge_id": p.challenge_id,
                "name": p.name,
                "challenge_title": p.challenge.title if p.challenge else "Challenge",
                "progress_percentage": p.progress_percentage,
                "current_stage": p.current_stage,
                "student_count": len(p.members)
            } for p in projects
        ],
        "pending_milestones": [
            {
                "id": ms.id,
                "project_id": ms.project_id,
                "title": ms.title,
                "completion_percentage": ms.completion_percentage,
                "status": ms.status.value
            } for ms in pending_milestones
        ]
    }

@router.post("/approve-milestone/{milestone_id}")
def approve_milestone(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ms = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    if not ms:
        raise HTTPException(status_code=404, detail="Milestone not found")

    # Object-level authorization: ensure faculty is mentor of the milestone's project or admin
    if current_user.role != "GOVERNMENT_ADMIN":
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if not faculty:
            raise HTTPException(status_code=403, detail="Only verified faculty mentors can approve milestones")

        project = db.query(Project).filter(Project.id == ms.project_id).first()
        if not project or (project.faculty_mentor_id != faculty.id and project.university_id != faculty.university_id):
            raise HTTPException(
                status_code=403,
                detail="Forbidden: You are not the assigned mentor for this project."
            )

    ms.approved_by_faculty = True
    ms.approved_at = datetime.now(timezone.utc)
    ms.status = MilestoneStatus.APPROVED
    db.commit()
    return {"status": "success", "message": f"Milestone '{ms.title}' approved by faculty mentor"}
