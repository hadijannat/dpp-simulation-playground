from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models.event_outbox import EventOutbox


def enqueue_event(
    db: Session,
    *,
    event_id: str,
    stream: str,
    payload: dict[str, Any],
) -> EventOutbox:
    row = EventOutbox(
        event_id=event_id,
        stream=stream,
        payload=payload,
        status="pending",
        attempts=0,
        available_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def claim_pending_events(
    db: Session,
    *,
    limit: int,
    lock_timeout_seconds: int,
) -> list[EventOutbox]:
    now = datetime.now(timezone.utc)
    stale_lock = now - timedelta(seconds=max(1, lock_timeout_seconds))

    rows = (
        db.query(EventOutbox)
        .filter(EventOutbox.status.in_(["pending", "processing"]))
        .filter(EventOutbox.available_at <= now)
        .filter(or_(EventOutbox.locked_at.is_(None), EventOutbox.locked_at < stale_lock))
        .order_by(EventOutbox.id.asc())
        .limit(max(1, limit))
        .all()
    )

    for row in rows:
        row.status = "processing"
        row.locked_at = now

    db.flush()
    return rows


def mark_published(row: EventOutbox, *, stream_message_id: str | None = None) -> None:
    now = datetime.now(timezone.utc)
    row.status = "published"
    row.stream_message_id = stream_message_id
    row.published_at = now
    row.locked_at = None
    row.last_error = None


def mark_retry(row: EventOutbox, *, error: str | None, backoff_seconds: int) -> None:
    now = datetime.now(timezone.utc)
    row.status = "pending"
    row.attempts = int(row.attempts or 0) + 1
    row.last_error = (error or "unknown_error")[:4000]
    row.locked_at = None
    row.available_at = now + timedelta(seconds=max(1, backoff_seconds))
