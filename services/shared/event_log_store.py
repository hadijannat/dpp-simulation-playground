from __future__ import annotations

import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .repositories import event_log_repo

logger = logging.getLogger(__name__)

_session_factory: sessionmaker | None = None
_init_attempted = False
_lock = threading.Lock()


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_event_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        candidate = value.strip()
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _get_session_factory() -> sessionmaker | None:
    global _session_factory, _init_attempted

    if _session_factory is not None:
        return _session_factory

    with _lock:
        if _session_factory is not None:
            return _session_factory
        if _init_attempted:
            return None

        _init_attempted = True
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.debug("Skipping event-log persistence because DATABASE_URL is not set")
            return None

        try:
            engine = create_engine(database_url, future=True)
            _session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        except Exception:
            logger.exception("Failed to initialize event-log session factory")
            _session_factory = None
        return _session_factory


def persist_event(
    stream: str,
    event: dict[str, Any],
    *,
    published: bool,
    stream_message_id: str | None = None,
    publish_error: str | None = None,
) -> bool:
    session_factory = _get_session_factory()
    if session_factory is None:
        return False

    event_id = _coerce_str(event.get("event_id")) or str(uuid4())
    metadata = event.get("metadata")

    db = session_factory()
    try:
        event_log_repo.upsert_event(
            db,
            event_id=event_id,
            event_type=_coerce_str(event.get("event_type")) or "unknown",
            user_id=_coerce_str(event.get("user_id")) or "",
            source_service=_coerce_str(event.get("source_service")) or "unknown",
            version=_coerce_str(event.get("version")) or "1",
            session_id=_coerce_str(event.get("session_id")),
            run_id=_coerce_str(event.get("run_id")),
            request_id=_coerce_str(event.get("request_id")),
            event_timestamp=_parse_event_timestamp(event.get("timestamp")),
            stream=stream,
            stream_message_id=_coerce_str(stream_message_id),
            published=published,
            publish_error=_coerce_str(publish_error),
            metadata=metadata if isinstance(metadata, (dict, list)) else {},
            payload=dict(event),
        )
        db.commit()
        return True
    except Exception:
        db.rollback()
        logger.exception("Failed to persist event log", extra={"event_id": event_id, "stream": stream})
        return False
    finally:
        db.close()
