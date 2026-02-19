from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...engine.point_rule_engine import load_active_point_rules, load_point_rules_from_yaml
from ...engine.points_engine import ROLE_MULTIPLIERS, _apply_multiplier
from ...models.user_points import UserPoints
from ...auth import require_roles
from services.shared.models.event_log import EventLog

router = APIRouter()


WINDOW_ALIASES = {
    "all": "all",
    "daily": "daily",
    "day": "daily",
    "weekly": "weekly",
    "week": "weekly",
    "monthly": "monthly",
    "month": "monthly",
}
VALID_ROLES = set(ROLE_MULTIPLIERS.keys())


def _normalize_window(window: str) -> str:
    normalized = WINDOW_ALIASES.get((window or "all").strip().lower())
    if not normalized:
        raise HTTPException(status_code=422, detail="window must be one of: all, daily, weekly, monthly")
    return normalized


def _normalize_role(role: str | None) -> str | None:
    if role is None:
        return None
    normalized = role.strip().lower()
    if not normalized:
        return None
    if normalized not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"role must be one of: {', '.join(sorted(VALID_ROLES))}")
    return normalized


def _window_start(window: str, now: datetime) -> datetime | None:
    if window == "all":
        return None
    if window == "daily":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if window == "weekly":
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return day_start - timedelta(days=day_start.weekday())
    if window == "monthly":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


def _load_point_rules(db: Session) -> dict[str, int]:
    rules = load_active_point_rules(db)
    if not rules:
        rules = load_point_rules_from_yaml()
    return {event_type: int(points) for event_type, points in rules.items() if int(points) > 0}


def _extract_role(metadata: dict[str, Any] | list[Any] | None) -> str | None:
    if not isinstance(metadata, dict):
        return None
    role = metadata.get("role")
    if not isinstance(role, str):
        return None
    normalized = role.strip().lower()
    return normalized or None


def _load_events_for_window(
    db: Session,
    *,
    point_rules: dict[str, int],
    start_time: datetime | None,
) -> list[EventLog]:
    if not point_rules:
        return []
    query = db.query(EventLog).filter(EventLog.published.is_(True))
    query = query.filter(EventLog.event_type.in_(list(point_rules.keys())))
    if start_time is not None:
        query = query.filter(EventLog.event_timestamp >= start_time)
    return query.all()


def _build_windowed_items(
    events: list[Any],
    *,
    point_rules: dict[str, int],
    role: str | None,
    window: str,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    totals: dict[str, int] = {}
    roles_by_user: dict[str, str] = {}

    for item in events:
        event_type = str(getattr(item, "event_type", "") or "")
        base_points = point_rules.get(event_type)
        if not base_points:
            continue

        user_id = str(getattr(item, "user_id", "") or "").strip()
        if not user_id:
            continue

        metadata = getattr(item, "metadata_", None)
        event_role = _extract_role(metadata)
        if role and event_role != role:
            continue

        applied_points = _apply_multiplier(int(base_points), metadata if isinstance(metadata, dict) else None)
        totals[user_id] = totals.get(user_id, 0) + int(applied_points)
        if event_role:
            roles_by_user[user_id] = event_role

    ranked = sorted(totals.items(), key=lambda row: (-row[1], row[0]))
    sliced = ranked[offset : offset + limit]
    items: list[dict[str, Any]] = []
    for user_id, total_points in sliced:
        row: dict[str, Any] = {
            "user_id": user_id,
            "total_points": int(total_points),
            "level": max(1, int(total_points / 100) + 1),
            "window": window,
        }
        resolved_role = role or roles_by_user.get(user_id)
        if resolved_role:
            row["role"] = resolved_role
        items.append(row)
    return items


@router.get("/leaderboard")
def leaderboard(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    window: str = "all",
    role: str | None = None,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"])
    bounded_limit = max(1, min(limit, 100))
    bounded_offset = max(0, offset)
    normalized_window = _normalize_window(window)
    normalized_role = _normalize_role(role)

    if normalized_window == "all" and normalized_role is None:
        items = (
            db.query(UserPoints)
            .order_by(UserPoints.total_points.desc())
            .offset(bounded_offset)
            .limit(bounded_limit)
            .all()
        )
        return {
            "items": [
                {"user_id": str(item.user_id), "total_points": item.total_points, "level": item.level, "window": "all"}
                for item in items
            ],
            "window": "all",
            "role": None,
        }

    point_rules = _load_point_rules(db)
    start_time = _window_start(normalized_window, datetime.now(timezone.utc))
    events = _load_events_for_window(db, point_rules=point_rules, start_time=start_time)
    items = _build_windowed_items(
        events,
        point_rules=point_rules,
        role=normalized_role,
        window=normalized_window,
        limit=bounded_limit,
        offset=bounded_offset,
    )
    return {
        "items": items,
        "window": normalized_window,
        "role": normalized_role,
    }
