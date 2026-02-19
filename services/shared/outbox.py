from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .redis_client import get_redis, publish_event
from .repositories import event_outbox_repo

logger = logging.getLogger(__name__)


def _is_sqlite_session(db: Session) -> bool:
    bind = db.get_bind()
    return bool(bind and bind.dialect.name == "sqlite")


def _missing_outbox_table(exc: Exception) -> bool:
    raw = str(getattr(exc, "orig", exc)).lower()
    return "event_outbox" in raw and ("no such table" in raw or "does not exist" in raw)


def enqueue_event(db: Session, *, stream: str, payload: dict[str, Any], commit: bool = True) -> tuple[bool, str | None]:
    event_id = str(payload.get("event_id") or uuid4())
    payload["event_id"] = event_id

    event_outbox_repo.enqueue_event(db, event_id=event_id, stream=stream, payload=dict(payload))
    if commit:
        db.commit()
    return True, event_id


def emit_event(
    db: Session,
    *,
    stream: str,
    payload: dict[str, Any],
    redis_url: str,
    maxlen: int | None = None,
    commit: bool = True,
    log: logging.Logger | None = None,
) -> tuple[bool, str | None]:
    active_logger = log or logger

    try:
        return enqueue_event(db, stream=stream, payload=payload, commit=commit)
    except SQLAlchemyError as exc:
        db.rollback()
        if _is_sqlite_session(db) and _missing_outbox_table(exc):
            active_logger.warning("Outbox table unavailable on SQLite; falling back to direct publish")
            ok, message_id = publish_event(get_redis(redis_url), stream, payload, maxlen=maxlen)
            return ok, message_id

        active_logger.warning("Failed to enqueue outbox event", extra={"stream": stream, "error": str(exc)})
        return False, None
