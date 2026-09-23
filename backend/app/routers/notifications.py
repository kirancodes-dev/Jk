import json
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import (
    Notification, NotificationOutbox, UserNotificationPreference, User, utc_now
)
from backend.app.schemas.schemas import (
    NotificationOut, PaginatedNotificationsOut,
    NotificationPreferenceUpdate, NotificationPreferenceOut,
    NotificationOutboxOut
)
from backend.app.services.notification_service import notification_service
from backend.app.routers.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=Union[PaginatedNotificationsOut, List[NotificationOut]])
def get_user_notifications(
    category: Optional[str] = None,
    is_read: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    paginated: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves user notifications with category filtering, unread status filtering,
    and server-side pagination.
    """
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_archived == False
    )

    if category and category.upper() != "ALL":
        query = query.filter(Notification.category == category.upper())

    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    total = query.count()
    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
        Notification.is_archived == False
    ).count()

    items = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    if paginated:
        return PaginatedNotificationsOut(
            total=total,
            unread_count=unread_count,
            limit=limit,
            offset=offset,
            items=items
        )
    return items


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"status": "success", "message": "Marked as read"}


@router.post("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "success", "message": "All notifications marked as read"}


@router.get("/preferences", response_model=NotificationPreferenceOut)
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves user notification channels, language, and category subscription preferences."""
    pref = notification_service.get_or_create_user_preferences(db, current_user)
    db.commit()

    categories = {}
    if pref.categories_json:
        try:
            categories = json.loads(pref.categories_json)
        except Exception:
            categories = {}

    return NotificationPreferenceOut(
        user_id=pref.user_id,
        email_enabled=pref.email_enabled,
        sms_enabled=pref.sms_enabled,
        push_enabled=pref.push_enabled,
        whatsapp_enabled=pref.whatsapp_enabled,
        preferred_locale=pref.preferred_locale,
        categories=categories,
        consent_given=pref.consent_given,
        consent_timestamp=pref.consent_timestamp,
        consent_version=pref.consent_version,
        updated_at=pref.updated_at
    )


@router.put("/preferences", response_model=NotificationPreferenceOut)
def update_user_preferences(
    payload: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates user notification channels, categories, and statutory consent."""
    pref = notification_service.get_or_create_user_preferences(db, current_user)

    if payload.email_enabled is not None:
        pref.email_enabled = payload.email_enabled
    if payload.sms_enabled is not None:
        pref.sms_enabled = payload.sms_enabled
    if payload.push_enabled is not None:
        pref.push_enabled = payload.push_enabled
    if payload.whatsapp_enabled is not None:
        pref.whatsapp_enabled = payload.whatsapp_enabled
    if payload.preferred_locale is not None:
        pref.preferred_locale = payload.preferred_locale
    if payload.categories is not None:
        pref.categories_json = json.dumps(payload.categories)
    if payload.consent_given is not None:
        pref.consent_given = payload.consent_given
        pref.consent_timestamp = utc_now()

    pref.updated_at = utc_now()
    db.commit()
    db.refresh(pref)

    categories = {}
    if pref.categories_json:
        try:
            categories = json.loads(pref.categories_json)
        except Exception:
            categories = {}

    return NotificationPreferenceOut(
        user_id=pref.user_id,
        email_enabled=pref.email_enabled,
        sms_enabled=pref.sms_enabled,
        push_enabled=pref.push_enabled,
        whatsapp_enabled=pref.whatsapp_enabled,
        preferred_locale=pref.preferred_locale,
        categories=categories,
        consent_given=pref.consent_given,
        consent_timestamp=pref.consent_timestamp,
        consent_version=pref.consent_version,
        updated_at=pref.updated_at
    )


@router.get("/outbox", response_model=List[NotificationOutboxOut])
def get_user_outbox_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View external dispatch outbox delivery status and provider records for the current user."""
    items = db.query(NotificationOutbox).filter(
        NotificationOutbox.user_id == current_user.id
    ).order_by(NotificationOutbox.created_at.desc()).limit(limit).all()
    return items


@router.post("/outbox/process")
def process_outbox_queue(
    max_items: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Triggers execution/retry of pending outbox messages via provider adapters."""
    processed = notification_service.process_outbox(db, max_items=max_items)
    return {"status": "success", "processed_count": processed}


@router.delete("/cleanup")
def cleanup_old_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archives read notifications exceeding the statutory retention window."""
    archived = notification_service.cleanup_expired_notifications(db)
    return {"status": "success", "archived_count": archived}
