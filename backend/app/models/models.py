import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    CITIZEN = "CITIZEN"
    COMMUNITY_ORG = "COMMUNITY_ORG"
    PRI = "PRI"
    ULB = "ULB"
    GOVERNMENT_OFFICER = "GOVERNMENT_OFFICER"
    GOVERNMENT_ADMIN = "GOVERNMENT_ADMIN"
    UNIVERSITY = "UNIVERSITY"
    FACULTY_MENTOR = "FACULTY_MENTOR"
    STUDENT = "STUDENT"
    INDUSTRY = "INDUSTRY"
    RESEARCH_LAB = "RESEARCH_LAB"
    INNOVATION_HUB = "INNOVATION_HUB"

class GovernmentScope(str, enum.Enum):
    PANCHAYAT = "PANCHAYAT"
    BLOCK = "BLOCK"
    DISTRICT = "DISTRICT"
    STATE = "STATE"

class AccountStatus(str, enum.Enum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"

class OrganizationVerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"

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
    IMPACT_AUDITED = "IMPACT_AUDITED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    PAUSED = "PAUSED"
    REOPENED = "REOPENED"

class ProjectStage(str, enum.Enum):
    INITIATION = "INITIATION"
    PLANNING = "PLANNING"
    PROTOTYPE = "PROTOTYPE"
    FIELD_TESTING = "FIELD_TESTING"
    DEPLOYMENT = "DEPLOYMENT"
    VERIFICATION = "VERIFICATION"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"

class AllocationStatus(str, enum.Enum):
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"

class AIJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"
    FALLBACK_COMPLETED = "FALLBACK_COMPLETED"

class MilestoneStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"

class TeamInvitationStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"

class MembershipAction(str, enum.Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    REPLACED = "REPLACED"

class ProposalStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    FACULTY_REVIEWED = "FACULTY_REVIEWED"
    HEI_APPROVED = "HEI_APPROVED"
    GOVERNMENT_REVIEWED = "GOVERNMENT_REVIEWED"
    INDUSTRY_FEEDBACK = "INDUSTRY_FEEDBACK"
    APPROVED = "APPROVED"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

class EvidenceReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    REJECTED = "REJECTED"

class FacilityType(str, enum.Enum):
    LAB = "LAB"
    EQUIPMENT = "EQUIPMENT"
    INCUBATION_CENTER = "INCUBATION_CENTER"
    INNOVATION_CENTER = "INNOVATION_CENTER"
    RESEARCH_CENTER = "RESEARCH_CENTER"

class CapabilityEvidenceType(str, enum.Enum):
    NAAC = "NAAC"
    NBA = "NBA"
    AISHE = "AISHE"
    NIRF = "NIRF"
    MOU = "MOU"
    ACCREDITATION = "ACCREDITATION"
    OTHER = "OTHER"

# ----------------- Stage 7: Industry / CSR / IP -----------------

class PartnerType(str, enum.Enum):
    INDUSTRY = "INDUSTRY"
    STARTUP = "STARTUP"
    MSME = "MSME"
    CSR_FOUNDATION = "CSR_FOUNDATION"
    RESEARCH_LAB = "RESEARCH_LAB"
    INNOVATION_HUB = "INNOVATION_HUB"

class CollaborationOfferType(str, enum.Enum):
    MENTORSHIP = "MENTORSHIP"
    TECHNICAL_SUPPORT = "TECHNICAL_SUPPORT"
    EQUIPMENT = "EQUIPMENT"
    PROTOTYPING = "PROTOTYPING"
    FUNDING = "FUNDING"
    TESTING = "TESTING"
    DEPLOYMENT = "DEPLOYMENT"
    RESEARCH_LAB_ACCESS = "RESEARCH_LAB_ACCESS"
    TECHNOLOGY_TRANSFER = "TECHNOLOGY_TRANSFER"

class AgreementStatus(str, enum.Enum):
    OFFERED = "OFFERED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CONFLICT_CHECK = "CONFLICT_CHECK"
    ACCEPTED = "ACCEPTED"
    CONTRACT_RECORDED = "CONTRACT_RECORDED"
    ACTIVE = "ACTIVE"
    MILESTONE_LINKED = "MILESTONE_LINKED"
    COMPLETED = "COMPLETED"
    DECLINED = "DECLINED"
    TERMINATED = "TERMINATED"

class FundingHoldState(str, enum.Enum):
    PENDING = "PENDING"
    HELD = "HELD"
    RELEASED = "RELEASED"
    REVERSED = "REVERSED"

class IPRecordType(str, enum.Enum):
    PATENT = "PATENT"
    SOFTWARE = "SOFTWARE"
    DESIGN = "DESIGN"
    TRADE_SECRET = "TRADE_SECRET"
    OPEN_SOURCE = "OPEN_SOURCE"

class IPOwnership(str, enum.Enum):
    UNIVERSITY = "UNIVERSITY"
    INDUSTRY = "INDUSTRY"
    JOINT = "JOINT"
    GOVERNMENT = "GOVERNMENT"
    INVENTOR = "INVENTOR"

class IPConsentStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class ChallengeSourceType(str, enum.Enum):
    CITIZEN_MOBILE = "CITIZEN_MOBILE"
    PRI_PORTAL = "PRI_PORTAL"
    ULB_DESK = "ULB_DESK"
    COMMUNITY_SURVEY = "COMMUNITY_SURVEY"
    GOVERNMENT_FIELD = "GOVERNMENT_FIELD"
    WEB_PORTAL = "WEB_PORTAL"

class ContactPreference(str, enum.Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    WHATSAPP = "WHATSAPP"

class DataSharingChoice(str, enum.Enum):
    PUBLIC = "PUBLIC"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    GOVERNMENT_ONLY = "GOVERNMENT_ONLY"

class AttachmentScanStatus(str, enum.Enum):
    PENDING = "PENDING"
    CLEAN = "CLEAN"
    INFECTED = "INFECTED"
    QUARANTINED = "QUARANTINED"

class AttachmentAccessClassification(str, enum.Enum):
    PUBLIC = "PUBLIC"
    RESTRICTED = "RESTRICTED"
    CONFIDENTIAL_EVIDENCE = "CONFIDENTIAL_EVIDENCE"

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
    account_status = Column(SQLEnum(AccountStatus, native_enum=False), default=AccountStatus.ACTIVE, nullable=False, index=True)
    password_changed_at = Column(DateTime, default=utc_now, nullable=False)
    district_name = Column(String(100), nullable=True, index=True)
    block_name = Column(String(100), nullable=True, index=True)
    panchayat_name = Column(String(100), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("government_departments.id"), nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255), nullable=True)
    id_provider = Column(String(50), default="LOCAL")
    id_provider_subject = Column(String(255), nullable=True)
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
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

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
    organization_profile_id = Column(Integer, ForeignKey("organization_profiles.id"), nullable=True, index=True)
    institution_name = Column(String(255), nullable=False, index=True)
    district_name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    has_incubation_center = Column(Boolean, default=True)
    has_innovation_center = Column(Boolean, default=True)
    facilities_description = Column(Text, nullable=True)
    nirf_ranking = Column(Integer, nullable=True)

    # Stage 6: Verified capability profile
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    capacity_max_active_projects = Column(Integer, default=10, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    user = relationship("User", back_populates="university_profile")
    organization_profile = relationship("OrganizationProfile", foreign_keys=[organization_profile_id])
    departments = relationship("Department", back_populates="university", cascade="all, delete-orphan")
    expertise_areas = relationship("UniversityExpertise", back_populates="university", cascade="all, delete-orphan")
    facilities = relationship("UniversityFacility", back_populates="university", cascade="all, delete-orphan")
    district_coverage = relationship("UniversityDistrictCoverage", back_populates="university", cascade="all, delete-orphan")
    capability_evidence = relationship("UniversityCapabilityEvidence", back_populates="university", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="university")
    assigned_challenges = relationship("Challenge", back_populates="assigned_university")

    @property
    def is_verified_active(self) -> bool:
        """A verified, active HEI: organization profile VERIFIED and university marked active."""
        if not self.is_active:
            return False
        if self.organization_profile is not None:
            return self.organization_profile.verification_status == "VERIFIED"
        return bool(self.user and self.user.is_verified)


class UniversityFacility(Base):
    __tablename__ = "university_facilities"

    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False, index=True)
    facility_type = Column(SQLEnum(FacilityType, native_enum=False), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    capacity_units = Column(Integer, nullable=True)
    is_operational = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    university = relationship("University", back_populates="facilities")


class UniversityDistrictCoverage(Base):
    __tablename__ = "university_district_coverage"

    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False, index=True)
    district_name = Column(String(100), nullable=False, index=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    university = relationship("University", back_populates="district_coverage")


class UniversityCapabilityEvidence(Base):
    __tablename__ = "university_capability_evidence"

    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False, index=True)
    evidence_type = Column(SQLEnum(CapabilityEvidenceType, native_enum=False), default=CapabilityEvidenceType.OTHER, nullable=False)
    title = Column(String(255), nullable=False)
    evidence_object_id = Column(String(64), nullable=True, index=True)  # links to EvidenceFile.object_id
    issued_by = Column(String(255), nullable=True)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    university = relationship("University", back_populates="capability_evidence")

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
    organization_profile_id = Column(Integer, ForeignKey("organization_profiles.id"), nullable=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    industry_domain = Column(String(150), nullable=False)
    contact_person = Column(String(150), nullable=True)
    website = Column(String(255), nullable=True)
    csr_focus_areas = Column(Text, nullable=True)
    technologies = Column(Text, nullable=True)
    available_support = Column(Text, nullable=True)  # Mentorship, funding, prototyping, pilot

    # Stage 7: Verified partner identity & capability profile
    partner_type = Column(SQLEnum(PartnerType, native_enum=False), default=PartnerType.INDUSTRY, nullable=False, index=True)
    legal_identity = Column(String(255), nullable=True)
    registration_number = Column(String(100), nullable=True)  # CIN / registration number
    csr_eligible = Column(Boolean, default=False, nullable=False)
    authorized_representative_name = Column(String(255), nullable=True)
    authorized_representative_designation = Column(String(150), nullable=True)
    domains = Column(Text, nullable=True)  # comma-separated or JSON list
    capacity_description = Column(Text, nullable=True)
    geographic_coverage = Column(Text, nullable=True)  # JSON list of district names
    compliance_documents = Column(Text, nullable=True)  # JSON list of EvidenceFile object_ids
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    suspended_reason = Column(Text, nullable=True)
    notification_preferences = Column(Text, nullable=True)  # JSON preferences
    version = Column(Integer, default=1, nullable=False)

    user = relationship("User", back_populates="industry_profile")
    organization_profile = relationship("OrganizationProfile", foreign_keys=[organization_profile_id])
    collaborations = relationship("IndustryCollaboration", back_populates="industry")

    @property
    def is_verified_active(self) -> bool:
        """A verified, active partner: organization profile VERIFIED and account active/unsuspended."""
        if not self.is_active:
            return False
        if self.organization_profile is not None:
            return self.organization_profile.verification_status == "VERIFIED"
        return bool(self.user and self.user.is_verified)

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

    # Submitter & Governance Modeling (Stage 3)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organization_profiles.id"), nullable=True, index=True)
    submitter_role = Column(String(50), nullable=True)
    source_type = Column(String(50), default="CITIZEN_MOBILE")
    contact_preference = Column(String(50), default="SMS")
    consent_version = Column(String(20), default="v1.0")
    consent_given = Column(Boolean, default=True)
    data_sharing_choice = Column(String(50), default="PUBLIC")
    accessibility_needs = Column(Text, nullable=True)
    submission_language = Column(String(10), default="en")
    original_title = Column(String(255), nullable=True)
    original_description = Column(Text, nullable=True)
    translation_status = Column(String(50), default="NONE")
    is_anonymous_public = Column(Boolean, default=False)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    citizen = relationship("Citizen", back_populates="challenges")
    submitted_by_user = relationship("User", foreign_keys=[submitted_by_user_id])
    organization = relationship("OrganizationProfile", foreign_keys=[organization_id])
    assigned_university = relationship("University", back_populates="assigned_challenges")
    allocations = relationship("ChallengeAllocation", back_populates="challenge", cascade="all, delete-orphan", order_by="desc(ChallengeAllocation.created_at)")
    location = relationship("ChallengeLocation", back_populates="challenge", uselist=False, cascade="all, delete-orphan")
    media = relationship("ChallengeMedia", back_populates="challenge", cascade="all, delete-orphan")
    attachments = relationship("ChallengeAttachment", back_populates="challenge", cascade="all, delete-orphan")
    ai_analysis = relationship("AIAnalysis", back_populates="challenge", uselist=False, cascade="all, delete-orphan")
    ai_overrides = relationship("AIHumanOverride", back_populates="challenge", cascade="all, delete-orphan", order_by="desc(AIHumanOverride.created_at)")
    ai_jobs = relationship("AIJob", back_populates="challenge", cascade="all, delete-orphan", order_by="desc(AIJob.created_at)")
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

    # Governance & Transparency Metadata (Stage 5)
    model_name = Column(String(100), default="JHARKHAND_TAXONOMY_CLASSIFIER_V2", nullable=False)
    model_version = Column(String(50), default="2.2.0", nullable=False)
    provider_name = Column(String(100), default="LOCAL_DETERMINISTIC_ENGINE", nullable=False)
    execution_time_ms = Column(Integer, default=0, nullable=False)
    input_snapshot_hash = Column(String(64), nullable=True)
    detected_language = Column(String(20), default="en", nullable=False)
    language_confidence = Column(Float, default=1.0, nullable=False)
    calibration_status = Column(String(50), default="CALIBRATED_FALLBACK", nullable=False)
    is_fallback = Column(Boolean, default=True, nullable=False)
    fallback_reason = Column(String(255), nullable=True)
    policy_version = Column(String(50), default="v2026.1", nullable=False)
    explanation = Column(Text, nullable=True)
    features_json = Column(Text, nullable=True)
    priority_breakdown_json = Column(Text, nullable=True)
    translated_title = Column(Text, nullable=True)
    translated_description = Column(Text, nullable=True)

    challenge = relationship("Challenge", back_populates="ai_analysis")
    overrides = relationship("AIHumanOverride", back_populates="ai_analysis", cascade="all, delete-orphan")

class ChallengeSimilarity(Base):
    __tablename__ = "challenge_similarity"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False, index=True)
    similar_challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)
    matched_keywords = Column(Text, nullable=True)

    # Decomposed Multi-factor Signals (Stage 5)
    text_similarity = Column(Float, default=0.0, nullable=False)
    geographic_similarity = Column(Float, default=0.0, nullable=False)
    temporal_similarity = Column(Float, default=0.0, nullable=False)
    category_similarity = Column(Float, default=0.0, nullable=False)
    explanation = Column(Text, nullable=True)
    dismissed = Column(Boolean, default=False, nullable=False)
    dismissed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    dismissal_reason = Column(Text, nullable=True)

    challenge = relationship("Challenge", foreign_keys=[challenge_id], back_populates="similarities")
    similar_challenge = relationship("Challenge", foreign_keys=[similar_challenge_id])
    dismissed_by_user = relationship("User", foreign_keys=[dismissed_by_user_id])

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

class ChallengeAllocation(Base):
    __tablename__ = "challenge_allocations"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False, index=True)
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_to_org_id = Column(Integer, ForeignKey("organization_profiles.id"), nullable=False, index=True)
    status = Column(SQLEnum(AllocationStatus), default=AllocationStatus.OFFERED, nullable=False, index=True)
    allocated_at = Column(DateTime, default=utc_now, nullable=False)
    deadline_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    response_notes = Column(Text, nullable=True)
    capacity_assessment = Column(Text, nullable=True)
    coi_declared = Column(Boolean, default=False, nullable=False)
    reassigned_from_allocation_id = Column(Integer, ForeignKey("challenge_allocations.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    challenge = relationship("Challenge", back_populates="allocations")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by_user_id])
    assigned_to_org = relationship("OrganizationProfile", foreign_keys=[assigned_to_org_id])
    reassigned_from = relationship("ChallengeAllocation", remote_side=[id])

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
    milestones_locked = Column(Boolean, default=False, nullable=False)
    faculty_mentor_status = Column(String(50), default="PENDING", nullable=False)  # PENDING, ACCEPTED, DECLINED
    version = Column(Integer, default=1, nullable=False)
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
    team_invitations = relationship("TeamInvitation", back_populates="project", cascade="all, delete-orphan")
    membership_history = relationship("ProjectMembershipHistory", back_populates="project", cascade="all, delete-orphan")

class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    role_in_team = Column(String(100), default="Researcher & Developer")
    invitation_id = Column(Integer, ForeignKey("team_invitations.id"), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    conflict_declared = Column(Boolean, default=False, nullable=False)
    conflict_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="members")
    student = relationship("Student", back_populates="project_memberships")
    department = relationship("Department")

class TeamInvitation(Base):
    __tablename__ = "team_invitations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    invited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    role_in_team = Column(String(100), default="Researcher & Developer")
    proposed_start_date = Column(DateTime, nullable=True)
    proposed_end_date = Column(DateTime, nullable=True)
    status = Column(SQLEnum(TeamInvitationStatus, native_enum=False), default=TeamInvitationStatus.PENDING, nullable=False, index=True)
    conflict_declared = Column(Boolean, default=False, nullable=False)
    conflict_notes = Column(Text, nullable=True)
    response_notes = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="team_invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    student = relationship("Student")
    faculty = relationship("Faculty")
    department = relationship("Department")

class ProjectMembershipHistory(Base):
    __tablename__ = "project_membership_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    action = Column(SQLEnum(MembershipAction, native_enum=False), nullable=False)
    previous_member_student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    role_in_team = Column(String(100), nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=True)
    occurred_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="membership_history")
    actor = relationship("User", foreign_keys=[actor_id])

class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    completion_percentage = Column(Float, default=0.0)
    weight_pct = Column(Float, default=20.0)  # Weights sum to 100% per project
    deliverable_files = Column(Text, nullable=True)  # JSON list of evidence/document links (legacy)
    status = Column(SQLEnum(MilestoneStatus), default=MilestoneStatus.NOT_STARTED)
    due_date = Column(DateTime, nullable=True)
    approved_by_faculty = Column(Boolean, default=False)
    approved_at = Column(DateTime, nullable=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="milestones")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])

class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    milestone_id = Column(Integer, ForeignKey("project_milestones.id"), nullable=True)
    title = Column(String(255), nullable=False)
    assigned_to_student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, SUBMITTED, REVISION_REQUESTED, APPROVED
    is_completed = Column(Boolean, default=False)
    due_date = Column(DateTime, nullable=True)
    submission_notes = Column(Text, nullable=True)
    submission_attachment = Column(String(500), nullable=True)  # legacy free-text (deprecated for new writes)

    project = relationship("Project", back_populates="tasks")
    milestone = relationship("ProjectMilestone")
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

    # Stage 6: Required structured fields
    objectives = Column(Text, nullable=True)
    feasibility_notes = Column(Text, nullable=True)
    budget_breakdown = Column(Text, nullable=True)
    risks = Column(Text, nullable=True)
    safeguarding_notes = Column(Text, nullable=True)
    maintenance_plan = Column(Text, nullable=True)
    measurable_outcomes = Column(Text, nullable=True)

    # Versioned workflow
    status = Column(SQLEnum(ProposalStatus, native_enum=False), default=ProposalStatus.DRAFT, nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    supersedes_id = Column(Integer, ForeignKey("solution_proposals.id"), nullable=True)
    is_current = Column(Boolean, default=True, nullable=False, index=True)

    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    faculty_reviewed_by_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    faculty_review_notes = Column(Text, nullable=True)
    hei_approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    hei_approval_notes = Column(Text, nullable=True)
    government_reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    government_review_notes = Column(Text, nullable=True)
    revision_requested_reason = Column(Text, nullable=True)

    submitted_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    is_approved_by_gov = Column(Boolean, default=False)  # legacy flag, mirrors status == APPROVED

    project = relationship("Project", back_populates="proposals")
    supersedes = relationship("SolutionProposal", remote_side=[id])
    submitted_by = relationship("User", foreign_keys=[submitted_by_user_id])
    faculty_reviewer = relationship("Faculty", foreign_keys=[faculty_reviewed_by_id])
    hei_approver = relationship("User", foreign_keys=[hei_approved_by_user_id])
    government_reviewer = relationship("User", foreign_keys=[government_reviewed_by_user_id])

class ReviewComment(Base):
    """
    Generic review/communication comment thread for proposals, milestones, deliverables,
    tasks, industry collaborations, funding records, and IP records.
    """
    __tablename__ = "review_comments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # PROPOSAL, MILESTONE, DELIVERABLE, TASK, COLLABORATION, FUNDING, IP_RECORD
    entity_id = Column(Integer, nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    # Moderation & retention (Stage 7)
    is_flagged = Column(Boolean, default=False, nullable=False)
    is_hidden = Column(Boolean, default=False, nullable=False)
    moderated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderation_action = Column(String(50), nullable=True)  # FLAGGED, HIDDEN, RESTORED
    moderation_notes = Column(Text, nullable=True)
    retention_state = Column(String(50), default="ACTIVE", nullable=False)

    project = relationship("Project")
    author = relationship("User", foreign_keys=[author_id])
    moderated_by = relationship("User", foreign_keys=[moderated_by_user_id])

class EvidenceFile(Base):
    """
    Secure, typed, versioned evidence substrate for milestone deliverables, task submissions,
    proposal attachments, and HEI capability evidence. Never exposes an arbitrary client-supplied URL.
    """
    __tablename__ = "evidence_files"

    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(String(64), unique=True, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # MILESTONE_DELIVERABLE, TASK_SUBMISSION, PROPOSAL_ATTACHMENT, UNIVERSITY_CAPABILITY, CSR_RECEIPT, IP_RECORD
    entity_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    version = Column(Integer, default=1, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)
    supersedes_id = Column(Integer, ForeignKey("evidence_files.id"), nullable=True)

    original_filename = Column(String(255), nullable=False)
    detected_mime = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256_checksum = Column(String(64), nullable=False)
    storage_key = Column(String(500), nullable=False)
    scan_status = Column(String(50), default="CLEAN")
    access_classification = Column(String(50), default="RESTRICTED")

    review_status = Column(SQLEnum(EvidenceReviewStatus, native_enum=False), default=EvidenceReviewStatus.PENDING, nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utc_now)

    owner = relationship("User", foreign_keys=[owner_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    project = relationship("Project", foreign_keys=[project_id])
    supersedes = relationship("EvidenceFile", remote_side=[id])

class IndustryCollaboration(Base):
    __tablename__ = "industry_collaborations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    industry_id = Column(Integer, ForeignKey("industry_partners.id"), nullable=False)
    offer_type = Column(String(100), nullable=False)  # Mentorship, Technical Support, Prototype Support, Funding, Pilot Implementation
    description = Column(Text, nullable=True)
    status = Column(String(50), default="Offered")  # legacy free-text mirror of agreement_status
    created_at = Column(DateTime, default=utc_now)

    # Stage 7: structured agreement workflow
    agreement_status = Column(SQLEnum(AgreementStatus, native_enum=False), default=AgreementStatus.OFFERED, nullable=False, index=True)
    scope = Column(Text, nullable=True)
    personnel = Column(Text, nullable=True)  # named contacts/roles
    in_kind_value = Column(Float, nullable=True)
    cash_value = Column(Float, nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    dependencies = Column(Text, nullable=True)
    data_access_level = Column(String(50), default="RESTRICTED")  # NONE, RESTRICTED, FULL
    safety_requirements = Column(Text, nullable=True)
    deliverables = Column(Text, nullable=True)
    milestone_id = Column(Integer, ForeignKey("project_milestones.id"), nullable=True)

    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    conflict_check_notes = Column(Text, nullable=True)
    conflict_declared = Column(Boolean, default=False, nullable=False)
    mou_evidence_object_id = Column(String(64), nullable=True)  # server-generated evidence reference
    accepted_at = Column(DateTime, nullable=True)
    terminated_reason = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="collaborations")
    industry = relationship("IndustryPartner", back_populates="collaborations")
    milestone = relationship("ProjectMilestone")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])
    funding_records = relationship("FundingRecord", back_populates="collaboration", cascade="all, delete-orphan")


class FundingRecord(Base):
    """
    CSR / funding governance ledger. Never claims a payment transferred unless a
    configured finance/payment integration confirms it — see settlement_status.
    """
    __tablename__ = "funding_records"

    id = Column(Integer, primary_key=True, index=True)
    collaboration_id = Column(Integer, ForeignKey("industry_collaborations.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    industry_id = Column(Integer, ForeignKey("industry_partners.id"), nullable=False, index=True)
    milestone_id = Column(Integer, ForeignKey("project_milestones.id"), nullable=True)

    budget_line_item = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    sanction_authority = Column(String(255), nullable=True)  # approving officer name/role
    agreement_reference = Column(String(255), nullable=True)
    disbursement_schedule = Column(Text, nullable=True)  # JSON list of {date, amount, condition}

    hold_state = Column(SQLEnum(FundingHoldState, native_enum=False), default=FundingHoldState.PENDING, nullable=False, index=True)
    receipt_evidence_object_id = Column(String(64), nullable=True)
    utilization_notes = Column(Text, nullable=True)

    # Payment/finance integration confirmation gate — never inferred from a client claim.
    payment_integration_reference = Column(String(255), nullable=True)
    settlement_status = Column(String(50), default="PENDING_EXTERNAL_CONFIRMATION", nullable=False)
    payment_confirmed = Column(Boolean, default=False, nullable=False)

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    collaboration = relationship("IndustryCollaboration", back_populates="funding_records")
    project = relationship("Project")
    industry = relationship("IndustryPartner")
    milestone = relationship("ProjectMilestone")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])


class IPRecord(Base):
    """Intellectual property & technology-transfer record with multi-party consent."""
    __tablename__ = "ip_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    collaboration_id = Column(Integer, ForeignKey("industry_collaborations.id"), nullable=True)

    record_type = Column(SQLEnum(IPRecordType, native_enum=False), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    background_ip_notes = Column(Text, nullable=True)
    foreground_ip_notes = Column(Text, nullable=True)
    ownership = Column(SQLEnum(IPOwnership, native_enum=False), default=IPOwnership.JOINT, nullable=False)
    license_terms = Column(Text, nullable=True)
    contributor_attributions = Column(Text, nullable=True)  # JSON list of {user_id, name, role, share}
    publication_restrictions = Column(Text, nullable=True)
    patent_reference = Column(String(255), nullable=True)
    software_repo_reference = Column(String(255), nullable=True)
    design_reference = Column(String(255), nullable=True)
    startup_spinoff_name = Column(String(255), nullable=True)
    open_source_decision = Column(Boolean, nullable=True)
    government_benefit_terms = Column(Text, nullable=True)

    status = Column(String(50), default="DRAFT", nullable=False, index=True)  # DRAFT, PENDING_CONSENT, APPROVED, REJECTED, ARCHIVED
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("Project")
    collaboration = relationship("IndustryCollaboration")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    consents = relationship("IPConsentRecord", back_populates="ip_record", cascade="all, delete-orphan")


class IPConsentRecord(Base):
    """Per-party consent tracking required before an IPRecord can be finally closed."""
    __tablename__ = "ip_consent_records"

    id = Column(Integer, primary_key=True, index=True)
    ip_record_id = Column(Integer, ForeignKey("ip_records.id"), nullable=False, index=True)
    party_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    party_role = Column(String(50), nullable=False)  # STUDENT, FACULTY_MENTOR, UNIVERSITY, INDUSTRY, GOVERNMENT_ADMIN
    status = Column(SQLEnum(IPConsentStatus, native_enum=False), default=IPConsentStatus.PENDING, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    ip_record = relationship("IPRecord", back_populates="consents")
    party = relationship("User", foreign_keys=[party_user_id])

class ProjectDocument(Base):
    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    doc_type = Column(String(50), default="Report")
    file_url = Column(String(500), nullable=False)  # server-generated secure reference, never client-supplied
    evidence_object_id = Column(String(64), nullable=True, index=True)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="documents")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id])

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
    category = Column(String(50), default="GENERAL", nullable=False)
    deep_link = Column(String(255), nullable=True)
    retention_days = Column(Integer, default=90, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="notifications")
    outbox_items = relationship("NotificationOutbox", back_populates="notification", cascade="all, delete-orphan")

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


class DomainAuditEvent(Base):
    __tablename__ = "domain_audit_events"

    id = Column(Integer, primary_key=True, index=True)
    sequence_number = Column(BigInteger, unique=True, nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)
    previous_state = Column(String(64), nullable=True)
    new_state = Column(String(64), nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    actor_role = Column(String(64), nullable=True)
    jurisdiction_level = Column(String(64), nullable=True)
    jurisdiction_value = Column(String(128), nullable=True)
    reason_code = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=False)  # Canonical JSON representation
    payload_hash = Column(String(64), nullable=False)
    prev_event_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=False, index=True)
    is_internal = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, index=True)

    actor = relationship("User", foreign_keys=[actor_id])


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
    inspector_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    inspector_organization_id = Column(Integer, ForeignKey("organization_profiles.id"), nullable=True)
    assignment_id = Column(String(100), nullable=True)
    verification_status = Column(String(50), default="SUBMITTED", index=True)  # SUBMITTED, VERIFIED, REJECTED
    evidence_urls = Column(Text, nullable=True)  # JSON array of proof files
    checklist_responses = Column(Text, nullable=True)  # JSON structured checklist
    visit_timestamp = Column(DateTime, nullable=True)
    device_metadata = Column(Text, nullable=True)  # JSON device/timestamp evidence
    before_media_urls = Column(Text, nullable=True)  # JSON array
    after_media_urls = Column(Text, nullable=True)  # JSON array
    lab_report_references = Column(Text, nullable=True)  # JSON lab IDs & test parameters
    beneficiary_sample_size = Column(Integer, nullable=True)
    beneficiary_feedback_summary = Column(Text, nullable=True)
    geotagged_lat = Column(Float, nullable=True)
    geotagged_lng = Column(Float, nullable=True)
    inspection_notes = Column(Text, nullable=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_decision = Column(String(50), nullable=True)
    review_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project")
    milestone = relationship("ProjectMilestone")
    inspector = relationship("User", foreign_keys=[inspector_user_id])
    inspector_organization = relationship("OrganizationProfile", foreign_keys=[inspector_organization_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])


class OutcomeMetric(Base):
    __tablename__ = "outcome_metrics"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name = Column(String(255), nullable=False, index=True)
    metric_definition = Column(Text, nullable=False)
    metric_type = Column(String(50), default="QUANTITATIVE", nullable=False)  # QUANTITATIVE, QUALITATIVE
    unit_of_measure = Column(String(50), nullable=True)
    baseline_value = Column(String(100), nullable=False)
    baseline_date = Column(DateTime, default=utc_now, nullable=False)
    baseline_source = Column(String(255), nullable=False)
    target_value = Column(String(100), nullable=False)
    target_date = Column(DateTime, nullable=True)
    actual_value = Column(String(100), nullable=True)
    actual_date = Column(DateTime, nullable=True)
    actual_source = Column(String(255), nullable=True)
    collection_method = Column(String(100), nullable=True)
    sample_size = Column(Integer, nullable=True)
    uncertainty_margin = Column(String(50), nullable=True)
    responsible_org_name = Column(String(255), nullable=True)
    responsible_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    evidence_references = Column(Text, nullable=True)  # JSON array
    district_name = Column(String(100), nullable=True)
    block_name = Column(String(100), nullable=True)
    verification_status = Column(String(50), default="REPORTED", nullable=False)  # REPORTED, ESTIMATED, MEASURED, INDEPENDENTLY_VERIFIED
    verified_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project")
    challenge = relationship("Challenge")
    responsible_user = relationship("User", foreign_keys=[responsible_user_id])
    verified_by = relationship("User", foreign_keys=[verified_by_user_id])


class CitizenFeedback(Base):
    __tablename__ = "citizen_feedback"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    challenge_version = Column(Integer, default=1, nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5
    is_issue_resolved = Column(Boolean, default=True)
    satisfaction_score = Column(Float, default=5.0)
    comments = Column(Text, nullable=False)
    original_comments = Column(Text, nullable=True)
    evidence_photo_url = Column(String(500), nullable=True)
    beneficiary_verification_type = Column(String(50), default="ORIGINAL_REPORTER", nullable=False)  # ORIGINAL_REPORTER, VERIFIED_RESIDENT, INVITATION_TOKEN
    invitation_token = Column(String(100), nullable=True)
    moderation_status = Column(String(50), default="APPROVED", nullable=False)  # APPROVED, PENDING, FLAGGED, REDACTED
    moderated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderation_reason = Column(Text, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    appeal_status = Column(String(50), default="NONE", nullable=False)  # NONE, APPEALED, UPHELD, REJECTED
    appeal_reason = Column(Text, nullable=True)
    accessibility_needs = Column(String(100), nullable=True)
    language = Column(String(20), default="en", nullable=False)
    submitted_at = Column(DateTime, default=utc_now)

    challenge = relationship("Challenge")
    citizen = relationship("Citizen")
    user = relationship("User", foreign_keys=[user_id])
    moderated_by = relationship("User", foreign_keys=[moderated_by_user_id])


class ProjectClosureRecord(Base):
    __tablename__ = "project_closure_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    closed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    closure_decision = Column(String(50), nullable=False)  # APPROVED_CLOSED, REJECTED_REVISION, ESCALATED_REOPENED
    preconditions_snapshot_json = Column(Text, nullable=False)
    ip_cleared = Column(Boolean, default=True, nullable=False)
    ip_handover_details = Column(Text, nullable=True)
    maintenance_handover_plan = Column(Text, nullable=False)
    handover_recipient_org = Column(String(255), nullable=False)
    closure_remarks = Column(Text, nullable=False)
    closed_at = Column(DateTime, default=utc_now, nullable=False)

    project = relationship("Project")
    challenge = relationship("Challenge")
    closed_by = relationship("User", foreign_keys=[closed_by_user_id])


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), unique=True, nullable=False, index=True)
    revoked_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=False)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    refresh_token_hash = Column(String(64), nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    revoked_reason = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_used_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="sessions")


class OTPChallenge(Base):
    __tablename__ = "otp_challenges"

    id = Column(Integer, primary_key=True, index=True)
    account_identifier = Column(String(255), nullable=False, index=True)
    otp_hash = Column(String(64), nullable=False)
    purpose = Column(String(50), nullable=False, default="PASSWORD_RESET")
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    delivery_status = Column(String(50), default="PENDING")
    is_used = Column(Boolean, default=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now)
    ip_address = Column(String(45), nullable=True)


class ChallengeAttachment(Base):
    __tablename__ = "challenge_attachments"

    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(String(64), unique=True, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    detected_mime = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256_checksum = Column(String(64), nullable=False)
    storage_key = Column(String(500), nullable=False)
    scan_status = Column(String(50), default="CLEAN")
    access_classification = Column(String(50), default="RESTRICTED")
    retention_state = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=utc_now)

    owner = relationship("User")
    challenge = relationship("Challenge", back_populates="attachments")


class ChallengeDraft(Base):
    __tablename__ = "challenge_drafts"

    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    idempotency_key = Column(String(128), index=True, nullable=True)
    payload_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User")


class TaxonomyDomain(Base):
    __tablename__ = "taxonomy_domains"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    icon_name = Column(String(50), default="category")
    is_active = Column(Boolean, default=True)

    subdomains = relationship("TaxonomySubdomain", back_populates="domain", cascade="all, delete-orphan")


class TaxonomySubdomain(Base):
    __tablename__ = "taxonomy_subdomains"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("taxonomy_domains.id"), nullable=False, index=True)
    code = Column(String(100), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    domain = relationship("TaxonomyDomain", back_populates="subdomains")


class AIJob(Base):
    """
    Durable persistent outbox job queue for asynchronous AI analysis.
    Supports idempotency, exponential backoff, dead-letter state, and observable status.
    """
    __tablename__ = "ai_jobs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False, index=True)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    job_type = Column(String(50), default="FULL_ANALYSIS", nullable=False)
    status = Column(SQLEnum(AIJobStatus), default=AIJobStatus.PENDING, nullable=False, index=True)
    payload_json = Column(Text, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    backoff_seconds = Column(Integer, default=5, nullable=False)
    next_run_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    timeout_seconds = Column(Integer, default=60, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    challenge = relationship("Challenge", back_populates="ai_jobs")


class AIHumanOverride(Base):
    """
    Auditable Human-in-the-Loop decision record.
    Never overwrites the original AI output, preserving reproducibility and accountability.
    """
    __tablename__ = "ai_human_overrides"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False, index=True)
    analysis_id = Column(Integer, ForeignKey("ai_analysis.id"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    decision_type = Column(String(50), nullable=False)  # DOMAIN_OVERRIDE, PRIORITY_OVERRIDE, DUPLICATE_DECISION, UNIVERSITY_OVERRIDE, FULL_ACCEPTANCE
    original_value = Column(Text, nullable=False)
    override_value = Column(Text, nullable=False)
    mandatory_reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    challenge = relationship("Challenge", back_populates="ai_overrides")
    ai_analysis = relationship("AIAnalysis", back_populates="overrides")
    reviewer = relationship("User", foreign_keys=[reviewer_id])


class AIPriorityWeightConfig(Base):
    """
    Configurable, versioned multi-factor priority weights.
    Weights are transparently configured and versioned, not hidden in code.
    """
    __tablename__ = "ai_priority_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_version = Column(String(50), unique=True, nullable=False, index=True)
    weights_json = Column(Text, nullable=False)
    thresholds_json = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class AIModelGovernance(Base):
    """
    Model Registry & Change Approval Record.
    Tracks model versions, approval status, benchmark metrics, and audit log.
    """
    __tablename__ = "ai_model_governance"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    provider_name = Column(String(100), nullable=False)
    task_type = Column(String(50), nullable=False)  # CLASSIFICATION, PRIORITY, DEDUPLICATION, MATCHING, TRANSLATION
    approval_status = Column(String(50), default="STAGING", nullable=False)  # STAGING, APPROVED, DEPRECATED
    benchmark_metrics_json = Column(Text, nullable=True)
    changelog = Column(Text, nullable=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


# ==========================================
# STAGE 9: Notifications Outbox & Preferences
# ==========================================

class NotificationOutbox(Base):
    """
    Durable Outbox Queue for External Notifications (Email, SMS, Push, WhatsApp).
    Guarantees observable delivery states, retries, failure reasons, and template versioning.
    """
    __tablename__ = "notification_outbox"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(30), nullable=False)  # IN_APP, EMAIL, SMS, PUSH, WHATSAPP
    provider = Column(String(100), nullable=False)  # NIC_SMS_GATEWAY, STATE_EMAIL_RELAY, FCM_PUSH
    recipient = Column(String(255), nullable=False)  # Phone number, email, or device token
    template_id = Column(String(100), nullable=True)
    template_version = Column(String(20), nullable=True)
    locale = Column(String(10), default="en", nullable=False)
    delivery_status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING, SENDING, SENT, FAILED, CANCELLED
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    failure_reason = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    last_attempt_at = Column(DateTime, nullable=True)

    notification = relationship("Notification", back_populates="outbox_items")
    user = relationship("User")


class UserNotificationPreference(Base):
    """
    Citizen, Official, and Organization Notification Preferences & Consent.
    Tracks channel toggles, language, category alert subscriptions, and statutory consent.
    """
    __tablename__ = "user_notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    email_enabled = Column(Boolean, default=True, nullable=False)
    sms_enabled = Column(Boolean, default=False, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    whatsapp_enabled = Column(Boolean, default=False, nullable=False)
    preferred_locale = Column(String(10), default="en", nullable=False)  # en, hi, sat, unr, hoc, kru, khortha
    categories_json = Column(Text, nullable=True)  # JSON map of category toggles
    consent_given = Column(Boolean, default=True, nullable=False)
    consent_timestamp = Column(DateTime, default=utc_now, nullable=False)
    consent_version = Column(String(20), default="v1.0", nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User")


# ==========================================
# STAGE 10: Bounded Asynchronous Export Jobs
# ==========================================

class ExportJob(Base):
    """
    Tracks server-side asynchronous bounded report export requests.
    Prevents memory exhaustion and enables auditable data extraction.
    """
    __tablename__ = "export_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    export_type = Column(String(50), nullable=False)  # CHALLENGES, PROJECTS, IMPACT_METRICS, AUDIT_LOGS
    export_format = Column(String(20), default="CSV", nullable=False)  # CSV, PDF
    filters_json = Column(Text, nullable=True)
    status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING, PROCESSING, COMPLETED, FAILED
    file_path = Column(String(500), nullable=True)
    row_count = Column(Integer, default=0, nullable=False)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User")


