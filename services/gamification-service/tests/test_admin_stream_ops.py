from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

from app import main

STREAM = "simulation.events"
RETRY_STREAM = "simulation.events.retry"
DLQ_STREAM = "simulation.events.dlq"


def _set_roles(roles):
    def _verify(request):
        request.state.user = {"realm_access": {"roles": roles}}

    return _verify


class FakeRedis:
    def __init__(self):
        self.streams: dict[str, list[tuple[str, dict[str, Any]]]] = {
            STREAM: [],
            RETRY_STREAM: [],
            DLQ_STREAM: [
                (
                    "10-0",
                    {
                        "event": json.dumps(
                            {
                                "event_id": "evt-1",
                                "event_type": "story_step_completed",
                                "user_id": "user-1",
                                "timestamp": "2026-01-01T00:00:00+00:00",
                                "source_service": "simulation-engine",
                                "version": "1",
                            }
                        ),
                        "error": "boom",
                        "failed_at": "1700000000",
                    },
                )
            ],
        }
        self.replayed: set[str] = set()

    def xlen(self, stream: str) -> int:
        return len(self.streams.get(stream, []))

    def xinfo_groups(self, stream: str) -> list[dict[str, Any]]:
        if stream == STREAM:
            return [{"name": "gamification", "pending": 1}]
        if stream == RETRY_STREAM:
            return [{"name": "gamification-retry", "pending": 0}]
        return []

    def xpending_range(self, stream: str, group: str, min: str, max: str, count: int) -> list[dict[str, Any]]:
        if stream == STREAM and group == "gamification":
            return [
                {
                    "message_id": "1-0",
                    "consumer": "consumer-1",
                    "time_since_delivered": 250,
                    "times_delivered": 2,
                }
            ][:count]
        return []

    def xrevrange(self, stream: str, max: str, min: str, count: int):
        rows = list(reversed(self.streams.get(stream, [])))
        return rows[:count]

    def xrange(self, stream: str, min: str, max: str, count: int):
        rows = self.streams.get(stream, [])
        if min not in {"-", "+"} and min == max:
            rows = [row for row in rows if row[0] == min]
        return rows[:count]

    def sadd(self, key: str, value: str) -> int:
        if value in self.replayed:
            return 0
        self.replayed.add(value)
        return 1

    def srem(self, key: str, value: str) -> int:
        if value in self.replayed:
            self.replayed.remove(value)
            return 1
        return 0

    def xadd(self, stream: str, payload: dict[str, Any], maxlen: int | None = None, approximate: bool = False):
        next_id = f"{len(self.streams.get(stream, [])) + 1}-0"
        self.streams.setdefault(stream, []).append((next_id, payload))
        return next_id

    def xdel(self, stream: str, message_id: str) -> int:
        rows = self.streams.get(stream, [])
        original_len = len(rows)
        self.streams[stream] = [row for row in rows if row[0] != message_id]
        return 1 if len(self.streams[stream]) != original_len else 0


def test_admin_stream_pending_and_dlq(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(main, "verify_request", _set_roles(["admin"]))
    monkeypatch.setattr("app.api.v1.admin.Redis.from_url", lambda _url: fake_redis)

    client = TestClient(main.app)

    pending = client.get("/api/v1/admin/stream/pending")
    assert pending.status_code == 200
    pending_body = pending.json()
    assert pending_body["totals"]["stream"] == 1
    assert pending_body["items"]["stream"][0]["message_id"] == "1-0"

    dlq = client.get("/api/v1/admin/stream/dlq?limit=10&offset=0")
    assert dlq.status_code == 200
    dlq_body = dlq.json()
    assert dlq_body["total"] == 1
    assert dlq_body["items"][0]["message_id"] == "10-0"
    assert dlq_body["items"][0]["event"]["event_id"] == "evt-1"


def test_admin_dlq_replay_requeues_and_deletes(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(main, "verify_request", _set_roles(["admin"]))
    monkeypatch.setattr("app.api.v1.admin.Redis.from_url", lambda _url: fake_redis)

    client = TestClient(main.app)

    response = client.post(
        "/api/v1/admin/stream/dlq/replay",
        json={"message_ids": ["10-0"], "delete_after_replay": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["requested"] == 1
    assert body["replayed"] == 1
    assert body["skipped"] == 0
    assert body["failed"] == 0
    assert len(fake_redis.streams[STREAM]) == 1
    assert len(fake_redis.streams[DLQ_STREAM]) == 0


def test_admin_dlq_replay_skips_already_replayed(monkeypatch):
    fake_redis = FakeRedis()
    fake_redis.replayed.add("evt-1")

    monkeypatch.setattr(main, "verify_request", _set_roles(["admin"]))
    monkeypatch.setattr("app.api.v1.admin.Redis.from_url", lambda _url: fake_redis)

    client = TestClient(main.app)

    response = client.post(
        "/api/v1/admin/stream/dlq/replay",
        json={"message_ids": ["10-0"], "delete_after_replay": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["requested"] == 1
    assert body["replayed"] == 0
    assert body["skipped"] == 1
    assert body["failed"] == 0
    assert len(fake_redis.streams[STREAM]) == 0
    assert len(fake_redis.streams[DLQ_STREAM]) == 1
