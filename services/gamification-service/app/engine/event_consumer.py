import json
import threading
import time
from datetime import date
from typing import Dict, Any
from redis import Redis
import yaml
from pathlib import Path
from uuid import uuid4

from ..config import REDIS_URL
from ..core.db import SessionLocal
from ..models.user_achievement import UserAchievement
from ..models.achievement import Achievement
from .points_engine import add_points
from services.shared.redis_client import ensure_stream_group, xadd_with_retry

STREAM = "simulation.events"
DLQ_STREAM = "simulation.events.dlq"
RETRY_LIMIT = 3


def _load_point_rules() -> Dict[str, int]:
    path = Path(__file__).resolve().parents[1] / "definitions" / "point_rules.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def _load_achievement_defs():
    path = Path(__file__).resolve().parents[1] / "definitions" / "achievements.yaml"
    if not path.exists():
        return []
    return yaml.safe_load(path.read_text()) or []


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


def _handle_failure(client: Redis, msg_id: str, event: Dict[str, Any], error: Exception) -> None:
    retry = int(event.get("retry", 0)) if event.get("retry") is not None else 0
    if retry < RETRY_LIMIT:
        next_event = dict(event)
        next_event["retry"] = retry + 1
        next_event["last_error"] = str(error)
        xadd_with_retry(client, STREAM, next_event)
        time.sleep(min(2 ** retry, 4))
    else:
        payload = {
            "event": json.dumps(event),
            "error": str(error),
        }
        xadd_with_retry(client, DLQ_STREAM, payload)
    try:
        client.xack(STREAM, "gamification", msg_id)
    except Exception:
        return


def _worker():
    client = Redis.from_url(REDIS_URL)
    group = "gamification"
    consumer = f"consumer-{uuid4()}"
    ensure_stream_group(client, STREAM, group)
    point_rules = _load_point_rules()
    achievements = _load_achievement_defs()
    while True:
        try:
            result = client.xreadgroup(group, consumer, {STREAM: ">"}, block=5000, count=10)
        except Exception:
            time.sleep(2)
            continue
        if not result:
            continue
        for _, messages in result:
            for msg_id, data in messages:
                decoded = {_decode(k): _maybe_json(_decode(v)) for k, v in data.items()}
                try:
                    _process_event(decoded, point_rules, achievements)
                    client.xack(STREAM, group, msg_id)
                except Exception as exc:
                    _handle_failure(client, msg_id, decoded, exc)


def start_consumer():
    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
