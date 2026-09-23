import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status, BackgroundTasks, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.core.database import get_db
from backend.app.models.models import (
    Challenge, ChallengeLocation, ChallengeMedia, ChallengeStatus,
    ChallengePriority, StatusHistory, Comment, User, UserRole, Citizen,
    University, AIAnalysis, UniversityMatch, ChallengeSimilarity, District,
    ChallengeAttachment, ChallengeDraft, TaxonomyDomain, TaxonomySubdomain,
    ChallengeAllocation, DomainAuditEvent, AllocationStatus, AuditLog,
    AIHumanOverride, AIJob, AIJobStatus
)
from backend.app.schemas.schemas import (
    ChallengeCreate, ChallengeOut, ChallengeDetailOut, ChallengeStatusUpdate,
    AssignUniversityRequest, MarkDuplicateRequest, RejectChallengeRequest,
    CommentCreate, CommentOut, ChallengeLocationOut,
    ChallengeMediaOut, ChallengeAttachmentOut, AttachmentUploadOut,
    ChallengeDraftCreate, ChallengeDraftOut, TaxonomyDomainOut,
    AIAnalysisOut, UniversityMatchOut, SimilarChallengeOut,
    StatusHistoryOut,
    AcceptReviewRequest, RequestInfoRequest, SubmitInfoRequest, ValidateChallengeRequest,
    KeepSeparateRequest, AllocationResponseRequest, PauseChallengeRequest,
    ResumeChallengeRequest, ReopenChallengeRequest, AppealChallengeRequest,
    ChallengeAllocationOut, DomainAuditEventOut, AuditChainVerificationOut,
    AIHumanOverrideCreate, AIHumanOverrideOut, AIJobOut
)
from backend.app.services.ai_service import ai_service
from backend.app.services.ai.queue_service import queue_service
from backend.app.services.storage_service import storage_service
from backend.app.services.notification_service import notification_service
from backend.app.services.taxonomy_service import taxonomy_service
from backend.app.services.moderation_service import moderation_service
from backend.app.services.workflow_service import WorkflowService
from backend.app.routers.deps import (
    get_current_user, require_roles, get_optional_current_user,
    require_permission, check_jurisdiction, verify_challenge_jurisdiction
)
from backend.app.core.state_machine import validate_and_apply_challenge_transition

router = APIRouter(prefix="/challenges", tags=["Challenges"])

def run_background_ai_analysis(challenge_id: int, user_id: int, district_name: str, title: str):
    """
    Executes heavy AI NLP, duplicate detection, and university ranking
    via durable outbox queue to prevent API latency spikes and ensure resilience.
    """
    import logging
    from backend.app.core.database import SessionLocal
    db = SessionLocal()
    try:
        job = queue_service.enqueue_ai_job(db, challenge_id=challenge_id)
        queue_service.process_job(db, job)
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if challenge:
            notification_service.notify_role(
                db,
                UserRole.GOVERNMENT_ADMIN,
                title="New Societal Challenge Ready for Triage",
                message=f"Challenge '{title}' in {district_name} has completed automated AI screening.",
                reference_id=challenge.id,
                category="CHALLENGES",
                deep_link=f"/challenges/{challenge.id}"
            )
            notification_service.create_notification(
                db,
                user_id=user_id,
                title="Challenge AI Screening Complete",
                message=f"Your challenge '{title}' has been categorized and routed for government review.",
                reference_id=challenge.id,
                category="CHALLENGES",
                deep_link=f"/challenges/{challenge.id}"
            )
            db.commit()
    except Exception as exc:
        logging.getLogger("challenges").exception(f"Error in background AI processing: {exc}")
    finally:
        db.close()


@router.get("/taxonomy", response_model=List[TaxonomyDomainOut])
def get_taxonomy(db: Session = Depends(get_db)):
    """Returns canonical problem statement domains and subdomains."""
    taxonomy_service.seed_taxonomy_database(db)
    return taxonomy_service.get_taxonomy_tree(db)


@router.post("/attachments/upload", response_model=AttachmentUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Secure attachment upload endpoint for citizens, community groups, and PRIs.
    Validates magic bytes, enforces size limits, computes SHA-256, and stores in private storage.
    """
    attachment = await storage_service.save_challenge_attachment(file, owner_id=current_user.id, db=db)
    return AttachmentUploadOut(
        attachment_id=attachment.object_id,
        original_filename=attachment.original_filename,
        detected_mime=attachment.detected_mime,
        size_bytes=attachment.size_bytes,
        sha256_checksum=attachment.sha256_checksum,
        scan_status=attachment.scan_status,
        access_classification=attachment.access_classification,
        created_at=attachment.created_at
    )


@router.post("/drafts", response_model=ChallengeDraftOut)
def save_draft(
    payload: ChallengeDraftCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates or updates a user's challenge draft with idempotency support."""
    draft = None
    if payload.draft_id:
        draft = db.query(ChallengeDraft).filter(
            ChallengeDraft.draft_id == payload.draft_id,
            ChallengeDraft.user_id == current_user.id
        ).first()

    payload_str = json.dumps(payload.payload)
    if draft:
        draft.payload_json = payload_str
        draft.idempotency_key = payload.idempotency_key or draft.idempotency_key
        db.commit()
        db.refresh(draft)
    else:
        new_draft_id = payload.draft_id or uuid.uuid4().hex
        draft = ChallengeDraft(
            draft_id=new_draft_id,
            user_id=current_user.id,
            idempotency_key=payload.idempotency_key,
            payload_json=payload_str
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

    return ChallengeDraftOut(
        id=draft.id,
        draft_id=draft.draft_id,
        idempotency_key=draft.idempotency_key,
        payload=json.loads(draft.payload_json),
        created_at=draft.created_at,
        updated_at=draft.updated_at
    )


@router.get("/drafts", response_model=List[ChallengeDraftOut])
def list_drafts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all active drafts for the authenticated user."""
    drafts = db.query(ChallengeDraft).filter(ChallengeDraft.user_id == current_user.id).order_by(ChallengeDraft.updated_at.desc()).all()
    return [
        ChallengeDraftOut(
            id=d.id,
            draft_id=d.draft_id,
            idempotency_key=d.idempotency_key,
            payload=json.loads(d.payload_json),
            created_at=d.created_at,
            updated_at=d.updated_at
        )
        for d in drafts
    ]


@router.get("/drafts/{draft_id}", response_model=ChallengeDraftOut)
def get_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves a specific draft by draft ID."""
    draft = db.query(ChallengeDraft).filter(ChallengeDraft.draft_id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.user_id != current_user.id and current_user.role != UserRole.GOVERNMENT_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied to this draft")
    return ChallengeDraftOut(
        id=draft.id,
        draft_id=draft.draft_id,
        idempotency_key=draft.idempotency_key,
        payload=json.loads(draft.payload_json),
        created_at=draft.created_at,
        updated_at=draft.updated_at
    )


@router.delete("/drafts/{draft_id}")
def delete_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a challenge draft."""
    draft = db.query(ChallengeDraft).filter(ChallengeDraft.draft_id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.user_id != current_user.id and current_user.role != UserRole.GOVERNMENT_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied to this draft")
    db.delete(draft)
    db.commit()
    return {"status": "success", "message": "Draft deleted successfully"}


@router.get("", response_model=List[ChallengeOut])
def list_challenges(
    response: Response,
    category: Optional[str] = None,
    district: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
    page: Optional[int] = Query(None, ge=1, description="Page number"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    query = db.query(Challenge)
    
    if category and category != "All":
        query = query.filter(Challenge.category == category)
    if status and status != "All":
        query = query.filter(Challenge.status == status)
    if priority and priority != "All":
        query = query.filter(Challenge.priority == priority)
    if tier and tier != "All":
        query = query.filter(Challenge.current_tier == tier.upper())
    if district and district != "All":
        query = query.join(ChallengeLocation).filter(ChallengeLocation.district_name.ilike(f"%{district}%"))
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Challenge.title.ilike(term), Challenge.description.ilike(term)))

    total_count = query.count()
    response.headers["X-Total-Count"] = str(total_count)

    query = query.order_by(Challenge.created_at.desc())
    if page and page_size:
        response.headers["X-Page"] = str(page)
        response.headers["X-Page-Size"] = str(page_size)
        response.headers["X-Total-Pages"] = str((total_count + page_size - 1) // page_size)
        query = query.offset((page - 1) * page_size).limit(page_size)
        
    challenges = query.all()
    
    result = []
    for ch in challenges:
        dist_name = ch.location.district_name if ch.location else None
        univ_name = ch.assigned_university.institution_name if ch.assigned_university else None
        item = ChallengeOut(
            id=ch.id,
            title=ch.title,
            description=ch.description,
            category=ch.category,
            sub_category=ch.sub_category,
            urgency=ch.urgency,
            priority=ch.priority,
            expected_impact=ch.expected_impact,
            status=ch.status,
            district_name=dist_name,
            created_at=ch.created_at,
            assigned_university_name=univ_name,
            current_tier=ch.current_tier or "PANCHAYAT",
            escalation_level=ch.escalation_level or 1,
            escalated_by=ch.escalated_by,
            escalation_remarks=ch.escalation_remarks
        )
        result.append(item)
    return result

@router.post("", response_model=ChallengeDetailOut, status_code=status.HTTP_201_CREATED)
def report_challenge(
    payload: ChallengeCreate,
    background_tasks: BackgroundTasks,
    async_ai: bool = Query(False, description="Whether to run AI processing asynchronously in background"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Idempotency Check: prevent duplicate submissions on retry/network replay
    if payload.idempotency_key:
        existing = db.query(Challenge).filter(Challenge.idempotency_key == payload.idempotency_key).first()
        if existing:
            return get_challenge_detail(existing.id, current_user=current_user, db=db)

    # 2. Content Moderation & Abuse Check
    is_abusive, reason = moderation_service.inspect_submission(payload.title, payload.description)
    if is_abusive:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=reason
        )

    # 3. Controlled Taxonomy Validation
    canonical_domain = taxonomy_service.resolve_domain_code(payload.category)
    if not canonical_domain:
        allowed = ", ".join(taxonomy_service.CANONICAL_DOMAINS.keys())
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid domain category '{payload.category}'. Must be one of: {allowed}."
        )

    # 4. District and Geographic Coordinates Validation
    clean_district = taxonomy_service.resolve_district_name(payload.location.district_name)
    if not clean_district:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"District '{payload.location.district_name}' is not recognized as one of the 24 districts of Jharkhand."
        )

    valid_coords, coord_err = taxonomy_service.validate_coordinates(
        payload.location.latitude,
        payload.location.longitude,
        district_name=clean_district
    )
    if not valid_coords:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=coord_err
        )

    # 5. Affected Population Validation
    if payload.affected_population is None or payload.affected_population < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="affected_population must be a positive integer greater than or equal to 1."
        )

    # 6. Consent Verification
    if not payload.consent_given:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User consent is required to process and route this societal challenge."
        )

    # 7. Attachment Ownership & Security Validation
    linked_attachments = []
    if payload.attachment_ids:
        for att_id in payload.attachment_ids:
            att = db.query(ChallengeAttachment).filter(ChallengeAttachment.object_id == att_id).first()
            if not att:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Attachment '{att_id}' not found. Files must be issued by the server via /challenges/attachments/upload."
                )
            if att.owner_id != current_user.id and current_user.role != UserRole.GOVERNMENT_ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Unauthorized attachment: You do not own file attachment '{att_id}'."
                )
            if att.scan_status != "CLEAN":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Attachment '{att_id}' failed security scan status: {att.scan_status}."
                )
            linked_attachments.append(att)

    # Reject arbitrary external URLs
    if payload.media_urls:
        for u in payload.media_urls:
            if u.startswith(("http://", "https://")) and not any(u.startswith(prefix) for prefix in ("http://localhost", "http://127.0.0.1", "https://jharkhand.gov.in")):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Arbitrary external media URL rejected: '{u}'. Evidence attachments must be uploaded to the server."
                )

    # Retrieve or create citizen profile if citizen
    citizen = db.query(Citizen).filter(Citizen.user_id == current_user.id).first()
    citizen_id = citizen.id if citizen else None

    # Check district record
    dist = db.query(District).filter(District.name.ilike(clean_district)).first()
    dist_id = dist.id if dist else None

    # Submitter organization
    org_id = None
    if hasattr(current_user, "organization_id") and current_user.organization_id:
        org_id = current_user.organization_id

    challenge = Challenge(
        title=payload.title,
        description=payload.description,
        category=canonical_domain,
        sub_category=payload.sub_category,
        urgency=payload.urgency,
        expected_impact=payload.expected_impact,
        affected_population=payload.affected_population,
        status=ChallengeStatus.SUBMITTED,
        citizen_id=citizen_id,
        submitted_by_user_id=current_user.id,
        organization_id=org_id,
        submitter_role=current_user.role.value,
        source_type=payload.source_type or "CITIZEN_MOBILE",
        contact_preference=payload.contact_preference or "SMS",
        consent_version=payload.consent_version or "v1.0",
        consent_given=payload.consent_given,
        data_sharing_choice=payload.data_sharing_choice or "PUBLIC",
        accessibility_needs=payload.accessibility_needs,
        submission_language=payload.submission_language or "en",
        is_anonymous_public=payload.is_anonymous_public or False,
        idempotency_key=payload.idempotency_key
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)

    # Link verified attachments
    for att in linked_attachments:
        att.challenge_id = challenge.id

    # Location
    loc = ChallengeLocation(
        challenge_id=challenge.id,
        district_id=dist_id,
        district_name=clean_district,
        block_name=payload.location.block_name,
        village_or_city=payload.location.village_or_city,
        location_address=payload.location.location_address,
        latitude=payload.location.latitude,
        longitude=payload.location.longitude
    )
    db.add(loc)

    # Media attachments (legacy compatibility)
    if payload.media_urls:
        for url in payload.media_urls:
            m_type = "document" if url.endswith((".pdf", ".doc")) else "image"
            media = ChallengeMedia(
                challenge_id=challenge.id,
                media_type=m_type,
                file_url=url,
                file_name=url.split("/")[-1]
            )
            db.add(media)

    # Record status history and domain event
    role_desc = current_user.role.value.replace("_", " ").title()
    WorkflowService._record_domain_event(
        db=db,
        entity_type="Challenge",
        entity_id=challenge.id,
        action="CHALLENGE_SUBMITTED",
        previous_state=None,
        new_state="SUBMITTED",
        actor=current_user,
        payload={"title": challenge.title, "category": challenge.category, "district": payload.location.district_name},
        notes=f"{role_desc} reported societal challenge"
    )
    db.commit()
    
    # Enqueue AI Job in durable outbox queue
    job = queue_service.enqueue_ai_job(db, challenge_id=challenge.id)

    if async_ai:
        background_tasks.add_task(
            run_background_ai_analysis,
            challenge.id,
            current_user.id,
            payload.location.district_name,
            challenge.title
        )
    else:
        # Run AI Analysis Pipeline synchronously via queue processor
        queue_service.process_job(db, job)
        
        # Notify Admin of new challenge
        notification_service.notify_role(
            db,
            UserRole.GOVERNMENT_ADMIN,
            title="New Societal Challenge Submitted",
            message=f"A new challenge '{challenge.title}' was reported in {payload.location.district_name}.",
            reference_id=challenge.id,
            category="CHALLENGES",
            deep_link=f"/challenges/{challenge.id}"
        )
        
        # Notify Citizen
        notification_service.create_notification(
            db,
            user_id=current_user.id,
            title="Challenge Submitted & AI Analyzed",
            message=f"Your challenge '{challenge.title}' is logged and analyzed by the AI engine.",
            reference_id=challenge.id,
            category="CHALLENGES",
            deep_link=f"/challenges/{challenge.id}"
        )
        db.commit()
    
    return get_challenge_detail(challenge.id, current_user=current_user, db=db)

@router.get("/my", response_model=List[ChallengeOut])
def get_my_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    citizen = db.query(Citizen).filter(Citizen.user_id == current_user.id).first()
    if not citizen:
        return []
    challenges = db.query(Challenge).filter(Challenge.citizen_id == citizen.id).order_by(Challenge.created_at.desc()).all()
    result = []
    for ch in challenges:
        dist_name = ch.location.district_name if ch.location else None
        univ_name = ch.assigned_university.institution_name if ch.assigned_university else None
        result.append(ChallengeOut(
            id=ch.id,
            title=ch.title,
            description=ch.description,
            category=ch.category,
            sub_category=ch.sub_category,
            urgency=ch.urgency,
            priority=ch.priority,
            expected_impact=ch.expected_impact,
            status=ch.status,
            district_name=dist_name,
            created_at=ch.created_at,
            assigned_university_name=univ_name
        ))
    return result

@router.get("/nearby", response_model=List[ChallengeOut])
def get_nearby_challenges(
    district: str = Query(..., description="District to find challenges around"),
    db: Session = Depends(get_db)
):
    query = db.query(Challenge).join(ChallengeLocation).filter(
        ChallengeLocation.district_name.ilike(f"%{district}%")
    )
    challenges = query.order_by(Challenge.created_at.desc()).limit(20).all()
    result = []
    for ch in challenges:
        dist_name = ch.location.district_name if ch.location else None
        univ_name = ch.assigned_university.institution_name if ch.assigned_university else None
        result.append(ChallengeOut(
            id=ch.id,
            title=ch.title,
            description=ch.description,
            category=ch.category,
            sub_category=ch.sub_category,
            urgency=ch.urgency,
            priority=ch.priority,
            expected_impact=ch.expected_impact,
            status=ch.status,
            district_name=dist_name,
            created_at=ch.created_at,
            assigned_university_name=univ_name
        ))
    return result

@router.get("/{challenge_id}", response_model=ChallengeDetailOut)
def get_challenge_detail(
    challenge_id: int, 
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
        
    dist_name = ch.location.district_name if ch.location else None
    univ_name = ch.assigned_university.institution_name if ch.assigned_university else None
    
    loc_out = None
    if ch.location:
        is_author = current_user is not None and (
            (ch.submitted_by_user_id and ch.submitted_by_user_id == current_user.id) or
            (ch.citizen and ch.citizen.user_id == current_user.id)
        )
        is_gov_admin = current_user is not None and current_user.role == UserRole.GOVERNMENT_ADMIN
        is_gov_officer_in_scope = current_user is not None and current_user.role == UserRole.GOVERNMENT_OFFICER and (
            current_user.admin_tier == "STATE" or 
            (current_user.district_name and ch.location.district_name and current_user.district_name.lower() == ch.location.district_name.lower())
        )
        is_local_authority = current_user is not None and current_user.role in (UserRole.PRI, UserRole.ULB) and (
            current_user.district_name and ch.location.district_name and current_user.district_name.lower() == ch.location.district_name.lower()
        )
        is_privileged = bool(is_author or is_gov_admin or is_gov_officer_in_scope or is_local_authority)

        lat = ch.location.latitude
        lng = ch.location.longitude
        if not is_privileged and lat is not None and lng is not None:
            lat = round(lat, 2)
            lng = round(lng, 2)

        addr = (
            ch.location.location_address
            if is_privileged
            else f"{ch.location.block_name or ch.location.village_or_city or 'Area'}, {ch.location.district_name}, Jharkhand"
        )

        loc_out = ChallengeLocationOut(
            id=ch.location.id,
            district_name=ch.location.district_name,
            block_name=ch.location.block_name,
            village_or_city=ch.location.village_or_city,
            location_address=addr,
            latitude=lat,
            longitude=lng
        )

    # Submitter display privacy
    submitter_name = None
    if ch.submitted_by_user:
        if ch.is_anonymous_public and not is_privileged:
            submitter_name = "Anonymous Citizen"
        else:
            submitter_name = ch.submitted_by_user.full_name
    elif ch.citizen and ch.citizen.user:
        if ch.is_anonymous_public and not is_privileged:
            submitter_name = "Anonymous Citizen"
        else:
            submitter_name = ch.citizen.user.full_name

    media_out = [
        ChallengeMediaOut(
            id=m.id,
            media_type=m.media_type,
            file_url=m.file_url,
            file_name=m.file_name,
            uploaded_at=m.uploaded_at
        ) for m in ch.media
    ]

    attachments_out = [
        ChallengeAttachmentOut(
            id=a.id,
            object_id=a.object_id,
            original_filename=a.original_filename,
            detected_mime=a.detected_mime,
            size_bytes=a.size_bytes,
            sha256_checksum=a.sha256_checksum,
            scan_status=a.scan_status,
            access_classification=a.access_classification,
            created_at=a.created_at
        )
        for a in ch.attachments
    ]

    ai_out = None
    if ch.ai_analysis:
        ai_out = AIAnalysisOut(
            id=ch.ai_analysis.id,
            classified_domain=ch.ai_analysis.classified_domain,
            detected_priority=ch.ai_analysis.detected_priority,
            extracted_keywords=ch.ai_analysis.extracted_keywords,
            required_expertise=ch.ai_analysis.required_expertise,
            recommended_solution=ch.ai_analysis.recommended_solution,
            confidence_score=ch.ai_analysis.confidence_score
        )

    univ_matches_out = [
        UniversityMatchOut(
            university_id=um.university_id,
            institution_name=um.university.institution_name if um.university else "University",
            district_name=um.university.district_name if um.university else "Jharkhand",
            match_percentage=um.match_percentage,
            ranking=um.ranking,
            matching_factors=um.matching_factors
        ) for um in ch.university_matches
    ]

    sim_out = []
    for s in ch.similarities:
        sim_ch = s.similar_challenge
        if sim_ch:
            sim_dist = sim_ch.location.district_name if sim_ch.location else "Jharkhand"
            sim_out.append(SimilarChallengeOut(
                challenge_id=sim_ch.id,
                title=sim_ch.title,
                district_name=sim_dist,
                status=sim_ch.status,
                similarity_score=s.similarity_score
            ))

    history_out = [
        StatusHistoryOut(
            id=h.id,
            from_status=h.from_status,
            to_status=h.to_status,
            updated_by=h.updated_by,
            remarks=h.remarks,
            changed_at=h.changed_at
        ) for h in sorted(ch.status_history, key=lambda x: x.changed_at)
    ]

    comments_out = [
        CommentOut(
            id=c.id,
            user_id=c.user_id,
            author_name=c.author.full_name if c.author else "User",
            author_role=c.author.role.value if c.author else "CITIZEN",
            content=c.content,
            created_at=c.created_at
        ) for c in sorted(ch.comments, key=lambda x: x.created_at)
    ]

    allocations_out = [
        ChallengeAllocationOut(
            id=a.id,
            challenge_id=a.challenge_id,
            assigned_by_user_id=a.assigned_by_user_id,
            assigned_to_org_id=a.assigned_to_org_id,
            status=a.status.value if hasattr(a.status, 'value') else str(a.status),
            allocated_at=a.allocated_at,
            deadline_at=a.deadline_at,
            responded_at=a.responded_at,
            response_notes=a.response_notes,
            capacity_assessment=a.capacity_assessment,
            coi_declared=a.coi_declared,
            reassigned_from_allocation_id=a.reassigned_from_allocation_id,
            created_at=a.created_at
        ) for a in (ch.allocations or [])
    ]

    return ChallengeDetailOut(
        id=ch.id,
        title=ch.title,
        description=ch.description,
        category=ch.category,
        sub_category=ch.sub_category,
        urgency=ch.urgency,
        priority=ch.priority,
        expected_impact=ch.expected_impact,
        affected_population=ch.affected_population or 100,
        status=ch.status,
        district_name=dist_name,
        created_at=ch.created_at,
        assigned_university_name=univ_name,
        current_tier=ch.current_tier or "PANCHAYAT",
        escalation_level=ch.escalation_level or 1,
        escalated_by=ch.escalated_by,
        escalation_remarks=ch.escalation_remarks,
        submitted_by_name=submitter_name,
        submitter_role=ch.submitter_role,
        source_type=ch.source_type or "CITIZEN_MOBILE",
        consent_version=ch.consent_version or "v1.0",
        data_sharing_choice=ch.data_sharing_choice or "PUBLIC",
        submission_language=ch.submission_language or "en",
        translation_status=ch.translation_status or "NONE",
        is_anonymous_public=ch.is_anonymous_public or False,
        idempotency_key=ch.idempotency_key,
        version=ch.version or 1,
        location=loc_out,
        media=media_out,
        attachments=attachments_out,
        ai_analysis=ai_out,
        university_matches=univ_matches_out,
        similar_challenges=sim_out,
        status_history=history_out,
        comments=comments_out,
        allocations=allocations_out
    )

@router.post("/{challenge_id}/status")
def update_challenge_status(
    challenge_id: int,
    payload: ChallengeStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
        
    WorkflowService.transition_challenge(
        db=db,
        challenge=ch,
        to_status=payload.status,
        actor=current_user,
        expected_version=payload.expected_version,
        remarks=payload.remarks
    )
    
    if ch.citizen and ch.citizen.user:
        notification_service.create_notification(
            db,
            user_id=ch.citizen.user.id,
            title=f"Challenge Status: {payload.status.value}",
            message=f"Your reported challenge '{ch.title}' has updated to {payload.status.value}.",
            reference_id=ch.id
        )
    db.commit()
    return {"status": "success", "message": f"Challenge status updated to {payload.status.value}"}

@router.post("/{challenge_id}/accept-review")
def accept_challenge_for_review(
    challenge_id: int,
    payload: AcceptReviewRequest,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    ch = WorkflowService.accept_for_review(
        db=db,
        challenge_id=challenge_id,
        actor=current_user,
        expected_version=payload.expected_version,
        notes=payload.notes
    )
    db.commit()
    return {"status": "success", "message": "Challenge accepted into review queue", "challenge_status": ch.status.value}

@router.post("/{challenge_id}/request-info")
def request_challenge_info(
    challenge_id: int,
    payload: RequestInfoRequest,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    ch = WorkflowService.request_more_information(
        db=db,
        challenge_id=challenge_id,
        actor=current_user,
        clarification_items=payload.clarification_items,
        expected_version=payload.expected_version,
        notes=payload.notes
    )
    db.commit()
    return {"status": "success", "message": "Clarification requested from submitter", "challenge_status": ch.status.value}

@router.post("/{challenge_id}/submit-info")
def submit_challenge_info(
    challenge_id: int,
    payload: SubmitInfoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ch = WorkflowService.submit_clarification(
        db=db,
        challenge_id=challenge_id,
        actor=current_user,
        responses=payload.responses,
        additional_attachments=payload.additional_attachments,
        expected_version=payload.expected_version
    )
    db.commit()
    return {"status": "success", "message": "Clarification submitted; returned to review queue", "challenge_status": ch.status.value}

@router.post("/{challenge_id}/assign")
def assign_university(
    challenge_id: int,
    payload: AssignUniversityRequest,
    current_user: User = Depends(require_permission("challenge.assign")),
    db: Session = Depends(get_db)
):
    allocation = WorkflowService.assign_challenge(
        db=db,
        challenge_id=challenge_id,
        actor=current_user,
        university_id=payload.university_id,
        organization_id=payload.organization_id,
        deadline_days=payload.deadline_days,
        capacity_notes=payload.capacity_notes,
        remarks=payload.remarks,
        expected_version=payload.expected_version
    )
    ch = allocation.challenge
    if ch.assigned_university and ch.assigned_university.user:
        notification_service.create_notification(
            db,
            user_id=ch.assigned_university.user.id,
            title="Societal Challenge Assigned",
            message=f"Challenge '{ch.title}' has been assigned to your institution by the Government of Jharkhand.",
            reference_id=ch.id
        )
    if ch.citizen and ch.citizen.user:
        notification_service.create_notification(
            db,
            user_id=ch.citizen.user.id,
            title="University Assigned to Your Challenge",
            message=f"An academic institution has been assigned to work on a solution for '{ch.title}'.",
            reference_id=ch.id
        )
    db.commit()
    return {
        "status": "success",
        "message": f"Assigned to institution (allocation #{allocation.id})",
        "allocation_id": allocation.id,
        "deadline_at": allocation.deadline_at.isoformat() if allocation.deadline_at else None
    }

@router.post("/allocations/{allocation_id}/respond")
def respond_challenge_allocation(
    allocation_id: int,
    payload: AllocationResponseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allocation = WorkflowService.respond_allocation(
        db=db,
        allocation_id=allocation_id,
        actor=current_user,
        decision=payload.decision,
        notes=payload.notes,
        coi_declared=payload.coi_declared,
        expected_version=payload.expected_version
    )
    db.commit()
    return {
        "status": "success",
        "message": f"Allocation #{allocation.id} response recorded as {allocation.status.value}",
        "allocation_status": allocation.status.value
    }

@router.post("/{challenge_id}/duplicate")
def mark_challenge_duplicate(
    challenge_id: int,
    payload: MarkDuplicateRequest,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    ch = WorkflowService.confirm_duplicate(
        db=db,
        challenge_id=challenge_id,
        canonical_challenge_id=payload.canonical_challenge_id,
        actor=current_user,
        expected_version=payload.expected_version,
        remarks=payload.remarks
    )
    db.commit()
    return {"status": "success", "message": f"Challenge marked as duplicate of #{payload.canonical_challenge_id}"}

@router.post("/{challenge_id}/keep-separate")
def keep_challenge_separate(
    challenge_id: int,
    payload: KeepSeparateRequest,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    ch = WorkflowService.keep_separate(
        db=db,
        challenge_id=challenge_id,
        compared_challenge_id=payload.compared_challenge_id,
        actor=current_user,
        justification=payload.justification,
        expected_version=payload.expected_version
    )
    db.commit()
    return {"status": "success", "message": f"False similarity candidate #{payload.compared_challenge_id} dismissed"}

@router.post("/{challenge_id}/reject")
def reject_challenge(
    challenge_id: int,
    payload: RejectChallengeRequest,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    ch = WorkflowService.reject_challenge(
        db=db,
        challenge_id=challenge_id,
        actor=current_user,
        reason=payload.reason,
        reason_code=payload.reason_code,
        expected_version=payload.expected_version
    )
    db.commit()
    return {"status": "success", "message": "Challenge rejected with provided justification"}

@router.post("/{challenge_id}/pause")
def pause_challenge(
    challenge_id: int,
    payload: PauseChallengeRequest,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    ch = WorkflowService.pause_challenge(
        db=db,
        challenge_id=challenge_id,
        reason=payload.reason,
        actor=current_user,
        expected_version=payload.expected_version
    )
    db.commit()
    return {"status": "success", "message": "Challenge marked as PAUSED"}

@router.post("/{challenge_id}/resume")
def resume_challenge(
    challenge_id: int,
    payload: ResumeChallengeRequest,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    ch = WorkflowService.resume_challenge(
        db=db,
        challenge_id=challenge_id,
        actor=current_user,
        remarks=payload.remarks,
        expected_version=payload.expected_version
    )
    db.commit()
    return {"status": "success", "message": f"Challenge resumed to {ch.status.value}"}

@router.post("/{challenge_id}/reopen")
def reopen_challenge(
    challenge_id: int,
    payload: ReopenChallengeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ch = WorkflowService.reopen_challenge(
        db=db,
        challenge_id=challenge_id,
        reason=payload.reason,
        actor=current_user,
        expected_version=payload.expected_version
    )
    db.commit()
    return {"status": "success", "message": "Challenge reopened"}

@router.post("/{challenge_id}/appeal")
def appeal_challenge(
    challenge_id: int,
    payload: AppealChallengeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ch = WorkflowService.appeal_challenge(
        db=db,
        challenge_id=challenge_id,
        grounds=payload.grounds,
        actor=current_user,
        evidence=payload.evidence
    )
    db.commit()
    return {"status": "success", "message": "Appeal successfully submitted and placed in review queue"}

@router.post("/{challenge_id}/comments", response_model=CommentOut)
def add_comment(
    challenge_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
        
    comment = Comment(
        challenge_id=challenge_id,
        user_id=current_user.id,
        content=payload.content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return CommentOut(
        id=comment.id,
        user_id=current_user.id,
        author_name=current_user.full_name,
        author_role=current_user.role.value,
        content=comment.content,
        created_at=comment.created_at
    )

@router.post("/upload")
async def upload_challenge_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    attachment = await storage_service.save_challenge_attachment(file, owner_id=current_user.id, db=db)
    return {
        "file_url": f"/files/attachments/{attachment.object_id}",
        "file_name": attachment.original_filename,
        "attachment_id": attachment.object_id,
        "sha256_checksum": attachment.sha256_checksum,
        "size_bytes": attachment.size_bytes
    }

@router.get("/{challenge_id}/history")
def get_challenge_history(
    challenge_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")

    events = db.query(DomainAuditEvent).filter(
        DomainAuditEvent.entity_type == "Challenge",
        DomainAuditEvent.entity_id == challenge_id
    ).order_by(DomainAuditEvent.sequence_number.desc()).all()

    is_privileged = (
        current_user is not None and
        current_user.role in {UserRole.GOVERNMENT_ADMIN, UserRole.GOVERNMENT_OFFICER}
    )

    if not is_privileged:
        return WorkflowService.sanitize_history_for_public(events)

    if events:
        return [
            DomainAuditEventOut.model_validate(ev) for ev in events
        ]

    # Legacy fallback
    logs = db.query(AuditLog).filter(
        AuditLog.entity_name == "Challenge",
        AuditLog.entity_id == challenge_id
    ).order_by(AuditLog.timestamp.desc()).all()
    if not logs:
        return [
            {
                "actor_name": h.updated_by,
                "action": "STATUS_CHANGED",
                "old_state": h.from_status,
                "new_state": h.to_status,
                "reason": h.remarks,
                "timestamp": h.changed_at.isoformat() if h.changed_at else ""
            }
            for h in sorted(ch.status_history, key=lambda x: x.changed_at, reverse=True)
        ]
    return logs

@router.get("/{challenge_id}/audit-verification", response_model=AuditChainVerificationOut)
def verify_challenge_audit_chain(
    challenge_id: int,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
    result = WorkflowService.verify_audit_chain(db, entity_type="Challenge", entity_id=challenge_id)
    return AuditChainVerificationOut(**result)

@router.post("/{challenge_id}/ai-override", response_model=AIHumanOverrideOut)
def record_ai_override(
    challenge_id: int,
    payload: AIHumanOverrideCreate,
    current_user: User = Depends(require_permission("challenge.review")),
    db: Session = Depends(get_db)
):
    try:
        override = ai_service.record_human_override(
            db=db,
            challenge_id=challenge_id,
            reviewer_id=current_user.id,
            decision_type=payload.decision_type,
            override_value=payload.override_value,
            mandatory_reason=payload.mandatory_reason
        )
        return override
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{challenge_id}/ai-overrides", response_model=List[AIHumanOverrideOut])
def get_ai_overrides(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(AIHumanOverride).filter(AIHumanOverride.challenge_id == challenge_id).order_by(AIHumanOverride.created_at.desc()).all()

@router.get("/{challenge_id}/ai-job", response_model=Optional[AIJobOut])
def get_latest_ai_job(
    challenge_id: int,
    db: Session = Depends(get_db)
):
    job = db.query(AIJob).filter(AIJob.challenge_id == challenge_id).order_by(AIJob.id.desc()).first()
    return job

