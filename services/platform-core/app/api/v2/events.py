from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...core.db import get_db
from services.shared.repositories import event_log_repo

router = APIRouter()

ALL_ROLES = ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"]


def _serialize_event(item: Any) -> dict[str, Any]:
    return {
        "event_id": item.event_id,
        "event_type": item.event_type,
        "user_id": item.user_id,
        "timestamp": item.event_timestamp.isoformat() if item.event_timestamp else None,
        "source_service": item.source_service,
        "session_id": item.session_id,
        "run_id": item.run_id,
        "request_id": item.request_id,
        "metadata": item.metadata_ or {},
        "version": item.version,
        "stream": item.stream,
        "stream_message_id": item.stream_message_id,
        "published": bool(item.published),
    }


@router.get("/core/events")
def list_events(
    request: Request,
    session_id: str | None = None,
    run_id: str | None = None,
    event_type: str | None = None,
    source_service: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ALL_ROLES)

    if not session_id and not run_id:
        raise HTTPException(status_code=422, detail="Either session_id or run_id is required")

    bounded_limit = max(1, min(limit, 200))
    bounded_offset = max(0, offset)

    items, total = event_log_repo.list_events(
        db,
        session_id=session_id,
        run_id=run_id,
        event_type=event_type,
        source_service=source_service,
        limit=bounded_limit,
        offset=bounded_offset,
    )
    return {
        "items": [_serialize_event(item) for item in items],
        "total": total,
        "limit": bounded_limit,
        "offset": bounded_offset,
    }
