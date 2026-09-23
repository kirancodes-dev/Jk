from datetime import datetime
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from backend.app.models.models import (
    UserRole, ChallengePriority, ChallengeStatus, MilestoneStatus,
    TeamInvitationStatus, ProposalStatus, EvidenceReviewStatus, FacilityType, CapabilityEvidenceType,
    PartnerType, CollaborationOfferType, AgreementStatus, FundingHoldState, IPRecordType, IPOwnership, IPConsentStatus
)

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
    email: Optional[EmailStr] = None
    identifier: Optional[str] = None
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

class ChallengeAttachmentOut(BaseModel):
    id: int
    object_id: str
    original_filename: str
    detected_mime: str
    size_bytes: int
    sha256_checksum: str
    scan_status: str
    access_classification: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AttachmentUploadOut(BaseModel):
    attachment_id: str
    original_filename: str
    detected_mime: str
    size_bytes: int
    sha256_checksum: str
    scan_status: str
    access_classification: str
    created_at: datetime

class ChallengeCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=15, max_length=5000)
    category: str
    sub_category: Optional[str] = None
    urgency: str = "Medium"
    expected_impact: Optional[str] = None
    affected_population: int = Field(..., ge=1, description="Estimated number of citizens directly impacted")
    location: ChallengeLocationCreate
    source_type: Optional[str] = "CITIZEN_MOBILE"
    contact_preference: Optional[str] = "SMS"
    consent_version: Optional[str] = "v1.0"
    consent_given: bool = True
    data_sharing_choice: Optional[str] = "PUBLIC"
    accessibility_needs: Optional[str] = None
    submission_language: Optional[str] = "en"
    is_anonymous_public: Optional[bool] = False
    idempotency_key: Optional[str] = None
    attachment_ids: Optional[List[str]] = []
    media_urls: Optional[List[str]] = []

class ChallengeDraftCreate(BaseModel):
    draft_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    payload: Dict[str, Any]

class ChallengeDraftOut(BaseModel):
    id: int
    draft_id: str
    idempotency_key: Optional[str] = None
    payload: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TaxonomyDomainOut(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = "category"
    subdomains: List[str] = []

class AIAnalysisOut(BaseModel):
    id: int
    classified_domain: str
    detected_priority: ChallengePriority
    extracted_keywords: Optional[str] = None
    required_expertise: Optional[str] = None
    recommended_solution: Optional[str] = None
    confidence_score: float
    model_name: Optional[str] = "JHARKHAND_TAXONOMY_CLASSIFIER_V2"
    model_version: Optional[str] = "2.2.0"
    provider_name: Optional[str] = "LOCAL_DETERMINISTIC_ENGINE"
    execution_time_ms: Optional[int] = 0
    input_snapshot_hash: Optional[str] = None
    detected_language: Optional[str] = "en"
    language_confidence: Optional[float] = 1.0
    calibration_status: Optional[str] = "CALIBRATED_FALLBACK"
    is_fallback: bool = True
    fallback_reason: Optional[str] = None
    policy_version: Optional[str] = "v2026.1"
    explanation: Optional[str] = None
    features_json: Optional[str] = None
    priority_breakdown_json: Optional[str] = None
    translated_title: Optional[str] = None
    translated_description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UniversityMatchOut(BaseModel):
    university_id: int
    institution_name: str
    district_name: str
    match_percentage: float
    ranking: int
    matching_factors: Optional[str] = None
    verification_status: Optional[str] = "VERIFIED"

class SimilarChallengeOut(BaseModel):
    challenge_id: int
    title: str
    district_name: str
    status: ChallengeStatus
    similarity_score: float
    text_similarity: Optional[float] = 0.0
    geographic_similarity: Optional[float] = 0.0
    temporal_similarity: Optional[float] = 0.0
    category_similarity: Optional[float] = 0.0
    explanation: Optional[str] = None
    dismissed: bool = False
    dismissal_reason: Optional[str] = None

class AIHumanOverrideCreate(BaseModel):
    decision_type: str  # DOMAIN_OVERRIDE, PRIORITY_OVERRIDE, DUPLICATE_DECISION, UNIVERSITY_OVERRIDE, FULL_ACCEPTANCE
    override_value: str
    mandatory_reason: str

class AIHumanOverrideOut(BaseModel):
    id: int
    challenge_id: int
    analysis_id: Optional[int] = None
    reviewer_id: int
    decision_type: str
    original_value: str
    override_value: str
    mandatory_reason: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AIJobOut(BaseModel):
    id: int
    challenge_id: int
    idempotency_key: str
    job_type: str
    status: str
    attempts: int
    max_retries: int
    next_run_at: datetime
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class AIPriorityConfigCreate(BaseModel):
    config_version: str
    weights: Dict[str, float]
    description: Optional[str] = None

class AIPriorityConfigOut(BaseModel):
    id: int
    config_version: str
    weights_json: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


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

class ChallengeAllocationOut(BaseModel):
    id: int
    challenge_id: int
    assigned_by_user_id: int
    assigned_to_org_id: int
    status: str
    allocated_at: datetime
    deadline_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    response_notes: Optional[str] = None
    capacity_assessment: Optional[str] = None
    coi_declared: bool = False
    reassigned_from_allocation_id: Optional[int] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ChallengeOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    sub_category: Optional[str] = None
    urgency: str
    priority: ChallengePriority
    expected_impact: Optional[str] = None
    affected_population: int = 100
    status: ChallengeStatus
    district_name: Optional[str] = None
    created_at: datetime
    assigned_university_name: Optional[str] = None
    current_tier: Optional[str] = "PANCHAYAT"
    escalation_level: Optional[int] = 1
    escalated_by: Optional[str] = None
    escalation_remarks: Optional[str] = None
    moderation_reason: Optional[str] = None
    submitted_by_name: Optional[str] = None
    submitter_role: Optional[str] = None
    source_type: Optional[str] = "CITIZEN_MOBILE"
    consent_version: Optional[str] = "v1.0"
    data_sharing_choice: Optional[str] = "PUBLIC"
    submission_language: Optional[str] = "en"
    translation_status: Optional[str] = "NONE"
    is_anonymous_public: Optional[bool] = False
    idempotency_key: Optional[str] = None
    version: int = 1
    model_config = ConfigDict(from_attributes=True)

class ChallengeDetailOut(ChallengeOut):
    location: Optional[ChallengeLocationOut] = None
    media: List[ChallengeMediaOut] = []
    attachments: List[ChallengeAttachmentOut] = []
    ai_analysis: Optional[AIAnalysisOut] = None
    university_matches: List[UniversityMatchOut] = []
    similar_challenges: List[SimilarChallengeOut] = []
    status_history: List[StatusHistoryOut] = []
    comments: List[CommentOut] = []
    allocations: List[ChallengeAllocationOut] = []

class ChallengeStatusUpdate(BaseModel):
    status: ChallengeStatus
    remarks: Optional[str] = None
    expected_version: Optional[int] = None

class EscalateChallengeRequest(BaseModel):
    target_tier: str
    remarks: str
    expected_version: Optional[int] = None

class AssignUniversityRequest(BaseModel):
    university_id: Optional[int] = None
    organization_id: Optional[int] = None
    deadline_days: int = 14
    capacity_notes: Optional[str] = None
    remarks: Optional[str] = None
    expected_version: Optional[int] = None

class AcceptReviewRequest(BaseModel):
    expected_version: Optional[int] = None
    notes: Optional[str] = None

class RequestInfoRequest(BaseModel):
    expected_version: Optional[int] = None
    clarification_items: List[str] = []
    notes: Optional[str] = None

class SubmitInfoRequest(BaseModel):
    expected_version: Optional[int] = None
    responses: Dict[str, Any] = {}
    additional_attachments: Optional[List[str]] = []

class ValidateChallengeRequest(BaseModel):
    expected_version: Optional[int] = None
    remarks: Optional[str] = "Challenge reviewed and officially validated"
    assigned_tier: Optional[str] = None

class RejectChallengeRequest(BaseModel):
    reason: str
    reason_code: Optional[str] = "OTHER"
    expected_version: Optional[int] = None

class MarkDuplicateRequest(BaseModel):
    canonical_challenge_id: int
    remarks: Optional[str] = "Identified as duplicate of existing registered challenge"
    expected_version: Optional[int] = None

class KeepSeparateRequest(BaseModel):
    compared_challenge_id: int
    justification: str
    expected_version: Optional[int] = None

class AllocationResponseRequest(BaseModel):
    decision: str  # ACCEPT or DECLINE
    notes: Optional[str] = None
    coi_declared: bool = False
    expected_version: Optional[int] = None

class PauseChallengeRequest(BaseModel):
    reason: str
    expected_version: Optional[int] = None

class ResumeChallengeRequest(BaseModel):
    remarks: Optional[str] = None
    expected_version: Optional[int] = None

class ReopenChallengeRequest(BaseModel):
    reason: str
    expected_version: Optional[int] = None

class AppealChallengeRequest(BaseModel):
    grounds: str
    evidence: Optional[List[str]] = []

class DomainAuditEventOut(BaseModel):
    id: int
    sequence_number: int
    entity_type: str
    entity_id: int
    action: str
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    actor_id: Optional[int] = None
    actor_role: Optional[str] = None
    jurisdiction_level: Optional[str] = None
    jurisdiction_value: Optional[str] = None
    reason_code: Optional[str] = None
    notes: Optional[str] = None
    payload_hash: str
    prev_event_hash: Optional[str] = None
    event_hash: str
    is_internal: bool = False
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class AuditChainVerificationOut(BaseModel):
    is_valid: bool
    verified_count: int
    tampered_sequence: Optional[int] = None
    reason: Optional[str] = None

# ----------------- UNIVERSITY CAPABILITY PROFILE (Stage 6) -----------------

class UniversityFacilityCreate(BaseModel):
    facility_type: FacilityType
    name: str
    description: Optional[str] = None
    capacity_units: Optional[int] = None
    is_operational: bool = True

class UniversityFacilityOut(BaseModel):
    id: int
    facility_type: FacilityType
    name: str
    description: Optional[str] = None
    capacity_units: Optional[int] = None
    is_operational: bool
    model_config = ConfigDict(from_attributes=True)

class UniversityDistrictCoverageCreate(BaseModel):
    district_name: str
    is_primary: bool = False

class UniversityDistrictCoverageOut(BaseModel):
    id: int
    district_name: str
    is_primary: bool
    model_config = ConfigDict(from_attributes=True)

class UniversityCapabilityEvidenceCreate(BaseModel):
    evidence_type: CapabilityEvidenceType = CapabilityEvidenceType.OTHER
    title: str
    evidence_object_id: Optional[str] = None
    issued_by: Optional[str] = None
    valid_until: Optional[datetime] = None

class UniversityCapabilityEvidenceOut(BaseModel):
    id: int
    evidence_type: CapabilityEvidenceType
    title: str
    evidence_object_id: Optional[str] = None
    issued_by: Optional[str] = None
    valid_until: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DepartmentOut(BaseModel):
    id: int
    name: str
    head_of_department: Optional[str] = None
    faculty_count: int = 0
    student_count: int = 0
    model_config = ConfigDict(from_attributes=True)

class UniversityProfileUpdate(BaseModel):
    address: Optional[str] = None
    website: Optional[str] = None
    facilities_description: Optional[str] = None
    nirf_ranking: Optional[int] = None
    capacity_max_active_projects: Optional[int] = None

class UniversityProfileOut(BaseModel):
    id: int
    institution_name: str
    district_name: str
    address: Optional[str] = None
    website: Optional[str] = None
    nirf_ranking: Optional[int] = None
    is_active: bool
    verification_status: str
    is_verified_active: bool
    capacity_max_active_projects: int
    active_projects_count: int = 0
    departments: List[DepartmentOut] = []
    facilities: List[UniversityFacilityOut] = []
    district_coverage: List[UniversityDistrictCoverageOut] = []
    capability_evidence: List[UniversityCapabilityEvidenceOut] = []
    expertise_areas: List[str] = []

# ----------------- TEAM INVITATIONS (Stage 6) -----------------

class TeamInvitationCreate(BaseModel):
    student_id: Optional[int] = None
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    role_in_team: str = "Researcher & Developer"
    proposed_start_date: Optional[datetime] = None
    proposed_end_date: Optional[datetime] = None

class TeamInvitationRespond(BaseModel):
    decision: str  # ACCEPT or DECLINE
    conflict_declared: bool = False
    conflict_notes: Optional[str] = None
    response_notes: Optional[str] = None

class TeamInvitationOut(BaseModel):
    id: int
    project_id: int
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    faculty_id: Optional[int] = None
    faculty_name: Optional[str] = None
    department_id: Optional[int] = None
    role_in_team: str
    proposed_start_date: Optional[datetime] = None
    proposed_end_date: Optional[datetime] = None
    status: TeamInvitationStatus
    conflict_declared: bool
    conflict_notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MemberRemoveRequest(BaseModel):
    reason: str
    replacement_student_id: Optional[int] = None
    replacement_role_in_team: Optional[str] = None

class MembershipHistoryOut(BaseModel):
    id: int
    action: str
    student_id: Optional[int] = None
    previous_member_student_id: Optional[int] = None
    role_in_team: Optional[str] = None
    reason: Optional[str] = None
    occurred_at: datetime
    model_config = ConfigDict(from_attributes=True)

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
    id: int
    student_id: int
    student_name: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    role_in_team: str
    skills: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    conflict_declared: bool = False
    is_active: bool = True

class MilestoneCreate(BaseModel):
    title: str
    description: Optional[str] = None
    weight_pct: float = Field(..., gt=0, le=100)
    due_date: Optional[datetime] = None

class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    weight_pct: Optional[float] = None

class MilestoneSubmitRequest(BaseModel):
    notes: Optional[str] = None

class MilestoneReviewRequest(BaseModel):
    decision: str  # APPROVE, REVISION_REQUESTED, REJECTED
    notes: str = Field(..., min_length=3, description="Mandatory review comment")

class MilestoneOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completion_percentage: float
    weight_pct: float
    status: MilestoneStatus
    due_date: Optional[datetime] = None
    approved_by_faculty: bool
    review_notes: Optional[str] = None
    evidence_count: int = 0
    model_config = ConfigDict(from_attributes=True)

class MilestonesFinalizeResponse(BaseModel):
    status: str
    message: str
    total_weight: float
    locked: bool

class TaskCreate(BaseModel):
    title: str
    milestone_id: Optional[int] = None
    assigned_to_student_id: Optional[int] = None
    due_date: Optional[datetime] = None

class TaskSubmitRequest(BaseModel):
    submission_notes: Optional[str] = None

class TaskReviewRequest(BaseModel):
    decision: str  # APPROVE, REVISION_REQUESTED
    notes: Optional[str] = None

class TaskUpdate(BaseModel):
    is_completed: Optional[bool] = None
    submission_notes: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    title: str
    milestone_id: Optional[int] = None
    assigned_to_student_id: Optional[int] = None
    assigned_student_name: Optional[str] = None
    status: str = "PENDING"
    is_completed: bool
    submission_notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class SolutionProposalCreate(BaseModel):
    proposed_solution: str
    technical_approach: str
    objectives: str = Field(..., min_length=10)
    feasibility_notes: str = Field(..., min_length=10)
    budget_breakdown: str = Field(..., min_length=5)
    estimated_cost: float = Field(..., ge=0)
    timeline_weeks: int = Field(..., ge=1)
    risks: str = Field(..., min_length=5)
    safeguarding_notes: str = Field(..., min_length=5)
    maintenance_plan: str = Field(..., min_length=5)
    measurable_outcomes: str = Field(..., min_length=5)
    required_resources: Optional[str] = None
    expected_impact: Optional[str] = None

class ProposalReviewRequest(BaseModel):
    decision: str  # FACULTY_REVIEWED, HEI_APPROVED, GOVERNMENT_REVIEWED, APPROVED, REVISION_REQUESTED, REJECTED
    notes: str = Field(..., min_length=3)

class IndustryFeedbackRequest(BaseModel):
    notes: str = Field(..., min_length=3)

class SolutionProposalOut(BaseModel):
    id: int
    project_id: int
    proposed_solution: str
    technical_approach: str
    objectives: Optional[str] = None
    feasibility_notes: Optional[str] = None
    budget_breakdown: Optional[str] = None
    required_resources: Optional[str] = None
    expected_impact: Optional[str] = None
    estimated_cost: Optional[float] = None
    timeline_weeks: int
    risks: Optional[str] = None
    safeguarding_notes: Optional[str] = None
    maintenance_plan: Optional[str] = None
    measurable_outcomes: Optional[str] = None
    status: ProposalStatus
    version: int
    is_current: bool
    faculty_review_notes: Optional[str] = None
    hei_approval_notes: Optional[str] = None
    government_review_notes: Optional[str] = None
    revision_requested_reason: Optional[str] = None
    is_approved_by_gov: bool
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReviewCommentCreate(BaseModel):
    entity_type: str  # PROPOSAL, MILESTONE, DELIVERABLE, TASK
    entity_id: int
    content: str = Field(..., min_length=1)

class ReviewCommentOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    author_id: int
    author_name: Optional[str] = None
    author_role: Optional[str] = None
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EvidenceFileOut(BaseModel):
    object_id: str
    entity_type: str
    entity_id: int
    version: int
    is_current: bool
    original_filename: str
    detected_mime: str
    size_bytes: int
    sha256_checksum: str
    review_status: EvidenceReviewStatus
    review_notes: Optional[str] = None
    created_at: datetime
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
    agreement_status: Optional[AgreementStatus] = None
    model_config = ConfigDict(from_attributes=True)

class ProjectOut(BaseModel):
    id: int
    challenge_id: int
    challenge_title: str
    university_id: int
    university_name: str
    faculty_mentor_name: Optional[str] = None
    faculty_mentor_status: Optional[str] = "PENDING"
    name: str
    description: str
    progress_percentage: float
    current_stage: str
    milestones_locked: bool = False
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProjectDocumentOut(BaseModel):
    id: int
    project_id: int
    title: str
    doc_type: Optional[str] = "Report"
    evidence_object_id: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ProjectDetailOut(ProjectOut):
    objectives: Optional[str] = None
    expected_outcome: Optional[str] = None
    required_skills: Optional[str] = None
    members: List[ProjectMemberOut] = []
    pending_invitations: List[TeamInvitationOut] = []
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
    verification_type: str = "FIELD_INSPECTION"  # EVIDENCE_REVIEW, FIELD_INSPECTION, LAB_REPORT, BENEFICIARY_CONFIRMATION
    inspector_name: Optional[str] = None
    inspector_role: Optional[str] = None
    inspector_organization_id: Optional[int] = None
    assignment_id: Optional[str] = None
    checklist_responses: Optional[Union[Dict[str, Any], str]] = None
    visit_timestamp: Optional[datetime] = None
    device_metadata: Optional[Union[Dict[str, Any], str]] = None
    before_media_urls: Optional[Union[List[str], str]] = None
    after_media_urls: Optional[Union[List[str], str]] = None
    lab_report_references: Optional[Union[Dict[str, Any], List[Dict[str, Any]], str]] = None
    beneficiary_sample_size: Optional[int] = None
    beneficiary_feedback_summary: Optional[str] = None
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
    inspector_user_id: Optional[int] = None
    inspector_organization_id: Optional[int] = None
    assignment_id: Optional[str] = None
    verification_status: str
    evidence_urls: Optional[str] = None
    checklist_responses: Optional[str] = None
    visit_timestamp: Optional[datetime] = None
    device_metadata: Optional[str] = None
    before_media_urls: Optional[str] = None
    after_media_urls: Optional[str] = None
    lab_report_references: Optional[str] = None
    beneficiary_sample_size: Optional[int] = None
    beneficiary_feedback_summary: Optional[str] = None
    geotagged_lat: Optional[float] = None
    geotagged_lng: Optional[float] = None
    inspection_notes: Optional[str] = None
    reviewed_by_user_id: Optional[int] = None
    review_decision: Optional[str] = None
    review_notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- OUTCOME METRICS (STAGE 8) -----------------

class OutcomeMetricCreate(BaseModel):
    project_id: int
    metric_name: str = Field(..., min_length=3, max_length=255)
    metric_definition: str = Field(..., min_length=10)
    metric_type: str = "QUANTITATIVE"  # QUANTITATIVE, QUALITATIVE
    unit_of_measure: Optional[str] = None
    baseline_value: str = Field(..., min_length=1)
    baseline_date: Optional[datetime] = None
    baseline_source: str = Field(..., min_length=3)
    target_value: str = Field(..., min_length=1)
    target_date: Optional[datetime] = None
    collection_method: Optional[str] = None
    sample_size: Optional[int] = None
    uncertainty_margin: Optional[str] = None
    responsible_org_name: Optional[str] = None
    district_name: Optional[str] = None
    block_name: Optional[str] = None

class OutcomeMetricUpdate(BaseModel):
    actual_value: Optional[str] = None
    actual_date: Optional[datetime] = None
    actual_source: Optional[str] = None
    collection_method: Optional[str] = None
    sample_size: Optional[int] = None
    uncertainty_margin: Optional[str] = None
    evidence_references: Optional[Union[List[str], str]] = None
    verification_status: Optional[str] = None  # REPORTED, ESTIMATED, MEASURED

class OutcomeMetricVerifyRequest(BaseModel):
    verification_status: str = "INDEPENDENTLY_VERIFIED"  # MEASURED, INDEPENDENTLY_VERIFIED
    verification_notes: Optional[str] = None

class OutcomeMetricOut(BaseModel):
    id: int
    project_id: int
    challenge_id: int
    metric_name: str
    metric_definition: str
    metric_type: str
    unit_of_measure: Optional[str] = None
    baseline_value: str
    baseline_date: datetime
    baseline_source: str
    target_value: str
    target_date: Optional[datetime] = None
    actual_value: Optional[str] = None
    actual_date: Optional[datetime] = None
    actual_source: Optional[str] = None
    collection_method: Optional[str] = None
    sample_size: Optional[int] = None
    uncertainty_margin: Optional[str] = None
    responsible_org_name: Optional[str] = None
    responsible_user_id: Optional[int] = None
    evidence_references: Optional[str] = None
    district_name: Optional[str] = None
    block_name: Optional[str] = None
    verification_status: str
    verified_by_user_id: Optional[int] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- CITIZEN FEEDBACK -----------------

class CitizenFeedbackCreate(BaseModel):
    challenge_id: int
    challenge_version: Optional[int] = 1
    rating: int = Field(..., ge=1, le=5)
    is_issue_resolved: bool = True
    satisfaction_score: float = 5.0
    comments: str = Field(..., min_length=5)
    evidence_photo_url: Optional[str] = None
    beneficiary_verification_type: Optional[str] = "ORIGINAL_REPORTER"  # ORIGINAL_REPORTER, VERIFIED_RESIDENT, INVITATION_TOKEN
    invitation_token: Optional[str] = None
    is_public: Optional[bool] = True
    accessibility_needs: Optional[str] = None
    language: Optional[str] = "en"

class CitizenFeedbackModerationRequest(BaseModel):
    moderation_status: str = Field(..., pattern="^(APPROVED|FLAGGED|REDACTED)$")
    moderation_reason: str = Field(..., min_length=5)
    redacted_comments: Optional[str] = None

class CitizenFeedbackAppealRequest(BaseModel):
    appeal_reason: str = Field(..., min_length=10)

class CitizenFeedbackOut(BaseModel):
    id: int
    challenge_id: int
    citizen_id: int
    user_id: Optional[int] = None
    challenge_version: int
    rating: int
    is_issue_resolved: bool
    satisfaction_score: float
    comments: str
    evidence_photo_url: Optional[str] = None
    beneficiary_verification_type: str
    moderation_status: str
    moderation_reason: Optional[str] = None
    is_public: bool
    appeal_status: str
    accessibility_needs: Optional[str] = None
    language: str
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- PROJECT CLOSURE (STAGE 8) -----------------

class PreconditionItem(BaseModel):
    key: str
    title: str
    satisfied: bool
    details: Optional[str] = None

class ProjectClosureEvaluationOut(BaseModel):
    project_id: int
    challenge_id: int
    ready_for_closure: bool
    preconditions: List[PreconditionItem]
    missing_preconditions: List[str]

class ProjectClosureRequest(BaseModel):
    decision: str = "APPROVED_CLOSED"  # APPROVED_CLOSED, REJECTED_REVISION, ESCALATED_REOPENED
    ip_cleared: bool = True
    ip_handover_details: Optional[str] = None
    maintenance_handover_plan: str = Field(..., min_length=20)
    handover_recipient_org: str = Field(..., min_length=3)
    closure_remarks: str = Field(..., min_length=10)

class ProjectClosureRecordOut(BaseModel):
    id: int
    project_id: int
    challenge_id: int
    closed_by_user_id: int
    closure_decision: str
    preconditions_snapshot_json: str
    ip_cleared: bool
    ip_handover_details: Optional[str] = None
    maintenance_handover_plan: str
    handover_recipient_org: str
    closure_remarks: str
    closed_at: datetime
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
    category: str = "GENERAL"
    deep_link: Optional[str] = None
    retention_days: int = 90
    is_archived: bool = False
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PaginatedNotificationsOut(BaseModel):
    total: int
    unread_count: int
    limit: int
    offset: int
    items: List[NotificationOut]

class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    preferred_locale: Optional[str] = None
    categories: Optional[dict] = None
    consent_given: Optional[bool] = None

class NotificationPreferenceOut(BaseModel):
    user_id: int
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    whatsapp_enabled: bool
    preferred_locale: str
    categories: dict
    consent_given: bool
    consent_timestamp: datetime
    consent_version: str
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class NotificationOutboxOut(BaseModel):
    id: int
    user_id: int
    channel: str
    provider: str
    recipient: str
    template_id: Optional[str] = None
    locale: str
    delivery_status: str
    retry_count: int
    max_retries: int
    failure_reason: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ExportJobCreate(BaseModel):
    export_type: str  # CHALLENGES, PROJECTS, IMPACT_METRICS, AUDIT_LOGS
    export_format: str = "CSV"  # CSV, PDF
    filters: Optional[dict] = None

class ExportJobOut(BaseModel):
    id: int
    user_id: int
    export_type: str
    export_format: str
    status: str
    file_path: Optional[str] = None
    row_count: int
    failure_reason: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
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

# ----------------- STAGE 7: INDUSTRY / CSR / IP -----------------

class IndustryPartnerProfileUpdate(BaseModel):
    partner_type: Optional[PartnerType] = None
    legal_identity: Optional[str] = None
    registration_number: Optional[str] = None
    csr_eligible: Optional[bool] = None
    authorized_representative_name: Optional[str] = None
    authorized_representative_designation: Optional[str] = None
    domains: Optional[str] = None
    capacity_description: Optional[str] = None
    geographic_coverage: Optional[List[str]] = None
    compliance_documents: Optional[List[str]] = None
    notification_preferences: Optional[Dict[str, bool]] = None

class IndustryPartnerProfileOut(BaseModel):
    id: int
    company_name: str
    industry_domain: str
    partner_type: PartnerType
    legal_identity: Optional[str] = None
    registration_number: Optional[str] = None
    csr_eligible: bool = False
    authorized_representative_name: Optional[str] = None
    authorized_representative_designation: Optional[str] = None
    domains: Optional[str] = None
    capacity_description: Optional[str] = None
    geographic_coverage: Optional[str] = None
    compliance_documents: Optional[str] = None
    is_active: bool
    verification_status: str
    is_verified_active: bool
    model_config = ConfigDict(from_attributes=True)

class CollaborationOfferCreate(BaseModel):
    offer_type: CollaborationOfferType
    description: Optional[str] = None
    scope: str = Field(..., min_length=5)
    personnel: Optional[str] = None
    in_kind_value: Optional[float] = Field(None, ge=0)
    cash_value: Optional[float] = Field(None, ge=0)
    currency: str = "INR"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    dependencies: Optional[str] = None
    data_access_level: str = "RESTRICTED"  # NONE, RESTRICTED, FULL
    safety_requirements: Optional[str] = None
    deliverables: Optional[str] = None
    milestone_id: Optional[int] = None

class CollaborationReviewRequest(BaseModel):
    decision: str  # UNDER_REVIEW, CONFLICT_CHECK, ACCEPTED, CONTRACT_RECORDED, ACTIVE, COMPLETED, DECLINED, TERMINATED
    notes: str = Field(..., min_length=3)
    conflict_declared: Optional[bool] = None
    mou_evidence_object_id: Optional[str] = None

class CollaborationAgreementOut(BaseModel):
    id: int
    project_id: int
    company_name: str
    industry_domain: str
    offer_type: str
    description: Optional[str] = None
    agreement_status: AgreementStatus
    scope: Optional[str] = None
    personnel: Optional[str] = None
    in_kind_value: Optional[float] = None
    cash_value: Optional[float] = None
    currency: str = "INR"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    dependencies: Optional[str] = None
    data_access_level: Optional[str] = None
    safety_requirements: Optional[str] = None
    deliverables: Optional[str] = None
    milestone_id: Optional[int] = None
    review_notes: Optional[str] = None
    conflict_check_notes: Optional[str] = None
    conflict_declared: bool = False
    mou_evidence_object_id: Optional[str] = None
    version: int = 1
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FundingRecordCreate(BaseModel):
    collaboration_id: int
    milestone_id: Optional[int] = None
    budget_line_item: str = Field(..., min_length=3)
    amount: float = Field(..., gt=0)
    currency: str = "INR"
    sanction_authority: str = Field(..., min_length=3)
    agreement_reference: Optional[str] = None
    disbursement_schedule: Optional[str] = None

class FundingActionRequest(BaseModel):
    action: str  # APPROVE, HOLD, RELEASE, REVERSE
    notes: Optional[str] = None
    receipt_evidence_object_id: Optional[str] = None
    payment_integration_reference: Optional[str] = None

class FundingRecordOut(BaseModel):
    id: int
    collaboration_id: int
    project_id: int
    industry_id: int
    milestone_id: Optional[int] = None
    budget_line_item: str
    amount: float
    currency: str
    sanction_authority: Optional[str] = None
    agreement_reference: Optional[str] = None
    disbursement_schedule: Optional[str] = None
    hold_state: FundingHoldState
    receipt_evidence_object_id: Optional[str] = None
    utilization_notes: Optional[str] = None
    payment_integration_reference: Optional[str] = None
    settlement_status: str
    payment_confirmed: bool
    version: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IPRecordCreate(BaseModel):
    record_type: IPRecordType
    title: str = Field(..., min_length=3)
    description: Optional[str] = None
    background_ip_notes: Optional[str] = None
    foreground_ip_notes: Optional[str] = None
    ownership: IPOwnership = IPOwnership.JOINT
    license_terms: Optional[str] = None
    contributor_attributions: Optional[List[Dict[str, Any]]] = None
    publication_restrictions: Optional[str] = None
    patent_reference: Optional[str] = None
    software_repo_reference: Optional[str] = None
    design_reference: Optional[str] = None
    startup_spinoff_name: Optional[str] = None
    open_source_decision: Optional[bool] = None
    government_benefit_terms: Optional[str] = None
    collaboration_id: Optional[int] = None
    consent_party_user_ids: Optional[List[int]] = []

class IPConsentRespond(BaseModel):
    status: str  # ACCEPTED or REJECTED
    notes: Optional[str] = None

class IPConsentRecordOut(BaseModel):
    id: int
    party_user_id: int
    party_role: str
    status: IPConsentStatus
    notes: Optional[str] = None
    responded_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class IPRecordOut(BaseModel):
    id: int
    project_id: int
    collaboration_id: Optional[int] = None
    record_type: IPRecordType
    title: str
    description: Optional[str] = None
    background_ip_notes: Optional[str] = None
    foreground_ip_notes: Optional[str] = None
    ownership: IPOwnership
    license_terms: Optional[str] = None
    contributor_attributions: Optional[str] = None
    publication_restrictions: Optional[str] = None
    patent_reference: Optional[str] = None
    software_repo_reference: Optional[str] = None
    design_reference: Optional[str] = None
    startup_spinoff_name: Optional[str] = None
    open_source_decision: Optional[bool] = None
    government_benefit_terms: Optional[str] = None
    status: str
    consents: List[IPConsentRecordOut] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ModerationActionRequest(BaseModel):
    action: str  # FLAG, HIDE, RESTORE
    notes: Optional[str] = None

class RedactedProjectDiscoveryOut(BaseModel):
    id: int
    challenge_title: str
    university_name: str
    domain: str
    current_stage: str
    district_name: Optional[str] = None
    progress_band: str  # e.g. "0-25%", "25-50%" (banded, not exact, to reduce sensitive precision)
    seeking_support_types: List[str] = []

# ==========================================
# STAGE 10: Verifiable KPIs & Drill-Down Schemas
# ==========================================

class KPIMetadata(BaseModel):
    name: str
    display_title: str
    value: Union[float, int, str]
    unit: str = ""
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    time_window: str = "ALL_TIME"
    inclusion_rules: str
    freshness: str = "LIVE_TRANSACTIONAL"
    verification_level: str = "VERIFIED"  # REPORTED, ESTIMATED, MEASURED, VERIFIED
    reconciliation_metric_key: Optional[str] = None

class KPIDrillDownRecordOut(BaseModel):
    record_id: int
    entity_type: str
    title: str
    category: Optional[str] = None
    status: str
    district_name: Optional[str] = None
    block_name: Optional[str] = None
    verification_level: str
    contributing_value: Optional[Union[float, int, str]] = None
    timestamp: datetime
    audit_event_id: Optional[int] = None
    audit_tx_id: Optional[str] = None
    redacted: bool = False

class KPIDrillDownResponseOut(BaseModel):
    metric_key: str
    metadata: KPIMetadata
    total_records: int
    limit: int
    offset: int
    records: List[KPIDrillDownRecordOut]

class DistrictDrillDownOut(BaseModel):
    district_name: str
    total_challenges: int
    submitted: int
    under_review: int
    assigned: int
    in_progress: int
    resolved: int
    active_projects: int
    total_population: Optional[int] = None
    rural_population_pct: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class BlockDrillDownOut(BaseModel):
    district_name: str
    block_name: str
    total_challenges: int
    submitted: int
    under_review: int
    assigned: int
    in_progress: int
    resolved: int
    active_projects: int

class VerifiableAdminDashboardOut(BaseModel):
    total_challenges: int
    submitted: int
    under_review: int
    assigned: int
    in_progress: int
    resolved: int
    total_universities: int
    total_industry_partners: int
    total_students: int
    total_active_projects: int
    jurisdiction: dict
    tiers: dict
    kpis: Dict[str, KPIMetadata]

