from __future__ import annotations

import hashlib
import json
import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, sessionmaker

from .models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def _json_for_hash(value: Any) -> str:
    return json.dumps(value or {}, sort_keys=True, separators=(",", ":"), default=str)


def payload_hash(value: Any) -> str:
    return hashlib.sha256(_json_for_hash(value).encode("utf-8")).hexdigest()


def actor_subject(user: dict[str, Any] | None) -> str | None:
    if not user:
        return None
    for key in ("sub", "preferred_username", "username", "user_id", "email"):
        candidate = user.get(key)
        if candidate:
            text = str(candidate).strip()
            if text:
                return text
    return None


def _safe_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except ValueError:
        return None


def record_audit(
    db: Session,
    *,
    action: str,
    object_type: str,
    object_id: str,
    details: dict[str, Any] | None = None,
    actor_user_id: str | UUID | None = None,
    actor_subject_value: str | None = None,
    session_id: str | None = None,
    run_id: str | None = None,
    request_id: str | None = None,
    commit: bool = True,
) -> AuditLog:
    details_payload = details or {}
    row = AuditLog(
        id=uuid4(),
        action=action,
        actor_user_id=_safe_uuid(actor_user_id),
        actor_subject=actor_subject_value,
        object_type=object_type,
        object_id=object_id,
        session_id=session_id,
        run_id=run_id,
        request_id=request_id,
        payload_hash=payload_hash(details_payload),
        details=details_payload,
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    return row


def safe_record_audit(
    db: Session,
    *,
    action: str,
    object_type: str,
    object_id: str,
    details: dict[str, Any] | None = None,
    actor_user_id: str | UUID | None = None,
    actor_subject_value: str | None = None,
    session_id: str | None = None,
    run_id: str | None = None,
    request_id: str | None = None,
) -> bool:
    bind = db.get_bind()
    if bind is None:
        return False

    SessionLocal = sessionmaker(bind=bind, autoflush=False, autocommit=False)
    audit_db = SessionLocal()
    try:
        record_audit(
            audit_db,
            action=action,
            object_type=object_type,
            object_id=object_id,
            details=details,
            actor_user_id=actor_user_id,
            actor_subject_value=actor_subject_value,
            session_id=session_id,
            run_id=run_id,
            request_id=request_id,
            commit=True,
        )
        return True
    except Exception:
        audit_db.rollback()
        logger.warning(
            "Failed to write audit entry",
            extra={"action": action, "object_type": object_type, "object_id": object_id},
        )
        return False
    finally:
        audit_db.close()
