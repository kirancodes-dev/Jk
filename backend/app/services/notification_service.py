from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import Notification, User, UserRole

class NotificationService:
    def create_notification(
        self,
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "INFO",
        reference_id: Optional[int] = None
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            reference_id=reference_id,
            is_read=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    def notify_role(
        self,
        db: Session,
        role: UserRole,
        title: str,
        message: str,
        reference_id: Optional[int] = None
    ) -> List[Notification]:
        users = db.query(User).filter(User.role == role, User.is_active == True).all()
        created = []
        for u in users:
            notif = Notification(
                user_id=u.id,
                title=title,
                message=message,
                notification_type=role.value,
                reference_id=reference_id,
                is_read=False
            )
            db.add(notif)
            created.append(notif)
        db.commit()
        return created

notification_service = NotificationService()
