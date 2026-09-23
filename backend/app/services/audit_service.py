"""
Unified Centralized Audit Service for SIH 26043.
Provides immutable, tamper-evident audit logging for state compliance,
DPDP actions, challenge workflows, and administrative actions.
"""

import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.models import AuditLog, utc_now


class AuditService:
    @staticmethod
    def log_action(
        action: str,
        actor_id: Optional[int],
        actor_role: str,
        entity_type: str,
        entity_id: int,
        details: Optional[Dict[str, Any]] = None,
        old_state: Optional[str] = None,
        new_state: Optional[str] = None,
        actor_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
        db: Optional[Session] = None
    ) -> AuditLog:
        if details and not new_state:
            new_state = json.dumps(details)

        log_entry = AuditLog(
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=actor_role or "SYSTEM",
            action=action,
            entity_name=entity_type,
            entity_id=entity_id,
            old_state=old_state,
            new_state=new_state,
            ip_address=ip_address,
            reason=reason or (details.get("reason") if details else None),
            timestamp=utc_now()
        )
        if db:
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
        return log_entry


audit_service = AuditService()
