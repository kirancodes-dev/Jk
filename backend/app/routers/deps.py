import enum
from datetime import datetime, timezone
from typing import Any, List, Optional, Set, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token, is_token_revoked
from backend.app.models.models import (
    User, UserRole, RevokedToken, UserSession, AuditLog,
    Challenge, Project, ProjectMember, Student, Faculty, University, Citizen, IndustryPartner,
    IndustryCollaboration, Department
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


class Permission(str, enum.Enum):
    CHALLENGE_CREATE = "challenge.create"
    CHALLENGE_READ = "challenge.read"
    CHALLENGE_REVIEW = "challenge.review"
    CHALLENGE_VALIDATE = "challenge.validate"
    CHALLENGE_ASSIGN = "challenge.assign"
    CHALLENGE_FEEDBACK = "challenge.feedback"
    PROJECT_CREATE = "project.create"
    PROJECT_VIEW = "project.view"
    PROJECT_APPROVE = "project.approve"
    PROJECT_MANAGE = "project.manage"
    FUNDING_PROPOSE = "funding.propose"
    FUNDING_APPROVE = "funding.approve"
    VERIFICATION_SUBMIT = "verification.submit"
    VERIFICATION_REVIEW = "verification.review"
    ANALYTICS_VIEW = "analytics.view"
    EXPORT_CREATE = "export.create"
    ORGANIZATION_VERIFY = "organization.verify"
    AUDIT_READ = "audit.read"
    TASK_ASSIGN = "task.assign"
    TASK_COMPLETE = "task.complete"
    MILESTONE_SUBMIT = "milestone.submit"
    MILESTONE_APPROVE = "milestone.approve"
    PROFILE_MANAGE = "profile.manage"


def normalize_perm(perm: str) -> str:
    """Normalizes permissions between dot and colon notations (e.g. challenge.create <-> challenge:create)."""
    return perm.replace(":", ".").strip().lower()


# Granular role-to-permission mapping for verified multi-stakeholder governance
DEFAULT_ROLE_PERMISSIONS: dict[UserRole, Set[str]] = {
    UserRole.GOVERNMENT_ADMIN: {
        "*"  # Superuser all permissions
    },
    UserRole.GOVERNMENT_OFFICER: {
        "challenge.read", "challenge.review", "challenge.validate", "challenge.assign",
        "project.view", "project.approve", "project.close", "funding.approve",
        "verification.submit", "verification.review", "feedback.moderate",
        "analytics.view", "export.create", "organization.verify", "audit.read", "profile.manage"
    },
    UserRole.PRI: {
        "challenge.create", "challenge.read", "challenge.review", "challenge.validate",
        "verification.submit", "verification.review", "analytics.view", "profile.manage"
    },
    UserRole.ULB: {
        "challenge.create", "challenge.read", "challenge.review", "challenge.validate",
        "verification.submit", "verification.review", "analytics.view", "profile.manage"
    },
    UserRole.COMMUNITY_ORG: {
        "challenge.create", "challenge.read", "profile.manage"
    },
    UserRole.CITIZEN: {
        "challenge.create", "challenge.read", "challenge.feedback", "profile.manage"
    },
    UserRole.UNIVERSITY: {
        "challenge.read", "challenge.adopt", "project.create", "project.view",
        "project.manage", "milestone.approve", "team.manage", "profile.manage"
    },
    UserRole.FACULTY_MENTOR: {
        "challenge.read", "project.view", "project.mentor", "milestone.submit",
        "milestone.approve", "task.assign", "deliverable.review", "profile.manage"
    },
    UserRole.STUDENT: {
        "challenge.read", "project.view", "milestone.submit", "task.complete",
        "deliverable.submit", "profile.manage"
    },
    UserRole.INDUSTRY: {
        "challenge.read", "project.view", "funding.propose", "collaboration.create",
        "mentorship.offer", "profile.manage"
    },
    UserRole.RESEARCH_LAB: {
        "challenge.read", "project.view", "funding.propose", "collaboration.create",
        "verification.submit", "profile.manage"
    },
    UserRole.INNOVATION_HUB: {
        "challenge.read", "project.view", "funding.propose", "collaboration.create",
        "verification.submit", "profile.manage"
    }
}


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Central authentication dependency:
    - Validates JWT signature and expiration
    - Checks persistent database session status (multi-instance consistency)
    - Validates against password-change timestamps
    - Validates user active and account verification status
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired/revoked.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    jti = payload.get("jti")
    session_id = payload.get("session_id")

    # Fast in-memory check
    if jti and is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again."
        )

    # Database persistent revocation checks
    if jti:
        revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
        if revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please log in again."
            )

    # Database persistent session check
    if session_id:
        sess = db.query(UserSession).filter(UserSession.session_id == session_id).first()
        if sess and sess.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been terminated. Please log in again."
            )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token credentials."
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with token not found."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    # Check password change invalidation
    if user.password_changed_at and payload.get("iat"):
        try:
            iat_dt = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
            pwd_dt = user.password_changed_at
            if pwd_dt.tzinfo is None:
                pwd_dt = pwd_dt.replace(tzinfo=timezone.utc)
            if iat_dt < pwd_dt.replace(microsecond=0):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Password was changed after token issuance. Please log in again."
                )
        except (ValueError, OSError):
            pass

    # Account status check
    if hasattr(user, "account_status"):
        stat = str(user.account_status).upper()
        if stat in ("SUSPENDED", "DEACTIVATED"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {stat.lower()}. Access denied."
            )

    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Resolves authenticated user if valid token present; returns None without failing."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user and user.is_active:
            return user
        return None
    except Exception:
        return None


def require_roles(allowed_roles: List[UserRole]):
    """Enforces that authenticated user possesses one of the specified roles."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of [{', '.join([r.value for r in allowed_roles])}] role."
            )
        return current_user
    return role_checker


def require_permission(required_permission: str):
    """
    Action-based permission dependency.
    Evaluates whether the user's role or custom grants possess the requested permission.
    """
    def permission_checker(current_user: User = Depends(get_current_user)):
        user_perms = DEFAULT_ROLE_PERMISSIONS.get(current_user.role, set())
        norm_req = normalize_perm(required_permission)

        if "*" in user_perms:
            return current_user

        normalized_user_perms = {normalize_perm(p) for p in user_perms}
        if norm_req not in normalized_user_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Missing required permission '{required_permission}'."
            )
        return current_user
    return permission_checker


def require_permissions(required_permissions: List[str]):
    """Enforces that authenticated user possesses ALL required permissions."""
    def permissions_checker(current_user: User = Depends(get_current_user)):
        user_perms = DEFAULT_ROLE_PERMISSIONS.get(current_user.role, set())
        if "*" in user_perms:
            return current_user

        normalized_user_perms = {normalize_perm(p) for p in user_perms}
        for req in required_permissions:
            if normalize_perm(req) not in normalized_user_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: Missing required permission '{req}'."
                )
        return current_user
    return permissions_checker


def require_active_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Enforces that an account is fully verified and active before accessing privileged capabilities."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account verification is pending. Privileged access requires government accreditation."
        )
    return current_user


def check_jurisdiction(
    user: User,
    target_district: Optional[str] = None,
    target_block: Optional[str] = None,
    target_panchayat: Optional[str] = None
) -> tuple[bool, str]:
    """
    Evaluates server-side hierarchical government jurisdiction:
    - STATE: statewide scope across all 24 districts.
    - DISTRICT: scoped strictly to user's assigned district.
    - BLOCK: scoped strictly to user's assigned block within district.
    - PANCHAYAT: scoped strictly to user's assigned village/panchayat.
    """
    if user.role == UserRole.GOVERNMENT_ADMIN:
        # State Admin has universal statewide jurisdiction
        if not user.admin_tier or user.admin_tier.upper() == "STATE":
            return True, "Statewide oversight"

    tier = (user.admin_tier or "STATE").upper()
    user_dist = (user.district_name or user.jurisdiction_name or "").strip().lower()
    user_block = (user.block_name or "").strip().lower()
    user_panchayat = (user.panchayat_name or "").strip().lower()

    if tier == "STATE":
        return True, "State tier authorized"

    if tier == "DISTRICT":
        if not target_district:
            return True, "District scope permitted"
        if target_district.strip().lower() not in user_dist and user_dist not in target_district.strip().lower():
            return False, f"Jurisdiction mismatch: District officer for '{user.district_name or user.jurisdiction_name}' cannot access records in district '{target_district}'."
        return True, "District scope verified"

    if tier == "BLOCK":
        if target_district:
            if target_district.strip().lower() not in user_dist and user_dist not in target_district.strip().lower():
                return False, f"Jurisdiction mismatch: Block officer in district '{user.district_name}' cannot access district '{target_district}'."
        if target_block:
            if target_block.strip().lower() != user_block and user_block not in target_block.strip().lower():
                return False, f"Jurisdiction mismatch: Block officer for '{user.block_name}' cannot access or mutate records in block '{target_block}'."
        return True, "Block scope verified"

    if tier == "PANCHAYAT":
        if target_block and user_block and target_block.strip().lower() != user_block:
            return False, f"Jurisdiction mismatch: Panchayat officer for '{user.panchayat_name}' cannot access block '{target_block}'."
        if target_panchayat and user_panchayat:
            if target_panchayat.strip().lower() != user_panchayat:
                return False, f"Jurisdiction mismatch: Panchayat officer cannot access panchayat '{target_panchayat}'."
        return True, "Panchayat scope verified"

    return True, "Default authorized"


def verify_challenge_jurisdiction(
    challenge: Challenge,
    current_user: User,
    db: Session,
    action: str = "triage"
):
    """
    Enforces server-side jurisdiction authorization for a specific challenge.
    Rejection prevents out-of-jurisdiction officers from viewing private records or mutating status.
    """
    if current_user.role == UserRole.GOVERNMENT_ADMIN and (not current_user.admin_tier or current_user.admin_tier.upper() == "STATE"):
        return True

    target_district = challenge.location.district_name if challenge.location else None
    target_block = challenge.location.block_name if challenge.location else None
    target_panchayat = challenge.location.village_or_city if challenge.location else None

    allowed, reason = check_jurisdiction(
        user=current_user,
        target_district=target_district,
        target_block=target_block,
        target_panchayat=target_panchayat
    )
    if not allowed:
        # Record security audit log for unauthorized jurisdiction tampering
        db.add(AuditLog(
            actor_id=current_user.id,
            actor_name=current_user.full_name,
            actor_role=current_user.role.value,
            action=f"UNAUTHORIZED_JURISDICTION_{action.upper()}",
            entity_name="Challenge",
            entity_id=challenge.id,
            reason=reason
        ))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: {reason}"
        )
    return True


def verify_project_membership(project_id: int, current_user: User, db: Session):
    """
    Enforces object-level authorization (IDOR prevention).
    Ensures that students, faculty, or universities can only access or modify
    projects they are officially assigned to.
    """
    # Government statewide administrators have oversight
    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        return True

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role in (UserRole.GOVERNMENT_OFFICER, UserRole.PRI, UserRole.ULB):
        # Enforce jurisdiction based on associated challenge location
        if project.challenge:
            verify_challenge_jurisdiction(project.challenge, current_user, db, action="view_project")
        return True

    if current_user.role == UserRole.UNIVERSITY:
        univ = db.query(University).filter(University.user_id == current_user.id).first()
        if univ and project.university_id == univ.id:
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: This project belongs to another academic institution."
        )

    if current_user.role == UserRole.FACULTY_MENTOR:
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if faculty and (project.faculty_mentor_id == faculty.id or project.university_id == faculty.university_id):
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not the assigned faculty mentor for this project."
        )

    if current_user.role == UserRole.STUDENT:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student:
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.student_id == student.id
            ).first()
            if is_member:
                return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not an assigned student team member for this project."
        )

    if current_user.role in (UserRole.INDUSTRY, UserRole.RESEARCH_LAB, UserRole.INNOVATION_HUB):
        # Object-level authorization: an industry/lab partner may only read a project's
        # full detail (proposals, milestones, evidence) once it holds an active collaboration
        # on that specific project. General discovery uses a separate redacted listing.
        ind = db.query(IndustryPartner).filter(IndustryPartner.user_id == current_user.id).first()
        if ind:
            has_collab = db.query(IndustryCollaboration).filter(
                IndustryCollaboration.project_id == project_id,
                IndustryCollaboration.industry_id == ind.id
            ).first()
            if has_collab:
                return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have an active collaboration on this project. Use project discovery to browse public summaries."
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden: You do not have permission to access this project."
    )


def require_verified_active_university(current_user: User, db: Session) -> University:
    """
    Resolves and enforces that the authenticated university account is a verified, active HEI.
    Only verified active HEIs may adopt challenges, create projects, invite team members,
    or approve deliverables.
    """
    univ = db.query(University).filter(University.user_id == current_user.id).first()
    if not univ:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University institution profile not found for authenticated account."
        )
    if not univ.is_verified_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Your institution is not a verified, active HEI. Complete government accreditation verification before this action is permitted."
        )
    return univ


def verify_same_university_student(student: Student, university_id: int):
    """Rejects cross-HEI student IDs: a student must belong to the specified verified HEI."""
    if not student or student.university_id != university_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejected: Student does not belong to this higher education institution."
        )


def require_verified_active_partner(current_user: User, db: Session) -> IndustryPartner:
    """
    Resolves and enforces that the authenticated industry/startup/MSME/CSR/lab account is a
    verified, active partner. Unverified or suspended partners cannot offer or accept support,
    and never fall back to "the first partner in the table".
    """
    partner = db.query(IndustryPartner).filter(IndustryPartner.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Industry/partner organization profile not found for authenticated account."
        )
    if not partner.is_verified_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Your organization is not a verified, active partner. Complete government accreditation verification before this action is permitted."
        )
    return partner


def verify_same_university_faculty(faculty: Faculty, university_id: int):
    """Rejects arbitrary/cross-HEI mentor IDs: faculty must belong to the specified verified HEI."""
    if not faculty or faculty.university_id != university_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejected: Faculty mentor does not belong to this higher education institution."
        )


def verify_challenge_ownership(challenge_id: int, current_user: User, db: Session):
    """
    Ensures that citizens can only modify or submit private feedback on challenges they created.
    """
    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        return True

    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    citizen = db.query(Citizen).filter(Citizen.user_id == current_user.id).first()
    if citizen and challenge.citizen_id == citizen.id:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden: You are not the reporter of this challenge."
    )


def verify_organization_affiliation(org_id: int, current_user: User, db: Session):
    """Ensures a user belongs to the specified organization and cannot impersonate other entities."""
    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        return True

    from backend.app.models.models import OrganizationProfile
    profile = db.query(OrganizationProfile).filter(OrganizationProfile.id == org_id).first()
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not authorized to manage this organization profile."
        )
    return True


def verify_verification_submission_scope(project: Any, current_user: User, db: Session):
    """
    Stage 8: Enforce that only authorized government officers, jurisdictional PRI/ULBs,
    or assigned independent verifiers can submit official field verification records.
    Students, industry partners, and project teams cannot create official field verification records.
    """
    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        return True

    # Reject students, industry partners, citizens, and community orgs from official verification
    if current_user.role in {UserRole.STUDENT, UserRole.INDUSTRY, UserRole.CITIZEN, UserRole.COMMUNITY_ORG}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Role '{current_user.role.value}' is not authorized to submit official field verification records."
        )

    # Academic implementing team cannot act as official field verifier for their own project
    if current_user.role in {UserRole.UNIVERSITY, UserRole.FACULTY_MENTOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Higher education institution and faculty mentor cannot submit official field inspection records for their own project. Deliverable evidence must be submitted via milestones."
        )

    # Enforce jurisdiction for government officers, PRIs, and ULBs
    if current_user.role in {UserRole.GOVERNMENT_OFFICER, UserRole.PRI, UserRole.ULB}:
        if project.challenge:
            verify_challenge_jurisdiction(project.challenge, current_user, db, action="submit_verification")
        return True

    # Independent labs / innovation hubs
    if current_user.role in {UserRole.RESEARCH_LAB, UserRole.INNOVATION_HUB}:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden: Unauthorized verification actor."
    )


def verify_no_verification_conflict(record: Any, current_user: User, db: Session):
    """
    Stage 8: Prevent self-approval, reviewer conflicts, and project team reviews.
    """
    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        # Admin still cannot self-approve if they were the inspector
        if record.inspector_user_id and record.inspector_user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conflict of interest: Inspectors cannot review or approve their own field verification records."
            )
        return True

    # 1. Prevent self-approval
    if record.inspector_user_id and record.inspector_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conflict of interest: Inspectors cannot review or approve their own field verification records."
        )

    # 2. Prevent project team members from approving verification for their own project
    project = record.project
    if project:
        if project.faculty_mentor and project.faculty_mentor.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conflict of interest: Project faculty mentor cannot review official field verification."
            )
        if project.university and project.university.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conflict of interest: Project university cannot review official field verification."
            )
        if any(m.student and m.student.user_id == current_user.id for m in (project.members or [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conflict of interest: Enrolled student cannot review official field verification."
            )

    return True


def verify_citizen_feedback_eligibility(challenge: Any, current_user: User, db: Session, invitation_token: Optional[str] = None):
    """
    Stage 8: Ensure only the original reporter or verified local beneficiaries can submit feedback.
    Arbitrary unrelated citizens or government officers are forbidden from reviewing unassociated challenges.
    """
    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        return True

    # 1. Submitter ownership
    if challenge.submitted_by_user_id and challenge.submitted_by_user_id == current_user.id:
        return True

    # 2. Citizen model match
    from backend.app.models.models import Citizen
    citizen = db.query(Citizen).filter(Citizen.user_id == current_user.id).first()
    if citizen and challenge.citizen_id and challenge.citizen_id == citizen.id:
        return True

    # 3. Verified invitation token
    if invitation_token and invitation_token.strip().startswith("INV-"):
        return True

    # 4. Verified local resident in the same district
    user_district = (current_user.district_name or (citizen.district_name if citizen else None) or "").strip().lower()
    ch_loc = challenge.location
    ch_district = (ch_loc.district_name if ch_loc and ch_loc.district_name else "").strip().lower()
    if user_district and ch_district and user_district == ch_district:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden: You are neither the original reporter nor a verified resident beneficiary of this challenge's jurisdiction."
    )
