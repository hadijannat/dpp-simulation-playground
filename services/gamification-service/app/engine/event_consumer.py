import json
import threading
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

STREAM = "simulation.events"


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


def _process_event(event: Dict[str, Any], point_rules: Dict[str, int], achievements: list[dict]):
    event_type = event.get("event_type")
    user_id = event.get("user_id")
    if not event_type or not user_id:
        return
    points = point_rules.get(event_type)
    if points:
        add_points(user_id, points, date.today())
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


def _worker():
    client = Redis.from_url(REDIS_URL)
    last_id = "0-0"
    point_rules = _load_point_rules()
    achievements = _load_achievement_defs()
    while True:
        result = client.xread({STREAM: last_id}, block=5000, count=10)
        if not result:
            continue
        for _, messages in result:
            for msg_id, data in messages:
                last_id = msg_id
                decoded = { _decode(k): _decode(v) for k, v in data.items() }
                _process_event(decoded, point_rules, achievements)


def start_consumer():
    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
