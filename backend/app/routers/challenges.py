from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status, BackgroundTasks, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.core.database import get_db
from backend.app.models.models import (
    Challenge, ChallengeLocation, ChallengeMedia, ChallengeStatus,
    ChallengePriority, StatusHistory, Comment, User, UserRole, Citizen,
    University, AIAnalysis, UniversityMatch, ChallengeSimilarity, District
)
from backend.app.schemas.schemas import (
    ChallengeCreate, ChallengeOut, ChallengeDetailOut, ChallengeStatusUpdate,
    AssignUniversityRequest, MarkDuplicateRequest, RejectChallengeRequest,
    CommentCreate, CommentOut, ChallengeLocationOut,
    ChallengeMediaOut, AIAnalysisOut, UniversityMatchOut, SimilarChallengeOut,
    StatusHistoryOut
)
from backend.app.services.ai_service import ai_service
from backend.app.services.storage_service import storage_service
from backend.app.services.notification_service import notification_service
from backend.app.routers.deps import get_current_user, require_roles, get_optional_current_user
from backend.app.core.state_machine import validate_and_apply_challenge_transition
from backend.app.models.models import AuditLog

router = APIRouter(prefix="/challenges", tags=["Challenges"])

def run_background_ai_analysis(challenge_id: int, user_id: int, district_name: str, title: str):
    """
    Executes heavy AI NLP, duplicate detection, and university ranking
    in the background to prevent API latency spikes.
    """
    from backend.app.core.database import SessionLocal
    db = SessionLocal()
    try:
        challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
        if challenge:
            ai_service.analyze_challenge(challenge, db)
            db.add(StatusHistory(
                challenge_id=challenge.id,
                from_status="SUBMITTED",
                to_status="AI_ANALYSIS",
                updated_by="SIH AI Engine (Background Worker)",
                remarks="Asynchronous AI Classification, Priority Assessment & University Matching completed"
            ))
            notification_service.notify_role(
                db,
                UserRole.GOVERNMENT_ADMIN,
                title="New Societal Challenge Ready for Triage",
                message=f"Challenge '{title}' in {district_name} has completed automated AI screening.",
                reference_id=challenge.id
            )
            notification_service.create_notification(
                db,
                user_id=user_id,
                title="Challenge AI Screening Complete",
                message=f"Your challenge '{title}' has been categorized and routed for government review.",
                reference_id=challenge.id
            )
            db.commit()
    finally:
        db.close()

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
    # Retrieve or create citizen profile
    citizen = db.query(Citizen).filter(Citizen.user_id == current_user.id).first()
    citizen_id = citizen.id if citizen else None
    
    # Check district
    dist = db.query(District).filter(District.name.ilike(payload.location.district_name)).first()
    dist_id = dist.id if dist else None
    
    challenge = Challenge(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        sub_category=payload.sub_category,
        urgency=payload.urgency,
        expected_impact=payload.expected_impact,
        status=ChallengeStatus.SUBMITTED,
        citizen_id=citizen_id
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    
    # Location
    loc = ChallengeLocation(
        challenge_id=challenge.id,
        district_id=dist_id,
        district_name=payload.location.district_name,
        block_name=payload.location.block_name,
        village_or_city=payload.location.village_or_city,
        location_address=payload.location.location_address,
        latitude=payload.location.latitude,
        longitude=payload.location.longitude
    )
    db.add(loc)
    
    # Media attachments
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
            
    # Record status history
    db.add(StatusHistory(
        challenge_id=challenge.id,
        from_status=None,
        to_status="SUBMITTED",
        updated_by=current_user.full_name,
        remarks="Citizen reported societal challenge"
    ))
    db.commit()
    
    if async_ai:
        background_tasks.add_task(
            run_background_ai_analysis,
            challenge.id,
            current_user.id,
            payload.location.district_name,
            challenge.title
        )
    else:
        # Run AI Analysis Pipeline synchronously
        ai_service.analyze_challenge(challenge, db)
        
        # Record AI status transition
        db.add(StatusHistory(
            challenge_id=challenge.id,
            from_status="SUBMITTED",
            to_status="AI_ANALYSIS",
            updated_by="SIH AI Engine",
            remarks="AI Categorization, Priority Scoring & University Matching completed"
        ))
        
        # Notify Admin of new challenge
        notification_service.notify_role(
            db,
            UserRole.GOVERNMENT_ADMIN,
            title="New Societal Challenge Submitted",
            message=f"A new challenge '{challenge.title}' was reported in {payload.location.district_name}.",
            reference_id=challenge.id
        )
        
        # Notify Citizen
        notification_service.create_notification(
            db,
            user_id=current_user.id,
            title="Challenge Submitted & AI Analyzed",
            message=f"Your challenge '{challenge.title}' is logged and analyzed by the AI engine.",
            reference_id=challenge.id
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
        is_privileged = (
            current_user is not None and (
                current_user.role == UserRole.GOVERNMENT_ADMIN or 
                (ch.citizen and ch.citizen.user_id == current_user.id)
            )
        )
        lat = ch.location.latitude
        lng = ch.location.longitude
        if not is_privileged and lat is not None and lng is not None:
            lat = round(lat, 2)
            lng = round(lng, 2)

        loc_out = ChallengeLocationOut(
            id=ch.location.id,
            district_name=ch.location.district_name,
            block_name=ch.location.block_name,
            village_or_city=ch.location.village_or_city,
            location_address=ch.location.location_address if is_privileged else f"{ch.location.block_name or ch.location.district_name}, Jharkhand",
            latitude=lat,
            longitude=lng
        )
        
    media_out = [
        ChallengeMediaOut(
            id=m.id,
            media_type=m.media_type,
            file_url=m.file_url,
            file_name=m.file_name,
            uploaded_at=m.uploaded_at
        ) for m in ch.media
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
    
    return ChallengeDetailOut(
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
        escalation_remarks=ch.escalation_remarks,
        location=loc_out,
        media=media_out,
        ai_analysis=ai_out,
        university_matches=univ_matches_out,
        similar_challenges=sim_out,
        status_history=history_out,
        comments=comments_out
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
        
    # Enforce state machine transition & immutable audit log
    validate_and_apply_challenge_transition(
        db=db,
        challenge=ch,
        to_status=payload.status,
        actor_id=current_user.id,
        actor_role=current_user.role,
        actor_name=current_user.full_name,
        remarks=payload.remarks
    )
    
    # Notify citizen if challenge has citizen
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

@router.post("/{challenge_id}/assign")
def assign_university(
    challenge_id: int,
    payload: AssignUniversityRequest,
    current_user: User = Depends(require_roles([UserRole.GOVERNMENT_ADMIN])),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if ch.assigned_university_id is not None and ch.assigned_university_id != payload.university_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflict: Challenge #{ch.id} has already been assigned to another institution (ID: {ch.assigned_university_id})."
        )

    univ = db.query(University).filter(University.id == payload.university_id).first()
    if not univ:
        raise HTTPException(status_code=404, detail="University not found")
        
    old_status = ch.status.value
    ch.assigned_university_id = univ.id
    ch.status = ChallengeStatus.UNIVERSITY_ASSIGNED
    
    db.add(StatusHistory(
        challenge_id=ch.id,
        from_status=old_status,
        to_status="UNIVERSITY_ASSIGNED",
        updated_by=f"{current_user.full_name} ({current_user.role.value})",
        remarks=payload.remarks or f"Challenge formally assigned to {univ.institution_name}"
    ))

    db.add(AuditLog(
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        actor_role=current_user.role.value,
        action="CHALLENGE_ASSIGN_UNIVERSITY",
        entity_name="Challenge",
        entity_id=ch.id,
        old_state=old_status,
        new_state=f"Assigned to {univ.institution_name} (ID: {univ.id})",
        reason=f"Government routing to {univ.institution_name}"
    ))
    
    # Notify University user
    if univ.user:
        notification_service.create_notification(
            db,
            user_id=univ.user.id,
            title="Societal Challenge Assigned",
            message=f"Challenge '{ch.title}' has been assigned to your institution by the Government of Jharkhand.",
            reference_id=ch.id
        )
        
    # Notify Citizen
    if ch.citizen and ch.citizen.user:
        notification_service.create_notification(
            db,
            user_id=ch.citizen.user.id,
            title="University Assigned to Your Challenge",
            message=f"{univ.institution_name} has been assigned to work on a solution for '{ch.title}'.",
            reference_id=ch.id
        )
    db.commit()
    return {"status": "success", "message": f"Assigned to {univ.institution_name}"}

@router.post("/{challenge_id}/duplicate")
def mark_challenge_duplicate(
    challenge_id: int,
    payload: MarkDuplicateRequest,
    current_user: User = Depends(require_roles([UserRole.GOVERNMENT_ADMIN])),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
    canonical = db.query(Challenge).filter(Challenge.id == payload.canonical_challenge_id).first()
    if not canonical:
        raise HTTPException(status_code=404, detail="Canonical challenge not found")

    validate_and_apply_challenge_transition(
        db=db,
        challenge=ch,
        to_status=ChallengeStatus.DUPLICATE,
        actor_id=current_user.id,
        actor_role=current_user.role,
        actor_name=current_user.full_name,
        remarks=f"Duplicate of #{canonical.id}: {payload.remarks}"
    )
    ch.moderation_reason = f"Duplicate of #{canonical.id} ({canonical.title})"
    db.commit()
    return {"status": "success", "message": f"Challenge marked as duplicate of #{canonical.id}"}

@router.post("/{challenge_id}/reject")
def reject_challenge(
    challenge_id: int,
    payload: RejectChallengeRequest,
    current_user: User = Depends(require_roles([UserRole.GOVERNMENT_ADMIN])),
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")

    validate_and_apply_challenge_transition(
        db=db,
        challenge=ch,
        to_status=ChallengeStatus.REJECTED,
        actor_id=current_user.id,
        actor_role=current_user.role,
        actor_name=current_user.full_name,
        remarks=payload.reason
    )
    ch.moderation_reason = payload.reason
    db.commit()
    return {"status": "success", "message": "Challenge rejected with provided justification"}

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
    current_user: User = Depends(get_current_user)
):
    url = await storage_service.save_file(file, subfolder="challenges")
    return {"file_url": url, "file_name": file.filename}

@router.get("/{challenge_id}/history")
def get_challenge_history(
    challenge_id: int,
    db: Session = Depends(get_db)
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
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
