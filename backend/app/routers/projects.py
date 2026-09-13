from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import (
    Project, ProjectMember, ProjectMilestone, ProjectTask, SolutionProposal,
    IndustryCollaboration, Challenge, University, Faculty, Student, User,
    IndustryPartner, ChallengeStatus, MilestoneStatus, StatusHistory
)
from backend.app.schemas.schemas import (
    ProjectCreate, ProjectOut, ProjectDetailOut, ProjectMemberOut, MilestoneCreate,
    MilestoneUpdate, MilestoneOut, TaskCreate, TaskUpdate, TaskOut,
    SolutionProposalCreate, SolutionProposalOut, IndustryCollaborationCreate,
    IndustryCollaborationOut
)
from backend.app.services.notification_service import notification_service
from backend.app.routers.deps import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    out = []
    for p in projects:
        out.append(ProjectOut(
            id=p.id,
            challenge_id=p.challenge_id,
            challenge_title=p.challenge.title if p.challenge else "Societal Challenge",
            university_id=p.university_id,
            university_name=p.university.institution_name if p.university else "University",
            faculty_mentor_name=p.faculty_mentor.user.full_name if p.faculty_mentor and p.faculty_mentor.user else "Faculty Mentor",
            name=p.name,
            description=p.description,
            progress_percentage=p.progress_percentage,
            current_stage=p.current_stage,
            created_at=p.created_at
        ))
    return out

@router.post("", response_model=ProjectDetailOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    challenge = db.query(Challenge).filter(Challenge.id == payload.challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
        
    univ = db.query(University).filter(University.user_id == current_user.id).first()
    if not univ:
        # Fallback to challenge's assigned university or first university
        if challenge.assigned_university_id:
            univ = db.query(University).filter(University.id == challenge.assigned_university_id).first()
        else:
            univ = db.query(University).first()
            
    univ_id = univ.id if univ else 1
    
    project = Project(
        challenge_id=payload.challenge_id,
        university_id=univ_id,
        faculty_mentor_id=payload.faculty_mentor_id,
        name=payload.name,
        description=payload.description,
        objectives=payload.objectives,
        expected_outcome=payload.expected_outcome,
        required_skills=payload.required_skills,
        timeline_months=payload.timeline_months,
        progress_percentage=10.0,
        current_stage="Research & Team Formation"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Assign student members
    if payload.student_ids:
        for s_id in payload.student_ids:
            member = ProjectMember(
                project_id=project.id,
                student_id=s_id,
                role_in_team="Multidisciplinary Researcher"
            )
            db.add(member)
    else:
        # Add default student for seamless demo
        first_student = db.query(Student).first()
        if first_student:
            db.add(ProjectMember(
                project_id=project.id,
                student_id=first_student.id,
                role_in_team="Technical Lead & Developer"
            ))
            
    # Create standard initial milestones
    m1 = ProjectMilestone(project_id=project.id, title="Problem Validation & Field Survey", description="Engage rural stakeholders and collect field parameters.", completion_percentage=100.0, status=MilestoneStatus.APPROVED, approved_by_faculty=True)
    m2 = ProjectMilestone(project_id=project.id, title="Technical Architecture & Design", description="Draft engineering schematics and bill of materials.", completion_percentage=40.0, status=MilestoneStatus.IN_PROGRESS)
    m3 = ProjectMilestone(project_id=project.id, title="Prototype Fabrication & Lab Testing", description="Assemble working proof of concept in university lab.", completion_percentage=0.0, status=MilestoneStatus.NOT_STARTED)
    m4 = ProjectMilestone(project_id=project.id, title="Field Deployment & Pilot Testing", description="Deploy solution in the village and evaluate impact.", completion_percentage=0.0, status=MilestoneStatus.NOT_STARTED)
    db.add_all([m1, m2, m3, m4])
    
    # Update challenge status
    challenge.status = ChallengeStatus.TEAM_FORMED
    db.add(StatusHistory(
        challenge_id=challenge.id,
        from_status="UNIVERSITY_ASSIGNED",
        to_status="TEAM_FORMED",
        updated_by=f"{current_user.full_name} (University)",
        remarks=f"Project '{project.name}' initialized with multidisciplinary team."
    ))
    db.commit()
    return get_project_detail(project.id, db)

@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
        
    members_out = []
    for m in p.members:
        st = m.student
        if st and st.user:
            members_out.append(ProjectMemberOut(
                student_id=st.id,
                student_name=st.user.full_name,
                department_name=st.department.name if st.department else "Engineering",
                role_in_team=m.role_in_team,
                skills=st.skills
            ))
            
    milestones_out = [
        MilestoneOut(
            id=ms.id,
            title=ms.title,
            description=ms.description,
            completion_percentage=ms.completion_percentage,
            status=ms.status,
            due_date=ms.due_date,
            approved_by_faculty=ms.approved_by_faculty
        ) for ms in p.milestones
    ]
    
    tasks_out = []
    for t in p.tasks:
        st_name = t.assigned_student.user.full_name if t.assigned_student and t.assigned_student.user else None
        tasks_out.append(TaskOut(
            id=t.id,
            title=t.title,
            assigned_to_student_id=t.assigned_to_student_id,
            assigned_student_name=st_name,
            is_completed=t.is_completed,
            submission_notes=t.submission_notes,
            submission_attachment=t.submission_attachment
        ))
        
    proposals_out = [
        SolutionProposalOut(
            id=prop.id,
            proposed_solution=prop.proposed_solution,
            technical_approach=prop.technical_approach,
            required_resources=prop.required_resources,
            expected_impact=prop.expected_impact,
            estimated_cost=prop.estimated_cost,
            timeline_weeks=prop.timeline_weeks,
            is_approved_by_gov=prop.is_approved_by_gov
        ) for prop in p.proposals
    ]
    
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
    
    return ProjectDetailOut(
        id=p.id,
        challenge_id=p.challenge_id,
        challenge_title=p.challenge.title if p.challenge else "Societal Challenge",
        university_id=p.university_id,
        university_name=p.university.institution_name if p.university else "University",
        faculty_mentor_name=p.faculty_mentor.user.full_name if p.faculty_mentor and p.faculty_mentor.user else None,
        name=p.name,
        description=p.description,
        objectives=p.objectives,
        expected_outcome=p.expected_outcome,
        required_skills=p.required_skills,
        progress_percentage=p.progress_percentage,
        current_stage=p.current_stage,
        created_at=p.created_at,
        members=members_out,
        milestones=milestones_out,
        tasks=tasks_out,
        proposals=proposals_out,
        collaborations=collabs_out
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
        
    ms = ProjectMilestone(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        completion_percentage=payload.completion_percentage,
        due_date=payload.due_date,
        status=MilestoneStatus.IN_PROGRESS if payload.completion_percentage > 0 else MilestoneStatus.NOT_STARTED
    )
    db.add(ms)
    db.commit()
    db.refresh(ms)
    return ms

@router.patch("/{project_id}/milestones/{milestone_id}")
def update_milestone(
    project_id: int,
    milestone_id: int,
    payload: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ms = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == milestone_id,
        ProjectMilestone.project_id == project_id
    ).first()
    if not ms:
        raise HTTPException(status_code=404, detail="Milestone not found")
        
    if payload.completion_percentage is not None:
        ms.completion_percentage = payload.completion_percentage
        if payload.completion_percentage >= 100.0:
            ms.status = MilestoneStatus.COMPLETED
    if payload.status:
        ms.status = payload.status
    if payload.approved_by_faculty is not None:
        ms.approved_by_faculty = payload.approved_by_faculty
        if payload.approved_by_faculty:
            ms.approved_at = datetime.now(timezone.utc)
            
    # Recalculate project progress
    all_ms = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).all()
    if all_ms:
        avg_prog = sum(m.completion_percentage for m in all_ms) / len(all_ms)
        p = db.query(Project).filter(Project.id == project_id).first()
        p.progress_percentage = round(avg_prog, 1)
        if avg_prog >= 100.0 and p.challenge:
            p.challenge.status = ChallengeStatus.RESOLVED
            db.add(StatusHistory(
                challenge_id=p.challenge_id,
                from_status=p.challenge.status.value,
                to_status="RESOLVED",
                updated_by=current_user.full_name,
                remarks="All project milestones completed and validated. Challenge successfully RESOLVED."
            ))
            
    db.commit()
    return {"status": "success", "message": "Milestone updated"}

@router.post("/{project_id}/tasks", response_model=TaskOut)
def add_task(
    project_id: int,
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = ProjectTask(
        project_id=project_id,
        title=payload.title,
        assigned_to_student_id=payload.assigned_to_student_id,
        due_date=payload.due_date,
        is_completed=False
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskOut(
        id=task.id,
        title=task.title,
        assigned_to_student_id=task.assigned_to_student_id,
        assigned_student_name=None,
        is_completed=task.is_completed
    )

@router.patch("/{project_id}/tasks/{task_id}")
def update_task(
    project_id: int,
    task_id: int,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(ProjectTask).filter(ProjectTask.id == task_id, ProjectTask.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if payload.is_completed is not None:
        task.is_completed = payload.is_completed
    if payload.submission_notes:
        task.submission_notes = payload.submission_notes
    if payload.submission_attachment:
        task.submission_attachment = payload.submission_attachment
        
    db.commit()
    return {"status": "success", "message": "Task updated"}

@router.post("/{project_id}/proposals", response_model=SolutionProposalOut)
def submit_proposal(
    project_id: int,
    payload: SolutionProposalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proposal = SolutionProposal(
        project_id=project_id,
        proposed_solution=payload.proposed_solution,
        technical_approach=payload.technical_approach,
        required_resources=payload.required_resources,
        expected_impact=payload.expected_impact,
        estimated_cost=payload.estimated_cost,
        timeline_weeks=payload.timeline_weeks
    )
    db.add(proposal)
    
    # Advance challenge stage
    p = db.query(Project).filter(Project.id == project_id).first()
    if p and p.challenge:
        p.challenge.status = ChallengeStatus.SOLUTION_PROPOSED
        db.add(StatusHistory(
            challenge_id=p.challenge_id,
            from_status="TEAM_FORMED",
            to_status="SOLUTION_PROPOSED",
            updated_by=current_user.full_name,
            remarks=f"Solution proposal submitted: {payload.proposed_solution[:60]}..."
        ))
    db.commit()
    db.refresh(proposal)
    return proposal

@router.post("/{project_id}/collaborations", response_model=IndustryCollaborationOut)
def offer_collaboration(
    project_id: int,
    payload: IndustryCollaborationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ind = db.query(IndustryPartner).filter(IndustryPartner.user_id == current_user.id).first()
    if not ind:
        ind = db.query(IndustryPartner).first()
    ind_id = ind.id if ind else 1
    
    collab = IndustryCollaboration(
        project_id=project_id,
        industry_id=ind_id,
        offer_type=payload.offer_type,
        description=payload.description,
        status="Active"
    )
    db.add(collab)
    
    # Notify university & student leads
    p = db.query(Project).filter(Project.id == project_id).first()
    if p and p.university and p.university.user:
        notification_service.create_notification(
            db,
            user_id=p.university.user.id,
            title="Industry Collaboration Offered!",
            message=f"{ind.company_name if ind else 'Industry'} offered {payload.offer_type} for project '{p.name}'.",
            reference_id=p.id
        )
    db.commit()
    db.refresh(collab)
    return IndustryCollaborationOut(
        id=collab.id,
        company_name=ind.company_name if ind else "Industry Partner",
        industry_domain=ind.industry_domain if ind else "Corporate CSR",
        offer_type=collab.offer_type,
        description=collab.description,
        status=collab.status
    )
