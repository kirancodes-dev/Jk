import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    CITIZEN = "CITIZEN"
    UNIVERSITY = "UNIVERSITY"
    STUDENT = "STUDENT"
    FACULTY_MENTOR = "FACULTY_MENTOR"
    INDUSTRY = "INDUSTRY"
    GOVERNMENT_ADMIN = "GOVERNMENT_ADMIN"

class ChallengePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ChallengeStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    AI_ANALYSIS = "AI_ANALYSIS"
    UNDER_REVIEW = "UNDER_REVIEW"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
    DUPLICATE = "DUPLICATE"
    VALIDATED = "VALIDATED"
    UNIVERSITY_ASSIGNED = "UNIVERSITY_ASSIGNED"
    TEAM_FORMED = "TEAM_FORMED"
    SOLUTION_PROPOSED = "SOLUTION_PROPOSED"
    APPROVED = "APPROVED"
    PROTOTYPE = "PROTOTYPE"
    FIELD_TESTING = "FIELD_TESTING"
    DEPLOYMENT = "DEPLOYMENT"
    IN_PROGRESS = "IN_PROGRESS"
    FIELD_VERIFICATION = "FIELD_VERIFICATION"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"

class MilestoneStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"

class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    state = Column(String(100), default="Jharkhand", nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    total_population = Column(Integer, nullable=True)
    rural_population_pct = Column(Float, nullable=True)

    challenges = relationship("ChallengeLocation", back_populates="district")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False, index=True)
    admin_tier = Column(String(50), default="STATE")  # PANCHAYAT, BLOCK, DISTRICT, STATE
    jurisdiction_name = Column(String(255), default="Jharkhand State")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    citizen_profile = relationship("Citizen", back_populates="user", uselist=False, cascade="all, delete-orphan")
    university_profile = relationship("University", back_populates="user", uselist=False, cascade="all, delete-orphan")
    student_profile = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    faculty_profile = relationship("Faculty", back_populates="user", uselist=False, cascade="all, delete-orphan")
    industry_profile = relationship("IndustryPartner", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")

class Citizen(Base):
    __tablename__ = "citizens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    address = Column(String(255), nullable=True)
    district_name = Column(String(100), nullable=True)
    block_name = Column(String(100), nullable=True)
    village_or_city = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)

    user = relationship("User", back_populates="citizen_profile")
    challenges = relationship("Challenge", back_populates="citizen")

class University(Base):
    __tablename__ = "universities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    institution_name = Column(String(255), nullable=False, index=True)
    district_name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    has_incubation_center = Column(Boolean, default=True)
    has_innovation_center = Column(Boolean, default=True)
    facilities_description = Column(Text, nullable=True)
    nirf_ranking = Column(Integer, nullable=True)

    user = relationship("User", back_populates="university_profile")
    departments = relationship("Department", back_populates="university", cascade="all, delete-orphan")
    expertise_areas = relationship("UniversityExpertise", back_populates="university", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="university")
    assigned_challenges = relationship("Challenge", back_populates="assigned_university")

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False)
    name = Column(String(150), nullable=False)
    head_of_department = Column(String(150), nullable=True)

    university = relationship("University", back_populates="departments")
    faculty_members = relationship("Faculty", back_populates="department")
    students = relationship("Student", back_populates="department")

class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    designation = Column(String(100), nullable=True)
    expertise = Column(String(255), nullable=True)
    research_interests = Column(Text, nullable=True)
    experience_years = Column(Integer, default=5)

    user = relationship("User", back_populates="faculty_profile")
    university = relationship("University")
    department = relationship("Department", back_populates="faculty_members")
    mentored_projects = relationship("Project", back_populates="faculty_mentor")

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    roll_number = Column(String(50), nullable=True)
    degree = Column(String(100), default="B.Tech")
    year_of_study = Column(Integer, default=3)
    skills = Column(String(500), nullable=True)  # Comma separated

    user = relationship("User", back_populates="student_profile")
    university = relationship("University")
    department = relationship("Department", back_populates="students")
    project_memberships = relationship("ProjectMember", back_populates="student")

class IndustryPartner(Base):
    __tablename__ = "industry_partners"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    industry_domain = Column(String(150), nullable=False)
    contact_person = Column(String(150), nullable=True)
    website = Column(String(255), nullable=True)
    csr_focus_areas = Column(Text, nullable=True)
    technologies = Column(Text, nullable=True)
    available_support = Column(Text, nullable=True)  # Mentorship, funding, prototyping, pilot

    user = relationship("User", back_populates="industry_profile")
    collaborations = relationship("IndustryCollaboration", back_populates="industry")

class GovernmentDepartment(Base):
    __tablename__ = "government_departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    state = Column(String(100), default="Jharkhand")
    description = Column(Text, nullable=True)

class ChallengeCategory(Base):
    __tablename__ = "challenge_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon_name = Column(String(50), default="category")

class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    sub_category = Column(String(100), nullable=True)
    urgency = Column(String(50), default="Medium")
    priority = Column(SQLEnum(ChallengePriority), default=ChallengePriority.MEDIUM, index=True)
    expected_impact = Column(Text, nullable=True)
    status = Column(SQLEnum(ChallengeStatus), default=ChallengeStatus.SUBMITTED, index=True)
    current_tier = Column(String(50), default="PANCHAYAT", index=True)  # PANCHAYAT, BLOCK, DISTRICT, STATE
    escalation_level = Column(Integer, default=1)  # 1=Panchayat, 2=Block, 3=District, 4=State
    escalated_by = Column(String(255), nullable=True)
    escalation_remarks = Column(Text, nullable=True)
    
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=True)
    assigned_university_id = Column(Integer, ForeignKey("universities.id"), nullable=True)
    affected_population = Column(Integer, default=100)
    moderation_reason = Column(Text, nullable=True)
    moderated_by = Column(String(255), nullable=True)
    moderated_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    citizen = relationship("Citizen", back_populates="challenges")
    assigned_university = relationship("University", back_populates="assigned_challenges")
    location = relationship("ChallengeLocation", back_populates="challenge", uselist=False, cascade="all, delete-orphan")
    media = relationship("ChallengeMedia", back_populates="challenge", cascade="all, delete-orphan")
    ai_analysis = relationship("AIAnalysis", back_populates="challenge", uselist=False, cascade="all, delete-orphan")
    similarities = relationship("ChallengeSimilarity", foreign_keys="[ChallengeSimilarity.challenge_id]", back_populates="challenge", cascade="all, delete-orphan")
    university_matches = relationship("UniversityMatch", back_populates="challenge", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="challenge")
    status_history = relationship("StatusHistory", back_populates="challenge", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="challenge", cascade="all, delete-orphan")

class ChallengeLocation(Base):
    __tablename__ = "challenge_locations"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), unique=True, nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)
    district_name = Column(String(100), nullable=False, index=True)
    block_name = Column(String(100), nullable=True)
    village_or_city = Column(String(100), nullable=True)
    location_address = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    challenge = relationship("Challenge", back_populates="location")
    district = relationship("District", back_populates="challenges")

class ChallengeMedia(Base):
    __tablename__ = "challenge_media"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    media_type = Column(String(50), nullable=False)  # 'image', 'video', 'document'
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime, default=utc_now)

    challenge = relationship("Challenge", back_populates="media")

class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), unique=True, nullable=False)
    cleaned_text = Column(Text, nullable=True)
    classified_domain = Column(String(100), nullable=False)
    detected_priority = Column(SQLEnum(ChallengePriority), nullable=False)
    extracted_keywords = Column(Text, nullable=True)  # JSON or comma-separated
    required_expertise = Column(Text, nullable=True)  # JSON or comma-separated
    recommended_solution = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.92)
    analyzed_at = Column(DateTime, default=utc_now)

    challenge = relationship("Challenge", back_populates="ai_analysis")

class ChallengeSimilarity(Base):
    __tablename__ = "challenge_similarity"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    similar_challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    matched_keywords = Column(Text, nullable=True)

    challenge = relationship("Challenge", foreign_keys=[challenge_id], back_populates="similarities")
    similar_challenge = relationship("Challenge", foreign_keys=[similar_challenge_id])

class UniversityExpertise(Base):
    __tablename__ = "university_expertise"

    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False)
    domain = Column(String(100), nullable=False, index=True)
    department = Column(String(150), nullable=True)
    focus_area = Column(String(255), nullable=True)
    score_weight = Column(Float, default=1.0)

    university = relationship("University", back_populates="expertise_areas")

class UniversityMatch(Base):
    __tablename__ = "university_matches"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False)
    match_percentage = Column(Float, nullable=False)
    ranking = Column(Integer, default=1)
    matching_factors = Column(Text, nullable=True)

    challenge = relationship("Challenge", back_populates="university_matches")
    university = relationship("University")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False)
    faculty_mentor_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    objectives = Column(Text, nullable=True)
    expected_outcome = Column(Text, nullable=True)
    required_skills = Column(Text, nullable=True)
    timeline_months = Column(Integer, default=6)
    progress_percentage = Column(Float, default=0.0)
    current_stage = Column(String(100), default="Research & Ideation")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    challenge = relationship("Challenge", back_populates="projects")
    university = relationship("University", back_populates="projects")
    faculty_mentor = relationship("Faculty", back_populates="mentored_projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")
    proposals = relationship("SolutionProposal", back_populates="project", cascade="all, delete-orphan")
    collaborations = relationship("IndustryCollaboration", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("ProjectDocument", back_populates="project", cascade="all, delete-orphan")

class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    role_in_team = Column(String(100), default="Researcher & Developer")
    joined_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="members")
    student = relationship("Student", back_populates="project_memberships")

class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    completion_percentage = Column(Float, default=0.0)
    weight_pct = Column(Float, default=20.0)  # Weights sum to 100%
    deliverable_files = Column(Text, nullable=True)  # JSON list of evidence/document links
    status = Column(SQLEnum(MilestoneStatus), default=MilestoneStatus.NOT_STARTED)
    due_date = Column(DateTime, nullable=True)
    approved_by_faculty = Column(Boolean, default=False)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="milestones")

class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    assigned_to_student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    is_completed = Column(Boolean, default=False)
    due_date = Column(DateTime, nullable=True)
    submission_notes = Column(Text, nullable=True)
    submission_attachment = Column(String(500), nullable=True)

    project = relationship("Project", back_populates="tasks")
    assigned_student = relationship("Student")

class SolutionProposal(Base):
    __tablename__ = "solution_proposals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    proposed_solution = Column(Text, nullable=False)
    technical_approach = Column(Text, nullable=False)
    required_resources = Column(Text, nullable=True)
    expected_impact = Column(Text, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    timeline_weeks = Column(Integer, default=12)
    submitted_at = Column(DateTime, default=utc_now)
    is_approved_by_gov = Column(Boolean, default=False)

    project = relationship("Project", back_populates="proposals")

class IndustryCollaboration(Base):
    __tablename__ = "industry_collaborations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    industry_id = Column(Integer, ForeignKey("industry_partners.id"), nullable=False)
    offer_type = Column(String(100), nullable=False)  # Mentorship, Technical Support, Prototype Support, Funding, Pilot Implementation
    description = Column(Text, nullable=True)
    status = Column(String(50), default="Offered")  # Offered, Accepted, Active, Completed
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="collaborations")
    industry = relationship("IndustryPartner", back_populates="collaborations")

class ProjectDocument(Base):
    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    doc_type = Column(String(50), default="Report")
    file_url = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="documents")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    challenge = relationship("Challenge", back_populates="comments")
    author = relationship("User", back_populates="comments")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="INFO")
    reference_id = Column(Integer, nullable=True)  # challenge_id or project_id
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="notifications")

class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    updated_by = Column(String(100), default="System")
    remarks = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=utc_now)

    challenge = relationship("Challenge", back_populates="status_history")

class ImpactMetrics(Base):
    __tablename__ = "impact_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), unique=True, nullable=False)
    metric_value = Column(Integer, default=0)
    category = Column(String(100), default="General")
    last_updated = Column(DateTime, default=utc_now, onupdate=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    actor_name = Column(String(255), nullable=True)
    actor_role = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # CHALLENGE_VALIDATED, MILESTONE_APPROVED, etc.
    entity_name = Column(String(100), nullable=False, index=True)  # Challenge, Project, etc.
    entity_id = Column(Integer, nullable=False, index=True)
    old_state = Column(Text, nullable=True)  # JSON or status string
    new_state = Column(Text, nullable=True)  # JSON or status string
    ip_address = Column(String(45), nullable=True)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, index=True)

    actor = relationship("User")


class OrganizationProfile(Base):
    __tablename__ = "organization_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    legal_name = Column(String(255), nullable=False, index=True)
    org_type = Column(String(100), nullable=False, index=True)  # UNIVERSITY, INDUSTRY, CSR, NGO, LAB
    reg_number = Column(String(100), nullable=True, index=True)  # AISHE code / CIN / Registration
    official_email = Column(String(255), nullable=False)
    official_domain = Column(String(255), nullable=True)
    district_name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=True)
    contact_person = Column(String(150), nullable=True)
    phone_number = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)
    verification_status = Column(String(50), default="PENDING", index=True)  # PENDING, UNDER_REVIEW, VERIFIED, REJECTED, SUSPENDED
    submitted_documents = Column(Text, nullable=True)  # JSON list of uploaded document URLs
    rejection_reason = Column(Text, nullable=True)
    verified_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", foreign_keys=[user_id])
    verified_by = relationship("User", foreign_keys=[verified_by_user_id])


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    milestone_id = Column(Integer, ForeignKey("project_milestones.id"), nullable=True)
    verification_type = Column(String(100), nullable=False)  # EVIDENCE_REVIEW, FIELD_INSPECTION, LAB_REPORT, BENEFICIARY_CONFIRMATION
    inspector_name = Column(String(255), nullable=False)
    inspector_role = Column(String(100), nullable=False)
    verification_status = Column(String(50), default="SUBMITTED", index=True)  # SUBMITTED, VERIFIED, REJECTED
    evidence_urls = Column(Text, nullable=True)  # JSON array of proof files
    geotagged_lat = Column(Float, nullable=True)
    geotagged_lng = Column(Float, nullable=True)
    inspection_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project")
    milestone = relationship("ProjectMilestone")


class CitizenFeedback(Base):
    __tablename__ = "citizen_feedback"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1 to 5
    is_issue_resolved = Column(Boolean, default=True)
    satisfaction_score = Column(Float, default=5.0)
    comments = Column(Text, nullable=False)
    evidence_photo_url = Column(String(500), nullable=True)
    submitted_at = Column(DateTime, default=utc_now)

    challenge = relationship("Challenge")
    citizen = relationship("Citizen")


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), unique=True, nullable=False, index=True)
    revoked_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=False)
