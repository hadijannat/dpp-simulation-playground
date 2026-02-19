from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any

_events: deque[dict[str, Any]] = deque(maxlen=500)
_lock = Lock()


def record_webhook_event(
    *,
    channel: str,
    payload: dict[str, Any],
    callback_url: str | None = None,
    status_code: int | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channel": channel,
        "callback_url": callback_url,
        "status_code": status_code,
        "error": error,
        "payload": payload,
    }
    with _lock:
        _events.appendleft(entry)
    return entry


def list_webhook_events(limit: int = 100) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(limit, 500))
    with _lock:
        return list(_events)[:bounded_limit]


def clear_webhook_events() -> int:
    with _lock:
        count = len(_events)
        _events.clear()
    return count
