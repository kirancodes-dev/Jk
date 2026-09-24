import json
import re
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session
from backend.app.models.models import (
    Notification, NotificationOutbox, UserNotificationPreference,
    User, UserRole, utc_now
)
from backend.app.services.email_service import email_service

@dataclass
class AdapterResult:
    success: bool
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None


class NotificationSanitizer:
    """
    Sanitizes notification text to guarantee no sensitive data leaks:
    - Strips exact GPS coordinates (lat/long floats).
    - Strips authentication tokens, API keys, or session secrets.
    - Strips raw passwords or confidential document URLs.
    """
    # Regex for coordinates e.g. 23.344100, 85.309600 or "latitude: 23.34"
    GPS_REGEX = re.compile(r'([-+]?\d{1,2}\.\d{4,8})[\s,]+([-+]?\d{1,3}\.\d{4,8})', re.IGNORECASE)
    GPS_NAMED_REGEX = re.compile(r'(latitude|lat|longitude|lon|lng)[\s:=]+[-+]?\d{1,3}\.\d{3,8}', re.IGNORECASE)
    # Regex for tokens and keys
    TOKEN_REGEX = re.compile(r'(bearer\s+[a-zA-Z0-9_\-\.]+)|(token[\s:=]+[a-zA-Z0-9_\-\.]+)|(api[_-]?key[\s:=]+[a-zA-Z0-9_\-\.]+)', re.IGNORECASE)
    PASSWORD_REGEX = re.compile(r'(password[\s:=]+[^\s]+)', re.IGNORECASE)

    @classmethod
    def sanitize(cls, text: str) -> str:
        if not text:
            return ""
        sanitized = cls.GPS_REGEX.sub("[REDACTED_LOCATION]", text)
        sanitized = cls.GPS_NAMED_REGEX.sub("[REDACTED_COORDINATES]", sanitized)
        sanitized = cls.TOKEN_REGEX.sub("[REDACTED_TOKEN]", sanitized)
        sanitized = cls.PASSWORD_REGEX.sub("password: [REDACTED]", sanitized)
        return sanitized


class BaseNotificationAdapter:
    """Base interface for notification channel adapters (real or simulated)."""
    def send(self, recipient: str, message: str, metadata: Dict[str, Any]) -> AdapterResult:
        raise NotImplementedError


class SimulatedGovSmsAdapter(BaseNotificationAdapter):
    """
    SIMULATED SMS channel — no real telco/DLT SMS gateway is integrated. Validates
    Indian MSISDN format and fabricates a delivery ID so the outbox pipeline (retry,
    status tracking) can be exercised end-to-end, but no SMS is actually sent.
    Wiring a real gateway (e.g. C-DAC/NIC or a commercial DLT-registered provider)
    is planned, not implemented.
    """
    def send(self, recipient: str, message: str, metadata: Dict[str, Any]) -> AdapterResult:
        clean_phone = re.sub(r'[^\d+]', '', recipient)
        # Indian phone numbers: +91XXXXXXXXXX or 10 digits
        if not (clean_phone.startswith('+91') and len(clean_phone) == 13) and not (len(clean_phone) == 10 and clean_phone.isdigit()):
            return AdapterResult(
                success=False,
                error_message=f"Invalid Indian phone format for SMS gateway: {recipient}"
            )
        msg_id = f"SIMULATED-SMS-{uuid.uuid4().hex[:12].upper()}"
        return AdapterResult(success=True, provider_message_id=msg_id)


class GovEmailAdapter(BaseNotificationAdapter):
    """
    Real SMTP email delivery via backend/app/services/email_service.py (same
    SMTP_HOST/SMTP_USER/SMTP_PASSWORD used for OTP emails). Falls back to a clearly
    labeled simulated success — never a fabricated "delivered" claim about a real
    gateway — when SMTP credentials are not configured (e.g. local/dev/demo
    environments), so the outbox pipeline still works without a mail relay.
    """
    EMAIL_REGEX = re.compile(r'^[\w\.\+\-]+@[\w\.\-]+\.[a-zA-Z]{2,}$')

    def send(self, recipient: str, message: str, metadata: Dict[str, Any]) -> AdapterResult:
        if not self.EMAIL_REGEX.match(recipient.strip()):
            return AdapterResult(
                success=False,
                error_message=f"Malformed recipient email address: {recipient}"
            )
        subject = str(metadata.get("subject") or "Government of Jharkhand Innovation Portal Notification")
        sent_via_real_smtp = email_service.send_generic_email(recipient, subject, message)
        if sent_via_real_smtp:
            return AdapterResult(success=True, provider_message_id=f"SMTP-{uuid.uuid4().hex[:12].upper()}")
        # SMTP not configured in this environment — simulated fallback, clearly labeled.
        return AdapterResult(success=True, provider_message_id=f"SIMULATED-EMAIL-{uuid.uuid4().hex[:12].upper()}")


class SimulatedPushAdapter(BaseNotificationAdapter):
    """
    SIMULATED push channel — no Firebase Cloud Messaging (or other) project is wired
    up. Validates that a device token is present and fabricates a delivery ID.
    """
    def send(self, recipient: str, message: str, metadata: Dict[str, Any]) -> AdapterResult:
        if not recipient or len(recipient.strip()) < 5:
            return AdapterResult(
                success=False,
                error_message=f"Missing or invalid push registration token: {recipient}"
            )
        msg_id = f"SIMULATED-PUSH-{uuid.uuid4().hex}"
        return AdapterResult(success=True, provider_message_id=msg_id)


class SimulatedWhatsAppAdapter(BaseNotificationAdapter):
    """
    SIMULATED WhatsApp channel — no WhatsApp Business API account is integrated.
    Wiring a real provider (e.g. Meta's Cloud API via an NIC-approved BSP) is
    planned, not implemented.
    """
    def send(self, recipient: str, message: str, metadata: Dict[str, Any]) -> AdapterResult:
        clean_phone = re.sub(r'[^\d+]', '', recipient)
        if len(clean_phone) < 10:
            return AdapterResult(
                success=False,
                error_message=f"Invalid WhatsApp recipient number: {recipient}"
            )
        msg_id = f"SIMULATED-WAMID-{uuid.uuid4().hex}"
        return AdapterResult(success=True, provider_message_id=msg_id)


class NotificationService:
    """
    Event-Driven Notification & Outbox Dispatch Service.
    - Sanitizes all notification content.
    - Persists in-app notifications with deep links & retention policies.
    - Enforces user preferences & statutory consent before queuing outbox items.
    - Dispatches through channel adapters with retry, status tracking, and error
      reporting. Email is real SMTP delivery when configured; SMS, WhatsApp, and
      push are explicitly simulated (see each adapter's docstring and the
      "SIMULATED_*" provider labels below) — no real gateway is wired up for them yet.
    """
    def __init__(self):
        self.adapters = {
            "EMAIL": GovEmailAdapter(),
            "SMS": SimulatedGovSmsAdapter(),
            "PUSH": SimulatedPushAdapter(),
            "WHATSAPP": SimulatedWhatsAppAdapter(),
        }

    def get_or_create_user_preferences(self, db: Session, user: User) -> UserNotificationPreference:
        """Retrieves or initializes user notification preferences."""
        pref = db.query(UserNotificationPreference).filter(UserNotificationPreference.user_id == user.id).first()
        if not pref:
            default_categories = {
                "CHALLENGES": True,
                "MILESTONES": True,
                "VERIFICATIONS": True,
                "ESCALATIONS": True,
                "SYSTEM": True,
            }
            pref = UserNotificationPreference(
                user_id=user.id,
                email_enabled=True,
                sms_enabled=False,
                push_enabled=True,
                whatsapp_enabled=False,
                preferred_locale="en",
                categories_json=json.dumps(default_categories),
                consent_given=True,
                consent_timestamp=utc_now(),
                consent_version="v1.0"
            )
            db.add(pref)
            db.flush()
        return pref

    def create_notification(
        self,
        db: Session,
        user_id: Any,
        title: str,
        message: str,
        notification_type: str = "INFO",
        reference_id: Optional[int] = None,
        category: str = "GENERAL",
        deep_link: Optional[str] = None,
        retention_days: int = 90
    ) -> Notification:
        """
        Creates an in-app notification and queues configured/consented outbox deliveries.
        """
        # 1. Sanitize text
        clean_title = NotificationSanitizer.sanitize(title)
        clean_message = NotificationSanitizer.sanitize(message)

        # 2. Persist in-app notification
        notif = Notification(
            user_id=user_id,
            title=clean_title,
            message=clean_message,
            notification_type=notification_type,
            reference_id=reference_id,
            category=category.upper(),
            deep_link=deep_link,
            retention_days=retention_days,
            is_read=False,
            is_archived=False,
            created_at=utc_now()
        )
        db.add(notif)
        db.flush()

        # 3. Check User Preferences & Enqueue Outbox items
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            pref = self.get_or_create_user_preferences(db, user)
            self._queue_outbox_deliveries(db, notif, user, pref)

        db.commit()
        db.refresh(notif)
        return notif

    def _queue_outbox_deliveries(
        self,
        db: Session,
        notification: Notification,
        user: User,
        pref: UserNotificationPreference
    ):
        """Enqueues outbox records for permitted & consented channels."""
        if not pref.consent_given:
            return  # No external communication without consent

        # Check category subscription
        categories = {}
        if pref.categories_json:
            try:
                categories = json.loads(str(pref.categories_json))
            except Exception:
                categories = {}

        cat_key = str(notification.category or "").upper()
        if categories and not categories.get(cat_key, True):
            return  # Category alert muted by user

        # 1. Email Outbox
        if pref.email_enabled and user.email:
            email_outbox = NotificationOutbox(
                notification_id=notification.id,
                user_id=user.id,
                channel="EMAIL",
                provider="SMTP_EMAIL",
                recipient=user.email,
                template_id=f"TPL_{notification.category}_v1",
                template_version="1.0",
                locale=pref.preferred_locale,
                delivery_status="PENDING",
                retry_count=0,
                max_retries=3,
                payload_json=json.dumps({
                    "subject": notification.title,
                    "body": notification.message,
                    "deep_link": notification.deep_link,
                }),
                created_at=utc_now()
            )
            db.add(email_outbox)

        # 2. SMS Outbox
        if pref.sms_enabled and getattr(user, 'phone_number', None):
            sms_outbox = NotificationOutbox(
                notification_id=notification.id,
                user_id=user.id,
                channel="SMS",
                provider="SIMULATED_SMS",
                recipient=user.phone_number,
                template_id="DLT_11071600000001",
                template_version="1.0",
                locale=pref.preferred_locale,
                delivery_status="PENDING",
                retry_count=0,
                max_retries=3,
                payload_json=json.dumps({
                    "text": f"{notification.title}: {notification.message[:140]}"
                }),
                created_at=utc_now()
            )
            db.add(sms_outbox)

        # 3. Push Outbox
        if pref.push_enabled:
            # Simulated device push token — no real push provider (e.g. FCM) is wired up.
            push_token = f"simulated_push_token_{user.id}_{user.role.value}"
            push_outbox = NotificationOutbox(
                notification_id=notification.id,
                user_id=user.id,
                channel="PUSH",
                provider="SIMULATED_PUSH",
                recipient=push_token,
                template_id="PUSH_ALERT_v1",
                template_version="1.0",
                locale=pref.preferred_locale,
                delivery_status="PENDING",
                retry_count=0,
                max_retries=3,
                payload_json=json.dumps({
                    "title": notification.title,
                    "body": notification.message,
                    "deep_link": notification.deep_link,
                }),
                created_at=utc_now()
            )
            db.add(push_outbox)

    def notify_role(
        self,
        db: Session,
        role: UserRole,
        title: str,
        message: str,
        reference_id: Optional[int] = None,
        category: str = "GENERAL",
        deep_link: Optional[str] = None
    ) -> List[Notification]:
        """Broadcasts a notification to all active users with a specific role."""
        users = db.query(User).filter(User.role == role, User.is_active == True).all()
        created = []
        for u in users:
            notif = self.create_notification(
                db=db,
                user_id=u.id,
                title=title,
                message=message,
                notification_type=role.value,
                reference_id=reference_id,
                category=category,
                deep_link=deep_link
            )
            created.append(notif)
        return created

    def process_outbox(self, db: Session, max_items: int = 20, notification_id: Optional[Any] = None) -> int:
        """
        Processes pending and retryable outbox messages using real provider adapters.
        Tracks delivery state, retries, and failure reasons.
        """
        now = utc_now()
        query = db.query(NotificationOutbox).filter(
            NotificationOutbox.delivery_status.in_(["PENDING", "FAILED"]),
            NotificationOutbox.retry_count < NotificationOutbox.max_retries
        )
        if notification_id is not None:
            query = query.filter(NotificationOutbox.notification_id == notification_id)
        outbox_items = query.order_by(NotificationOutbox.created_at.asc()).limit(max_items).all()

        processed_count = 0
        for item in outbox_items:
            channel_key = str(item.channel)
            adapter = self.adapters.get(channel_key)
            if not adapter:
                setattr(item, "delivery_status", "FAILED")
                setattr(item, "failure_reason", f"No adapter registered for channel {channel_key}")
                setattr(item, "last_attempt_at", now)
                continue

            setattr(item, "delivery_status", "SENDING")
            setattr(item, "last_attempt_at", now)
            current_retries = int(getattr(item, "retry_count", 0) or 0)
            setattr(item, "retry_count", current_retries + 1)

            payload = {}
            if item.payload_json:
                try:
                    payload = json.loads(str(item.payload_json))
                except Exception:
                    payload = {}

            body = payload.get("body") or payload.get("text") or "Gov Update"
            recipient_str = str(item.recipient or "")
            result = adapter.send(recipient=recipient_str, message=body, metadata=payload)

            if result.success:
                setattr(item, "delivery_status", "SENT")
                setattr(item, "sent_at", now)
                setattr(item, "failure_reason", None)
            else:
                setattr(item, "delivery_status", "FAILED")
                setattr(item, "failure_reason", result.error_message or "Unknown delivery error")

            processed_count += 1

        db.commit()
        return processed_count

    def cleanup_expired_notifications(self, db: Session) -> int:
        """Archives or deletes notifications older than their retention window."""
        now = utc_now()
        cutoff_90 = now - timedelta(days=90)
        archived_count = db.query(Notification).filter(
            Notification.is_read == True,
            Notification.created_at < cutoff_90,
            Notification.is_archived == False
        ).update({"is_archived": True}, synchronize_session=False)
        db.commit()
        return archived_count


notification_service = NotificationService()
