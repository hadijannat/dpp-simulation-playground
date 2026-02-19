from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models.event_log import EventLog


def upsert_event(
    db: Session,
    *,
    event_id: str,
    event_type: str,
    user_id: str,
    source_service: str,
    version: str,
    session_id: str | None,
    run_id: str | None,
    request_id: str | None,
    event_timestamp: datetime,
    stream: str,
    stream_message_id: str | None,
    published: bool,
    publish_error: str | None,
    metadata: dict[str, Any] | list[Any] | None,
    payload: dict[str, Any],
) -> EventLog:
    row = db.query(EventLog).filter(EventLog.event_id == event_id).first()
    if row is None:
        row = EventLog(event_id=event_id)
        db.add(row)

    row.event_type = event_type
    row.user_id = user_id
    row.source_service = source_service
    row.version = version
    row.session_id = session_id
    row.run_id = run_id
    row.request_id = request_id
    row.event_timestamp = event_timestamp
    row.stream = stream
    row.stream_message_id = stream_message_id
    row.published = published
    row.publish_error = publish_error
    row.metadata_ = metadata if isinstance(metadata, (dict, list)) else {}
    row.payload = payload
    return row


def list_events(
    db: Session,
    *,
    session_id: str | None = None,
    run_id: str | None = None,
    event_type: str | None = None,
    source_service: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[EventLog], int]:
    query = db.query(EventLog)
    if session_id:
        query = query.filter(EventLog.session_id == session_id)
    if run_id:
        query = query.filter(EventLog.run_id == run_id)
    if event_type:
        query = query.filter(EventLog.event_type == event_type)
    if source_service:
        query = query.filter(EventLog.source_service == source_service)

    total = query.count()
    items = (
        query
        .order_by(EventLog.event_timestamp.desc(), EventLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total
