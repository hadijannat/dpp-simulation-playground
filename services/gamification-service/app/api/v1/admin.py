from __future__ import annotations

import json
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from redis import Redis
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...config import DLQ_STREAM_MAXLEN, REDIS_URL, RETRY_STREAM_MAXLEN, STREAM_MAXLEN
from ...core.db import get_db
from ...engine.event_consumer import invalidate_runtime_cache
from ...models.achievement import Achievement
from ...models.point_rule import PointRule
from services.shared.redis_client import xadd_with_retry

STREAM = "simulation.events"
RETRY_STREAM = "simulation.events.retry"
DLQ_STREAM = "simulation.events.dlq"
DLQ_REPLAY_SET = "simulation.events.dlq.replayed"

router = APIRouter()


def _decode(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def _maybe_json(value: Any) -> Any:
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


def _safe_xlen(client: Redis, stream: str) -> int:
    try:
        return int(client.xlen(stream))
    except Exception:
        return 0


def _group_pending(client: Redis, stream: str, group_name: str) -> int:
    try:
        groups = client.xinfo_groups(stream)
    except Exception:
        return 0
    for group in groups:
        name = _decode(group.get("name"))
        if name == group_name:
            return int(group.get("pending", 0))
    return 0


def _trim_stream(client: Redis, stream: str, maxlen: int) -> int:
    try:
        return int(client.xtrim(stream, maxlen=maxlen, approximate=True))
    except Exception:
        return 0


def _pending_entries(client: Redis, stream: str, group: str, limit: int) -> list[dict[str, Any]]:
    try:
        rows = client.xpending_range(stream, group, min="-", max="+", count=limit)
    except Exception:
        return []

    items: list[dict[str, Any]] = []
    for row in rows:
        items.append(
            {
                "message_id": _decode(row.get("message_id")),
                "consumer": _decode(row.get("consumer")),
                "idle_ms": int(row.get("time_since_delivered", 0) or 0),
                "deliveries": int(row.get("times_delivered", 0) or 0),
            }
        )
    return items


def _decode_stream_entry(message_id: Any, data: dict[Any, Any]) -> dict[str, Any]:
    decoded = {_decode(key): _maybe_json(_decode(value)) for key, value in data.items()}
    event = decoded.get("event")
    if isinstance(event, str):
        decoded["event"] = _maybe_json(event)
    return {"message_id": _decode(message_id), **decoded}


def _load_dlq_entry(client: Redis, message_id: str) -> dict[str, Any] | None:
    try:
        rows = client.xrange(DLQ_STREAM, min=message_id, max=message_id, count=1)
    except Exception:
        return None
    if not rows:
        return None
    msg_id, payload = rows[0]
    return _decode_stream_entry(msg_id, payload)


class PointRuleUpsertRequest(BaseModel):
    event_type: str
    points: int
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class PointRulePatchRequest(BaseModel):
    points: int | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None


class AchievementUpsertRequest(BaseModel):
    code: str
    name: str
    description: str | None = None
    points: int = 0
    criteria: dict[str, Any] = Field(default_factory=dict)
    category: str | None = None


class AchievementPatchRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    points: int | None = None
    criteria: dict[str, Any] | None = None
    category: str | None = None


class DlqReplayRequest(BaseModel):
    message_ids: list[str] = Field(default_factory=list)
    limit: int = 20
    delete_after_replay: bool = True


@router.get("/admin/stream-status")
def stream_status(request: Request):
    require_roles(request.state.user, ["developer", "admin"])
    client = Redis.from_url(REDIS_URL)
    return {
        "stream": STREAM,
        "retry_stream": RETRY_STREAM,
        "dlq_stream": DLQ_STREAM,
        "sizes": {
            "stream": _safe_xlen(client, STREAM),
            "retry": _safe_xlen(client, RETRY_STREAM),
            "dlq": _safe_xlen(client, DLQ_STREAM),
        },
        "pending": {
            "stream": _group_pending(client, STREAM, "gamification"),
            "retry": _group_pending(client, RETRY_STREAM, "gamification-retry"),
        },
        "maxlen": {
            "stream": STREAM_MAXLEN,
            "retry": RETRY_STREAM_MAXLEN,
            "dlq": DLQ_STREAM_MAXLEN,
        },
    }


@router.get("/admin/stream/pending")
def stream_pending(request: Request, limit: int = 50):
    require_roles(request.state.user, ["developer", "admin"])
    bounded_limit = max(1, min(limit, 200))
    client = Redis.from_url(REDIS_URL)
    return {
        "items": {
            "stream": _pending_entries(client, STREAM, "gamification", bounded_limit),
            "retry": _pending_entries(client, RETRY_STREAM, "gamification-retry", bounded_limit),
        },
        "totals": {
            "stream": _group_pending(client, STREAM, "gamification"),
            "retry": _group_pending(client, RETRY_STREAM, "gamification-retry"),
        },
        "limit": bounded_limit,
    }


@router.get("/admin/stream/dlq")
def stream_dlq(request: Request, limit: int = 50, offset: int = 0):
    require_roles(request.state.user, ["developer", "admin"])
    bounded_limit = max(1, min(limit, 200))
    bounded_offset = max(0, offset)

    client = Redis.from_url(REDIS_URL)
    rows = client.xrevrange(DLQ_STREAM, max="+", min="-", count=bounded_limit + bounded_offset)
    selected = rows[bounded_offset : bounded_offset + bounded_limit]
    items = [_decode_stream_entry(message_id, payload) for message_id, payload in selected]

    return {
        "items": items,
        "total": _safe_xlen(client, DLQ_STREAM),
        "limit": bounded_limit,
        "offset": bounded_offset,
    }


@router.post("/admin/stream/dlq/replay")
def replay_dlq(request: Request, payload: DlqReplayRequest):
    require_roles(request.state.user, ["developer", "admin"])
    bounded_limit = max(1, min(payload.limit, 200))

    client = Redis.from_url(REDIS_URL)
    target_ids: list[str] = []
    if payload.message_ids:
        target_ids = payload.message_ids[:bounded_limit]
    else:
        rows = client.xrange(DLQ_STREAM, min="-", max="+", count=bounded_limit)
        target_ids = [_decode(message_id) for message_id, _ in rows]

    replayed = 0
    skipped = 0
    failed = 0
    results: list[dict[str, Any]] = []

    for message_id in target_ids:
        entry = _load_dlq_entry(client, message_id)
        if entry is None:
            failed += 1
            results.append({"message_id": message_id, "status": "missing"})
            continue

        raw_event = entry.get("event")
        if not isinstance(raw_event, dict):
            failed += 1
            results.append({"message_id": message_id, "status": "invalid_event"})
            continue

        event_payload = dict(raw_event)
        event_id = str(event_payload.get("event_id") or message_id)
        if int(client.sadd(DLQ_REPLAY_SET, event_id)) == 0:
            skipped += 1
            results.append({"message_id": message_id, "status": "already_replayed", "event_id": event_id})
            continue

        metadata = event_payload.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        metadata["replayed_from_dlq"] = True
        metadata["dlq_message_id"] = message_id
        metadata["replayed_at"] = time.time()
        event_payload["metadata"] = metadata

        stream_message_id = xadd_with_retry(client, STREAM, event_payload)
        if stream_message_id is None:
            client.srem(DLQ_REPLAY_SET, event_id)
            failed += 1
            results.append({"message_id": message_id, "status": "requeue_failed", "event_id": event_id})
            continue

        replayed += 1
        results.append(
            {
                "message_id": message_id,
                "status": "replayed",
                "event_id": event_id,
                "stream_message_id": stream_message_id,
            }
        )
        if payload.delete_after_replay:
            try:
                client.xdel(DLQ_STREAM, message_id)
            except Exception:
                pass

    return {
        "requested": len(target_ids),
        "replayed": replayed,
        "skipped": skipped,
        "failed": failed,
        "results": results,
    }


@router.post("/admin/stream/trim")
def trim_streams(request: Request):
    require_roles(request.state.user, ["developer", "admin"])
    client = Redis.from_url(REDIS_URL)
    return {
        "trimmed": {
            "stream": _trim_stream(client, STREAM, STREAM_MAXLEN),
            "retry": _trim_stream(client, RETRY_STREAM, RETRY_STREAM_MAXLEN),
            "dlq": _trim_stream(client, DLQ_STREAM, DLQ_STREAM_MAXLEN),
        },
        "maxlen": {
            "stream": STREAM_MAXLEN,
            "retry": RETRY_STREAM_MAXLEN,
            "dlq": DLQ_STREAM_MAXLEN,
        },
    }


def _serialize_point_rule(rule: PointRule) -> dict[str, Any]:
    return {
        "event_type": rule.event_type,
        "points": int(rule.points or 0),
        "is_active": bool(rule.is_active),
        "metadata": rule.rule_metadata or {},
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
    }


def _serialize_achievement(item: Achievement) -> dict[str, Any]:
    return {
        "code": item.code,
        "name": item.name,
        "description": item.description,
        "points": int(item.points or 0),
        "criteria": item.criteria or {},
        "category": item.category,
    }


@router.get("/admin/point-rules")
def list_point_rules(request: Request, include_inactive: bool = True, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin"])
    query = db.query(PointRule).order_by(PointRule.event_type.asc())
    if not include_inactive:
        query = query.filter(PointRule.is_active.is_(True))
    return {"items": [_serialize_point_rule(item) for item in query.all()]}


@router.post("/admin/point-rules")
def upsert_point_rule(request: Request, payload: PointRuleUpsertRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin"])
    event_type = payload.event_type.strip()
    if not event_type:
        raise HTTPException(status_code=422, detail="event_type is required")
    rule = db.query(PointRule).filter(PointRule.event_type == event_type).first()
    if not rule:
        rule = PointRule(event_type=event_type)
        db.add(rule)
    rule.points = payload.points
    rule.is_active = payload.is_active
    rule.rule_metadata = payload.metadata
    db.commit()
    db.refresh(rule)
    invalidate_runtime_cache()
    return _serialize_point_rule(rule)


@router.patch("/admin/point-rules/{event_type}")
def patch_point_rule(request: Request, event_type: str, payload: PointRulePatchRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin"])
    rule = db.query(PointRule).filter(PointRule.event_type == event_type).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Point rule not found")
    if payload.points is not None:
        rule.points = payload.points
    if payload.is_active is not None:
        rule.is_active = payload.is_active
    if payload.metadata is not None:
        rule.rule_metadata = payload.metadata
    db.commit()
    db.refresh(rule)
    invalidate_runtime_cache()
    return _serialize_point_rule(rule)


@router.get("/admin/achievements")
def list_achievement_defs(request: Request, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin"])
    items = db.query(Achievement).order_by(Achievement.code.asc()).all()
    return {"items": [_serialize_achievement(item) for item in items]}


@router.post("/admin/achievements")
def upsert_achievement(request: Request, payload: AchievementUpsertRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin"])
    code = payload.code.strip()
    if not code:
        raise HTTPException(status_code=422, detail="code is required")
    achievement = db.query(Achievement).filter(Achievement.code == code).first()
    if not achievement:
        achievement = Achievement(code=code, name=payload.name, criteria=payload.criteria)
        db.add(achievement)
    achievement.name = payload.name
    achievement.description = payload.description
    achievement.points = payload.points
    achievement.criteria = payload.criteria
    achievement.category = payload.category
    db.commit()
    db.refresh(achievement)
    invalidate_runtime_cache()
    return _serialize_achievement(achievement)


@router.patch("/admin/achievements/{code}")
def patch_achievement(request: Request, code: str, payload: AchievementPatchRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["developer", "admin"])
    achievement = db.query(Achievement).filter(Achievement.code == code).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    if payload.name is not None:
        achievement.name = payload.name
    if payload.description is not None:
        achievement.description = payload.description
    if payload.points is not None:
        achievement.points = payload.points
    if payload.criteria is not None:
        achievement.criteria = payload.criteria
    if payload.category is not None:
        achievement.category = payload.category
    db.commit()
    db.refresh(achievement)
    invalidate_runtime_cache()
    return _serialize_achievement(achievement)
