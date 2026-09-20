from datetime import datetime
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from backend.app.models.models import UserRole, ChallengePriority, ChallengeStatus, MilestoneStatus

# ----------------- STANDARD API RESPONSE ENVELOPE -----------------

class ApiResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    request_id: Optional[str] = None

class PaginatedMeta(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int

# ----------------- AUTH & USER -----------------

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    role: UserRole
    user_id: int
    full_name: str
    email: str
    university_id: Optional[int] = None
    university_name: Optional[str] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    university_id: Optional[int] = None
    type: Optional[str] = "access"
    jti: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    token: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Optional[UserRole] = None
    university_id: Optional[int] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: Optional[str] = None
    role: UserRole
    district_name: Optional[str] = "Ranchi"
    institution_name: Optional[str] = None
    company_name: Optional[str] = None
    skills: Optional[str] = None
    expertise: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    phone_number: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

# ----------------- DISTRICT & CATEGORY -----------------

class DistrictOut(BaseModel):
    id: int
    name: str
    state: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class ChallengeCategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon_name: str = "category"
    model_config = ConfigDict(from_attributes=True)

# ----------------- CHALLENGE & MEDIA -----------------

class ChallengeLocationCreate(BaseModel):
    district_name: str
    block_name: Optional[str] = None
    village_or_city: Optional[str] = None
    location_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ChallengeLocationOut(BaseModel):
    id: int
    district_name: str
    block_name: Optional[str] = None
    village_or_city: Optional[str] = None
    location_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class ChallengeMediaOut(BaseModel):
    id: int
    media_type: str
    file_url: str
    file_name: Optional[str] = None
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChallengeCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=15)
    category: str
    sub_category: Optional[str] = None
    urgency: str = "Medium"
    expected_impact: Optional[str] = None
    affected_population: Optional[int] = 100
    location: ChallengeLocationCreate
    media_urls: Optional[List[str]] = []

class AIAnalysisOut(BaseModel):
    id: int
    classified_domain: str
    detected_priority: ChallengePriority
    extracted_keywords: Optional[str] = None
    required_expertise: Optional[str] = None
    recommended_solution: Optional[str] = None
    confidence_score: float
    model_config = ConfigDict(from_attributes=True)

class UniversityMatchOut(BaseModel):
    university_id: int
    institution_name: str
    district_name: str
    match_percentage: float
    ranking: int
    matching_factors: Optional[str] = None

class SimilarChallengeOut(BaseModel):
    challenge_id: int
    title: str
    district_name: str
    status: ChallengeStatus
    similarity_score: float

class StatusHistoryOut(BaseModel):
    id: int
    from_status: Optional[str] = None
    to_status: str
    updated_by: str
    remarks: Optional[str] = None
    changed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CommentCreate(BaseModel):
    content: str

class CommentOut(BaseModel):
    id: int
    user_id: int
    author_name: str
    author_role: str
    content: str
    created_at: datetime

class ChallengeOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    sub_category: Optional[str] = None
    urgency: str
    priority: ChallengePriority
    expected_impact: Optional[str] = None
    affected_population: Optional[int] = 100
    status: ChallengeStatus
    district_name: Optional[str] = None
    created_at: datetime
    assigned_university_name: Optional[str] = None
    current_tier: Optional[str] = "PANCHAYAT"
    escalation_level: Optional[int] = 1
    escalated_by: Optional[str] = None
    escalation_remarks: Optional[str] = None
    moderation_reason: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ChallengeDetailOut(ChallengeOut):
    location: Optional[ChallengeLocationOut] = None
    media: List[ChallengeMediaOut] = []
    ai_analysis: Optional[AIAnalysisOut] = None
    university_matches: List[UniversityMatchOut] = []
    similar_challenges: List[SimilarChallengeOut] = []
    status_history: List[StatusHistoryOut] = []
    comments: List[CommentOut] = []

class ChallengeStatusUpdate(BaseModel):
    status: ChallengeStatus
    remarks: Optional[str] = None

class EscalateChallengeRequest(BaseModel):
    target_tier: str
    remarks: str

class AssignUniversityRequest(BaseModel):
    university_id: int
    remarks: Optional[str] = None

class MarkDuplicateRequest(BaseModel):
    canonical_challenge_id: int
    remarks: Optional[str] = "Identified as duplicate of existing registered challenge"

class RejectChallengeRequest(BaseModel):
    reason: str

# ----------------- PROJECTS & TEAMS -----------------

class ProjectCreate(BaseModel):
    challenge_id: int
    name: str
    description: str
    objectives: Optional[str] = None
    expected_outcome: Optional[str] = None
    required_skills: Optional[str] = None
    timeline_months: int = 6
    faculty_mentor_id: Optional[int] = None
    student_ids: Optional[List[int]] = []

class ProjectMemberOut(BaseModel):
    student_id: int
    student_name: str
    department_name: Optional[str] = None
    role_in_team: str
    skills: Optional[str] = None

class MilestoneCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completion_percentage: float = 0.0
    weight_pct: float = 20.0
    due_date: Optional[datetime] = None

class MilestoneUpdate(BaseModel):
    completion_percentage: Optional[float] = None
    status: Optional[MilestoneStatus] = None
    approved_by_faculty: Optional[bool] = None
    deliverable_files: Optional[str] = None

class MilestoneOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completion_percentage: float
    weight_pct: Optional[float] = 20.0
    deliverable_files: Optional[str] = None
    status: MilestoneStatus
    due_date: Optional[datetime] = None
    approved_by_faculty: bool
    model_config = ConfigDict(from_attributes=True)

class TaskCreate(BaseModel):
    title: str
    assigned_to_student_id: Optional[int] = None
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    is_completed: Optional[bool] = None
    submission_notes: Optional[str] = None
    submission_attachment: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    title: str
    assigned_to_student_id: Optional[int] = None
    assigned_student_name: Optional[str] = None
    is_completed: bool
    submission_notes: Optional[str] = None
    submission_attachment: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class SolutionProposalCreate(BaseModel):
    proposed_solution: str
    technical_approach: str
    required_resources: Optional[str] = None
    expected_impact: Optional[str] = None
    estimated_cost: Optional[float] = None
    timeline_weeks: int = 12

class SolutionProposalOut(BaseModel):
    id: int
    proposed_solution: str
    technical_approach: str
    required_resources: Optional[str] = None
    expected_impact: Optional[str] = None
    estimated_cost: Optional[float] = None
    timeline_weeks: int
    is_approved_by_gov: bool
    model_config = ConfigDict(from_attributes=True)

class IndustryCollaborationCreate(BaseModel):
    offer_type: str  # Mentorship, Technical Support, Prototype Support, Funding, Pilot Implementation
    description: Optional[str] = None

class IndustryCollaborationOut(BaseModel):
    id: int
    company_name: str
    industry_domain: str
    offer_type: str
    description: Optional[str] = None
    status: str
    model_config = ConfigDict(from_attributes=True)

class ProjectOut(BaseModel):
    id: int
    challenge_id: int
    challenge_title: str
    university_id: int
    university_name: str
    faculty_mentor_name: Optional[str] = None
    name: str
    description: str
    progress_percentage: float
    current_stage: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProjectDocumentOut(BaseModel):
    id: int
    project_id: int
    title: str
    doc_type: Optional[str] = "Report"
    file_url: str
    uploaded_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ProjectDocumentCreate(BaseModel):
    title: str
    file_url: str
    doc_type: Optional[str] = "Report"

class ProjectDetailOut(ProjectOut):
    objectives: Optional[str] = None
    expected_outcome: Optional[str] = None
    required_skills: Optional[str] = None
    members: List[ProjectMemberOut] = []
    milestones: List[MilestoneOut] = []
    tasks: List[TaskOut] = []
    proposals: List[SolutionProposalOut] = []
    collaborations: List[IndustryCollaborationOut] = []
    documents: List[ProjectDocumentOut] = []

# ----------------- ORGANIZATIONS -----------------

class OrganizationProfileCreate(BaseModel):
    legal_name: str
    org_type: str  # UNIVERSITY, INDUSTRY, CSR, NGO, LAB
    reg_number: Optional[str] = None
    official_email: EmailStr
    official_domain: Optional[str] = None
    district_name: str
    address: Optional[str] = None
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    submitted_documents: Optional[str] = None

class OrganizationProfileOut(BaseModel):
    id: int
    user_id: int
    legal_name: str
    org_type: str
    reg_number: Optional[str] = None
    official_email: str
    official_domain: Optional[str] = None
    district_name: str
    address: Optional[str] = None
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    verification_status: str
    submitted_documents: Optional[str] = None
    rejection_reason: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrganizationVerifyRequest(BaseModel):
    status: str  # VERIFIED, REJECTED, UNDER_REVIEW
    rejection_reason: Optional[str] = None

# ----------------- VERIFICATION & EVIDENCE -----------------

class VerificationRecordCreate(BaseModel):
    project_id: int
    milestone_id: Optional[int] = None
    verification_type: str  # EVIDENCE_REVIEW, FIELD_INSPECTION, LAB_REPORT, BENEFICIARY_CONFIRMATION
    inspector_name: Optional[str] = None
    inspector_role: Optional[str] = None
    evidence_urls: Optional[Union[str, List[str]]] = None
    geotagged_lat: Optional[float] = None
    geotagged_lng: Optional[float] = None
    inspection_notes: Optional[str] = None

class VerificationReviewRequest(BaseModel):
    decision: Optional[str] = None
    status: Optional[str] = None
    remarks: Optional[str] = None
    review_notes: Optional[str] = None

class VerificationRecordOut(BaseModel):
    id: int
    project_id: int
    milestone_id: Optional[int] = None
    verification_type: str
    inspector_name: str
    inspector_role: str
    verification_status: str
    evidence_urls: Optional[str] = None
    geotagged_lat: Optional[float] = None
    geotagged_lng: Optional[float] = None
    inspection_notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- CITIZEN FEEDBACK -----------------

class CitizenFeedbackCreate(BaseModel):
    challenge_id: int
    rating: int = Field(..., ge=1, le=5)
    is_issue_resolved: bool = True
    satisfaction_score: float = 5.0
    comments: str = Field(..., min_length=5)
    evidence_photo_url: Optional[str] = None

class CitizenFeedbackOut(BaseModel):
    id: int
    challenge_id: int
    citizen_id: int
    rating: int
    is_issue_resolved: bool
    satisfaction_score: float
    comments: str
    evidence_photo_url: Optional[str] = None
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- AUDIT LOGS -----------------

class AuditLogOut(BaseModel):
    id: int
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    actor_role: str
    action: str
    entity_name: str
    entity_id: int
    old_state: Optional[str] = None
    new_state: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- NOTIFICATIONS & STATS -----------------

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    reference_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AdminAnalyticsOut(BaseModel):
    total_challenges: int
    submitted: int
    under_review: int
    assigned: int
    in_progress: int
    resolved: int
    total_universities: int
    total_industry_partners: int
    total_student_teams: int
    total_active_projects: int
    challenges_by_district: dict
    challenges_by_category: dict
    challenges_by_priority: dict
    impact_metrics: dict
