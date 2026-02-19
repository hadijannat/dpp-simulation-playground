import json
import logging
import os
import threading
import time
from datetime import date
from typing import Dict, Any
from redis import Redis
from uuid import uuid4

from ..config import (
    DLQ_STREAM_MAXLEN,
    REDIS_URL,
    RETRY_STREAM_MAXLEN,
    STREAM_MAXLEN,
    STREAM_TRIM_INTERVAL_SECONDS,
)
from ..core.db import SessionLocal
from ..models.user_achievement import UserAchievement
from ..models.achievement import Achievement
from .points_engine import add_points
from .achievement_engine import load_achievements
from .point_rule_engine import load_active_point_rules, load_point_rules_from_yaml
from services.shared.redis_client import ensure_stream_group, xadd_with_retry
from services.shared.events import validate_event

STREAM = "simulation.events"
RETRY_STREAM = "simulation.events.retry"
DLQ_STREAM = "simulation.events.dlq"
RETRY_LIMIT = 3
RULE_CACHE_TTL_SECONDS = max(5, int(os.getenv("RULE_CACHE_TTL_SECONDS", "30")))
logger = logging.getLogger(__name__)

_rules_cache: dict[str, Any] = {
    "loaded_at": 0.0,
    "point_rules": {},
    "achievements": [],
}


def invalidate_runtime_cache() -> None:
    _rules_cache["loaded_at"] = 0.0


def _load_achievement_defs_from_db() -> list[dict]:
    db = SessionLocal()
    try:
        rows = db.query(Achievement).order_by(Achievement.id.asc()).all()
        return [
            {
                "code": row.code,
                "name": row.name,
                "points": int(row.points or 0),
                "criteria": row.criteria or {},
                "category": row.category,
            }
            for row in rows
            if row.code
        ]
    finally:
        db.close()


def _load_runtime_rules() -> tuple[Dict[str, int], list[dict]]:
    now = time.time()
    loaded_at = float(_rules_cache.get("loaded_at", 0.0) or 0.0)
    if now - loaded_at < RULE_CACHE_TTL_SECONDS:
        return dict(_rules_cache.get("point_rules", {})), list(_rules_cache.get("achievements", []))

    point_rules: Dict[str, int] = {}
    db = SessionLocal()
    try:
        point_rules = load_active_point_rules(db)
    finally:
        db.close()
    if not point_rules:
        point_rules = load_point_rules_from_yaml()

    achievements = _load_achievement_defs_from_db()
    if not achievements:
        achievements = load_achievements()

    _rules_cache["loaded_at"] = now
    _rules_cache["point_rules"] = dict(point_rules)
    _rules_cache["achievements"] = list(achievements)
    return point_rules, achievements


def _decode(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def _maybe_json(value):
    if not isinstance(value, str):
        return value
    trimmed = value.strip()
    if not trimmed:
        return value
    if trimmed[0] in ("{", "["):
        try:
            return json.loads(trimmed)
        except json.JSONDecodeError:
            return value
    return value


def _process_event(event: Dict[str, Any], point_rules: Dict[str, int], achievements: list[dict]):
    event_type = event.get("event_type")
    user_id = event.get("user_id")
    if not event_type or not user_id:
        return
    points = point_rules.get(event_type)
    if points:
        add_points(user_id, points, date.today(), event.get("metadata"))
    if not achievements:
        return
    db = SessionLocal()
    try:
        for definition in achievements:
            criteria = definition.get("criteria", {})
            if criteria.get("event") != event_type:
                continue
            achievement = db.query(Achievement).filter(Achievement.code == definition.get("code")).first()
            if not achievement:
                continue
            existing = (
                db.query(UserAchievement)
                .filter(UserAchievement.user_id == user_id, UserAchievement.achievement_id == achievement.id)
                .first()
            )
            if existing:
                continue
            record = UserAchievement(id=uuid4(), user_id=user_id, achievement_id=achievement.id, context=event)
            db.add(record)
        db.commit()
    finally:
        db.close()


def _to_dlq(client: Redis, event: Dict[str, Any], error: Exception) -> None:
    payload = {
        "event": json.dumps(event),
        "error": str(error),
        "failed_at": time.time(),
    }
    xadd_with_retry(client, DLQ_STREAM, payload, maxlen=DLQ_STREAM_MAXLEN)


def _handle_stream_failure(client: Redis, msg_id: str, event: Dict[str, Any], error: Exception) -> None:
    error_text = str(error)
    retry = int(event.get("retry", 0) or 0)
    is_schema_error = error_text.startswith("invalid event:")

    if is_schema_error:
        _to_dlq(client, event, error)
    elif retry < RETRY_LIMIT:
        next_event = dict(event)
        next_event["retry"] = retry + 1
        next_event["last_error"] = error_text
        next_event["retry_delay_seconds"] = min(2 ** retry, 8)
        xadd_with_retry(client, RETRY_STREAM, next_event, maxlen=RETRY_STREAM_MAXLEN)
    else:
        _to_dlq(client, event, error)
    try:
        client.xack(STREAM, "gamification", msg_id)
    except Exception:
        return


def _process_stream_message(
    client: Redis,
    msg_id: str,
    data: dict,
    point_rules: Dict[str, int],
    achievements: list[dict],
) -> None:
    decoded = {_decode(k): _maybe_json(_decode(v)) for k, v in data.items()}
    is_valid, reason = validate_event(decoded)
    if not is_valid:
        raise ValueError(f"invalid event: {reason}")
    _process_event(decoded, point_rules, achievements)
    client.xack(STREAM, "gamification", msg_id)


def _stream_worker():
    client = Redis.from_url(REDIS_URL)
    group = "gamification"
    consumer = f"consumer-{uuid4()}"
    ensure_stream_group(client, STREAM, group)
    ensure_stream_group(client, RETRY_STREAM, "gamification-retry")
    while True:
        try:
            result = client.xreadgroup(group, consumer, {STREAM: ">"}, block=5000, count=10)
        except Exception:
            time.sleep(2)
            continue
        if not result:
            continue
        point_rules, achievements = _load_runtime_rules()
        for _, messages in result:
            for msg_id, data in messages:
                try:
                    _process_stream_message(client, msg_id, data, point_rules, achievements)
                except Exception as exc:
                    decoded = {_decode(k): _maybe_json(_decode(v)) for k, v in data.items()}
                    _handle_stream_failure(client, msg_id, decoded, exc)


def _retry_worker():
    client = Redis.from_url(REDIS_URL)
    group = "gamification-retry"
    consumer = f"retry-consumer-{uuid4()}"
    ensure_stream_group(client, RETRY_STREAM, group)
    while True:
        try:
            result = client.xreadgroup(group, consumer, {RETRY_STREAM: ">"}, block=5000, count=10)
        except Exception:
            time.sleep(2)
            continue
        if not result:
            continue
        for _, messages in result:
            for msg_id, data in messages:
                decoded = {_decode(k): _maybe_json(_decode(v)) for k, v in data.items()}
                try:
                    delay = float(decoded.get("retry_delay_seconds") or 0)
                    if delay > 0:
                        time.sleep(min(delay, 8))
                    retry_payload = dict(decoded)
                    retry_payload.pop("retry_delay_seconds", None)
                    xadd_with_retry(client, STREAM, retry_payload, maxlen=STREAM_MAXLEN)
                except Exception as exc:
                    _to_dlq(client, decoded, exc)
                finally:
                    try:
                        client.xack(RETRY_STREAM, group, msg_id)
                    except Exception:
                        pass


def _trim_stream(client: Redis, stream: str, maxlen: int) -> None:
    try:
        client.xtrim(stream, maxlen=maxlen, approximate=True)
    except Exception:
        logger.warning("Failed to trim stream", extra={"stream": stream, "maxlen": maxlen})


def _maintenance_worker():
    client = Redis.from_url(REDIS_URL)
    interval = max(10, STREAM_TRIM_INTERVAL_SECONDS)
    while True:
        _trim_stream(client, STREAM, STREAM_MAXLEN)
        _trim_stream(client, RETRY_STREAM, RETRY_STREAM_MAXLEN)
        _trim_stream(client, DLQ_STREAM, DLQ_STREAM_MAXLEN)
        time.sleep(interval)


def start_consumer():
    stream_thread = threading.Thread(target=_stream_worker, daemon=True)
    retry_thread = threading.Thread(target=_retry_worker, daemon=True)
    maintenance_thread = threading.Thread(target=_maintenance_worker, daemon=True)
    stream_thread.start()
    retry_thread.start()
    maintenance_thread.start()
    return stream_thread
