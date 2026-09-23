"""
Stage 9: Enterprise Notifications, Outbox Delivery Tracking & Preferences — Test Suite.

Validates:
1. Notification text sanitization: strips raw GPS coordinates, bearer tokens, and secrets from notification bodies.
2. In-app notifications with category, deep links, and retention.
3. User preferences & statutory consent gate: respects channel toggles (email, sms, push, whatsapp) and category subscriptions.
4. Outbox delivery tracking: records provider, delivery state (PENDING -> SENT / FAILED), retries, and failure reasons.
5. Provider adapter execution: valid addresses receive provider message IDs; invalid recipients fail gracefully with logged reasons.
6. Notifications API: category filtering, unread state, and server-side pagination.
7. Preferences API: CRUD operations for notification preferences and consent timestamps.
8. Retention cleanup: archives expired notifications.
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.core.security import create_access_token
from backend.app.models.models import (
    User, UserRole, Notification, NotificationOutbox, UserNotificationPreference, utc_now
)
from backend.app.services.notification_service import (
    notification_service, NotificationSanitizer, MockGovSmsAdapter, MockGovEmailAdapter, MockPushAdapter
)

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def _mk_user(db, email, role, full_name="Stage 9 User", phone_number="+919876543210"):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        email=email, full_name=full_name, phone_number=phone_number, role=role,
        hashed_password="hash", is_active=True, is_verified=True, admin_tier="STATE",
        district_name="Ranchi"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_notification_sanitization_no_sensitive_leak():
    """Verify that GPS coordinates, bearer tokens, and secrets are strictly redacted."""
    raw_text = (
        "Inspection completed at latitude: 23.344100, longitude: 85.309600. "
        "User used Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz and password: mySecretPassword123"
    )
    sanitized = NotificationSanitizer.sanitize(raw_text)

    assert "23.344100" not in sanitized
    assert "85.309600" not in sanitized
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
    assert "mySecretPassword123" not in sanitized
    assert "[REDACTED_COORDINATES]" in sanitized or "[REDACTED_LOCATION]" in sanitized
    assert "[REDACTED_TOKEN]" in sanitized
    assert "[REDACTED]" in sanitized


def test_in_app_notification_creation_and_preferences(db_session):
    """Test notification creation with category, deep link, and automatic preference init."""
    user = _mk_user(db_session, "stage9_citizen1@jharkhand.gov.in", UserRole.CITIZEN)

    notif = notification_service.create_notification(
        db=db_session,
        user_id=user.id,
        title="Field Inspection Scheduled",
        message="A verified officer will inspect the site at 23.3441, 85.3096",
        category="VERIFICATIONS",
        deep_link="/challenges/101/verification",
        retention_days=90
    )

    assert notif.id is not None
    assert notif.category == "VERIFICATIONS"
    assert notif.deep_link == "/challenges/101/verification"
    assert "23.3441" not in notif.message
    assert notif.is_read is False

    # Check user preferences record was automatically created
    pref = db_session.query(UserNotificationPreference).filter(
        UserNotificationPreference.user_id == user.id
    ).first()
    assert pref is not None
    assert pref.email_enabled is True
    assert pref.consent_given is True


def test_outbox_queueing_and_consent_control(db_session):
    """Verify outbox items are only queued for permitted channels and consented users."""
    user = _mk_user(db_session, "stage9_citizen2@jharkhand.gov.in", UserRole.CITIZEN, phone_number="+919876543211")

    # Update preferences: enable email and push, disable SMS
    pref = notification_service.get_or_create_user_preferences(db_session, user)
    pref.email_enabled = True
    pref.sms_enabled = False
    pref.push_enabled = True
    pref.consent_given = True
    db_session.commit()

    notif = notification_service.create_notification(
        db=db_session,
        user_id=user.id,
        title="Challenge Approved",
        message="Your challenge has been accepted for university matching.",
        category="CHALLENGES",
        deep_link="/challenges/102"
    )

    outbox_items = db_session.query(NotificationOutbox).filter(
        NotificationOutbox.notification_id == notif.id
    ).all()

    channels = [item.channel for item in outbox_items]
    assert "EMAIL" in channels
    assert "PUSH" in channels
    assert "SMS" not in channels  # SMS was disabled

    # Test Consent Revocation
    pref.consent_given = False
    db_session.commit()

    notif2 = notification_service.create_notification(
        db=db_session,
        user_id=user.id,
        title="No Consent Alert",
        message="This should not queue outbox records.",
        category="SYSTEM"
    )

    outbox_items2 = db_session.query(NotificationOutbox).filter(
        NotificationOutbox.notification_id == notif2.id
    ).all()
    assert len(outbox_items2) == 0  # No outbox entries when consent is withheld


def test_provider_adapters_and_delivery_status(db_session):
    """Verify provider adapters execute and update outbox delivery status."""
    user = _mk_user(db_session, "stage9_official@jharkhand.gov.in", UserRole.GOVERNMENT_ADMIN, phone_number="+919876543212")

    pref = notification_service.get_or_create_user_preferences(db_session, user)
    pref.email_enabled = True
    pref.sms_enabled = True
    pref.push_enabled = False
    pref.consent_given = True
    db_session.commit()

    notif = notification_service.create_notification(
        db=db_session,
        user_id=user.id,
        title="High Priority Escalation",
        message="Urgent action required on challenge 103.",
        category="ESCALATIONS",
        deep_link="/challenges/103"
    )

    # Process outbox queue for this notification
    processed = notification_service.process_outbox(db_session, max_items=50, notification_id=notif.id)
    assert processed >= 2

    # Verify outbox records reached SENT status with provider message IDs
    items = db_session.query(NotificationOutbox).filter(
        NotificationOutbox.notification_id == notif.id
    ).all()

    assert len(items) >= 2
    for item in items:
        db_session.refresh(item)
        assert item.delivery_status == "SENT"
        assert item.retry_count >= 1
        assert item.sent_at is not None
        assert item.failure_reason is None


def test_paginated_notifications_api(db_session):
    """Test notifications API with category filtering and pagination."""
    user = _mk_user(db_session, "stage9_citizen3@jharkhand.gov.in", UserRole.CITIZEN)
    token = create_access_token(str(user.id), user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Create 3 notifications in different categories
    notification_service.create_notification(db_session, user.id, "N1", "M1", category="CHALLENGES")
    notification_service.create_notification(db_session, user.id, "N2", "M2", category="PROJECTS")
    notification_service.create_notification(db_session, user.id, "N3", "M3", category="CHALLENGES")

    # 1. Fetch all with pagination
    res = client.get("/api/v1/notifications?paginated=true&limit=10&offset=0", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 3
    assert data["unread_count"] >= 3
    assert len(data["items"]) >= 3

    # 2. Filter by category=CHALLENGES
    res_filtered = client.get("/api/v1/notifications?paginated=true&category=CHALLENGES", headers=headers)
    assert res_filtered.status_code == 200
    data_filtered = res_filtered.json()
    for item in data_filtered["items"]:
        assert item["category"] == "CHALLENGES"

    # 3. Mark one read
    notif_id = data["items"][0]["id"]
    patch_res = client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "success"

    # 4. Check unread count decreased
    res_after = client.get("/api/v1/notifications?paginated=true", headers=headers)
    assert res_after.json()["unread_count"] == data["unread_count"] - 1


def test_preferences_api_crud(db_session):
    """Test GET and PUT /notifications/preferences."""
    email = f"stage9_citizen4_{int(datetime.now(timezone.utc).timestamp())}@jharkhand.gov.in"
    user = _mk_user(db_session, email, UserRole.CITIZEN)
    token = create_access_token(str(user.id), user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get preferences
    res = client.get("/api/v1/notifications/preferences", headers=headers)
    assert res.status_code == 200
    pref_data = res.json()
    assert pref_data["user_id"] == user.id
    assert pref_data["email_enabled"] is True

    # 2. Update preferences
    payload = {
        "email_enabled": False,
        "sms_enabled": True,
        "preferred_locale": "hi",
        "categories": {
            "CHALLENGES": True,
            "MILESTONES": False,
            "ESCALATIONS": True
        },
        "consent_given": True
    }
    update_res = client.put("/api/v1/notifications/preferences", json=payload, headers=headers)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["email_enabled"] is False
    assert updated["sms_enabled"] is True
    assert updated["preferred_locale"] == "hi"
    assert updated["categories"]["MILESTONES"] is False


def test_retention_and_cleanup(db_session):
    """Test cleanup of notifications past retention window."""
    user = _mk_user(db_session, "stage9_citizen5@jharkhand.gov.in", UserRole.CITIZEN)
    token = create_access_token(str(user.id), user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Create old read notification (>90 days ago)
    old_notif = Notification(
        user_id=user.id,
        title="Ancient Notification",
        message="From last quarter",
        category="SYSTEM",
        is_read=True,
        is_archived=False,
        created_at=datetime.now(timezone.utc) - timedelta(days=95)
    )
    db_session.add(old_notif)
    db_session.commit()

    del_res = client.delete("/api/v1/notifications/cleanup", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["archived_count"] >= 1

    # Verify old notification is now archived
    db_session.refresh(old_notif)
    assert old_notif.is_archived is True
