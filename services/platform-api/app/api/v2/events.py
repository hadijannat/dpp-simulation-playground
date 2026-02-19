from __future__ import annotations

from fastapi import APIRouter, Request

from ...auth import require_roles
from ...config import PLATFORM_CORE_URL
from ...core.proxy import request_json
from ...schemas.v2 import EventListResponse

router = APIRouter()

ALL_ROLES = ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"]


@router.get("/events", response_model=EventListResponse)
def list_events(
    request: Request,
    session_id: str | None = None,
    run_id: str | None = None,
    event_type: str | None = None,
    source_service: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    require_roles(request.state.user, ALL_ROLES)

    params = {
        "session_id": session_id,
        "run_id": run_id,
        "event_type": event_type,
        "source_service": source_service,
        "limit": limit,
        "offset": offset,
    }
    clean_params = {key: value for key, value in params.items() if value is not None}

    payload = request_json(
        request,
        "GET",
        f"{PLATFORM_CORE_URL}/api/v2/core/events",
        params=clean_params,
    )
    items = payload.get("items")
    if not isinstance(items, list):
        items = []
    total = payload.get("total") if isinstance(payload.get("total"), int) else len(items)
    resolved_limit = payload.get("limit") if isinstance(payload.get("limit"), int) else limit
    resolved_offset = payload.get("offset") if isinstance(payload.get("offset"), int) else offset
    return {
        "items": items,
        "total": total,
        "limit": resolved_limit,
        "offset": resolved_offset,
    }
