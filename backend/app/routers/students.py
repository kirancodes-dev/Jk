from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import Student, Project, ProjectMember, ProjectTask, User
from backend.app.schemas.schemas import ProjectOut, TaskOut, TaskUpdate
from backend.app.routers.deps import get_current_user

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/dashboard")
def get_student_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        student = db.query(Student).first()
        
    student_id = student.id if student else 1
    memberships = db.query(ProjectMember).filter(ProjectMember.student_id == student_id).all()
    project_ids = [m.project_id for m in memberships]
    
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all() if project_ids else []
    tasks = db.query(ProjectTask).filter(ProjectTask.assigned_to_student_id == student_id).all()
    
    pending_tasks = [t for t in tasks if not t.is_completed]
    completed_tasks = [t for t in tasks if t.is_completed]
    
    return {
        "student_name": student.user.full_name if student and student.user else "Student",
        "roll_number": student.roll_number if student else "BTECH/2023",
        "degree": student.degree if student else "B.Tech",
        "skills": student.skills.split(",") if student and student.skills else ["Python", "IoT", "Flutter"],
        "active_projects_count": len(projects),
        "pending_tasks_count": len(pending_tasks),
        "completed_tasks_count": len(completed_tasks),
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
                "title": t.title,
                "project_name": t.project.name if t.project else "Project",
                "is_completed": t.is_completed,
                "submission_notes": t.submission_notes
            } for t in tasks
        ]
    }

@router.get("/my-projects", response_model=List[ProjectOut])
def get_my_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        student = db.query(Student).first()
        
    student_id = student.id if student else 1
    memberships = db.query(ProjectMember).filter(ProjectMember.student_id == student_id).all()
    project_ids = [m.project_id for m in memberships]
    
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all() if project_ids else []
    out = []
    for p in projects:
        out.append(ProjectOut(
            id=p.id,
            challenge_id=p.challenge_id,
            challenge_title=p.challenge.title if p.challenge else "Societal Challenge",
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

@router.post("/submit-task/{task_id}")
def submit_task_work(
    task_id: int,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.is_completed = True if payload.is_completed is None else payload.is_completed
    if payload.submission_notes:
        task.submission_notes = payload.submission_notes
    if payload.submission_attachment:
        task.submission_attachment = payload.submission_attachment
        
    db.commit()
    return {"status": "success", "message": "Work submitted successfully for mentor review"}
