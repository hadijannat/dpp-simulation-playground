from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

SESSION_LIFECYCLE_KEY = "lifecycle_state"
SESSION_STATES = {"active", "paused", "completed", "failed"}
ALLOWED_TRANSITIONS = {
    "active": {"paused", "completed", "failed"},
    "paused": {"active", "completed", "failed"},
    "completed": set(),
    "failed": set(),
}


def get_lifecycle_state(session_state: dict[str, Any] | None, *, is_active: bool = True) -> str:
    current = (session_state or {}).get(SESSION_LIFECYCLE_KEY)
    if current in SESSION_STATES:
        return str(current)
    return "active" if is_active else "paused"


def set_lifecycle_state(session_state: dict[str, Any] | None, target_state: str) -> dict[str, Any]:
    if target_state not in SESSION_STATES:
        raise ValueError(f"invalid session lifecycle state: {target_state}")
    next_state = dict(session_state or {})
    next_state[SESSION_LIFECYCLE_KEY] = target_state
    next_state["state_updated_at"] = datetime.now(timezone.utc).isoformat()
    return next_state


def assert_transition_allowed(current_state: str, target_state: str) -> None:
    if target_state == current_state:
        return
    allowed = ALLOWED_TRANSITIONS.get(current_state, set())
    if target_state not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Invalid state transition: {current_state} -> {target_state}",
        )


def ensure_session_active(session_state: dict[str, Any] | None, *, is_active: bool) -> None:
    lifecycle_state = get_lifecycle_state(session_state, is_active=is_active)
    if lifecycle_state != "active":
        raise HTTPException(status_code=409, detail=f"Session is not active (state={lifecycle_state})")
