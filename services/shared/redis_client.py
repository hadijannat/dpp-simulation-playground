from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import redis

from .event_log_store import persist_event
from .events import validate_event

logger = logging.getLogger(__name__)


class _NoopCounter:
    def labels(self, **_kwargs: Any) -> "_NoopCounter":
        return self

    def inc(self, _amount: float = 1.0) -> None:
        return


def _build_counter(name: str, documentation: str, labelnames: list[str]):
    try:
        from prometheus_client import Counter

        return Counter(name, documentation, labelnames)
    except Exception:
        return _NoopCounter()


EVENT_PUBLISH_ATTEMPTS = _build_counter(
    "dpp_event_publish_total",
    "Total event publish attempts by stream and result",
    ["stream", "result"],
)
EVENT_PUBLISH_RETRIES = _build_counter(
    "dpp_event_publish_retries_total",
    "Total event publish retries by stream",
    ["stream"],
)


def _bool_from_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_from_env(name: str, default: int, *, minimum: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, value)


def _float_from_env(name: str, default: float, *, minimum: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return max(minimum, value)


def redis_connection_kwargs() -> dict[str, Any]:
    return {
        "protocol": _int_from_env("REDIS_PROTOCOL", 2, minimum=2),
        "socket_timeout": _float_from_env("REDIS_SOCKET_TIMEOUT_SECONDS", 10.0, minimum=0.1),
        "socket_connect_timeout": _float_from_env("REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS", 5.0, minimum=0.1),
        "socket_keepalive": _bool_from_env("REDIS_SOCKET_KEEPALIVE", True),
        "max_connections": _int_from_env("REDIS_MAX_CONNECTIONS", 100, minimum=1),
        "retry_on_timeout": _bool_from_env("REDIS_RETRY_ON_TIMEOUT", False),
    }


def get_redis(url: str) -> redis.Redis:
    return redis.from_url(url, **redis_connection_kwargs())


def ensure_stream_group(client: redis.Redis, stream: str, group: str) -> None:
    try:
        client.xgroup_create(stream, group, id="0-0", mkstream=True)
    except Exception:
        return


def normalize_stream_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bytes)):
            normalized[str(key)] = value
        else:
            normalized[str(key)] = json.dumps(value)
    return normalized


def xadd_with_retry(
    client: redis.Redis,
    stream: str,
    payload: dict[str, Any],
    retries: int = 3,
    *,
    maxlen: int | None = None,
) -> str | None:
    normalized = normalize_stream_payload(payload)
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            if maxlen:
                message_id = client.xadd(stream, normalized, maxlen=maxlen, approximate=True)
            else:
                message_id = client.xadd(stream, normalized)
            if isinstance(message_id, bytes):
                return message_id.decode("utf-8")
            return str(message_id)
        except Exception as exc:
            last_error = exc
            if attempt < retries - 1:
                EVENT_PUBLISH_RETRIES.labels(stream=stream).inc()
                logger.warning(
                    "Redis XADD failed, retrying",
                    extra={"stream": stream, "attempt": attempt + 1, "max_attempts": retries},
                )
                time.sleep(min(2 ** attempt, 4))

    if last_error is not None:
        logger.error(
            "Redis XADD failed after retries",
            extra={"stream": stream, "attempts": retries, "error": str(last_error)},
        )
    return None


def publish_event(
    client: redis.Redis,
    stream: str,
    payload: dict[str, Any],
    retries: int = 3,
    *,
    maxlen: int | None = None,
) -> tuple[bool, str | None]:
    valid, reason = validate_event(payload)
    if not valid:
        EVENT_PUBLISH_ATTEMPTS.labels(stream=stream, result="invalid").inc()
        logger.error(
            "Rejected invalid event payload",
            extra={"stream": stream, "reason": reason, "event_type": payload.get("event_type")},
        )
        persist_event(stream, payload, published=False, publish_error=reason)
        return False, None

    message_id = xadd_with_retry(client, stream, payload, retries=retries, maxlen=maxlen)
    ok = message_id is not None
    EVENT_PUBLISH_ATTEMPTS.labels(stream=stream, result="success" if ok else "failed").inc()

    if not ok:
        logger.error(
            "Event publish failed",
            extra={"stream": stream, "event_type": payload.get("event_type")},
        )

    persist_event(
        stream,
        payload,
        published=ok,
        stream_message_id=message_id,
        publish_error=None if ok else "redis_publish_failed",
    )
    return ok, message_id
