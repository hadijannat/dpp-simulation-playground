from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import PLATFORM_CORE_URL
from app.main import app


client = TestClient(app)

HEADERS = {
    "X-Dev-User": "v2-events-tester",
    "X-Dev-Roles": "developer,manufacturer,admin,regulator,consumer,recycler",
}


@dataclass
class DummyResponse:
    payload: Any
    status_code: int = 200

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def content(self) -> bytes:
        import json

        return json.dumps(self.payload).encode()

    def json(self) -> Any:
        return self.payload


def test_v2_events_proxy_forwards_filters(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, Any]] = []
    upstream_payload = {
        "items": [
            {
                "event_id": "evt-1",
                "event_type": "story_step_completed",
                "user_id": "user-1",
                "timestamp": "2026-01-01T00:00:00+00:00",
                "source_service": "simulation-engine",
                "session_id": "sess-1",
                "run_id": "run-1",
                "request_id": "req-1",
                "metadata": {},
                "version": "1",
                "stream": "simulation.events",
                "stream_message_id": "1-0",
                "published": True,
            }
        ],
        "total": 1,
        "limit": 25,
        "offset": 0,
    }

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.get(
        "/api/v2/events?session_id=sess-1&event_type=story_step_completed&limit=25&offset=0",
        headers=HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["event_id"] == "evt-1"
    assert calls
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == f"{PLATFORM_CORE_URL}/api/v2/core/events"
    assert calls[0]["params"]["session_id"] == "sess-1"
    assert calls[0]["params"]["event_type"] == "story_step_completed"


def test_v2_events_proxy_normalizes_missing_pagination(monkeypatch: pytest.MonkeyPatch):
    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        return DummyResponse({"items": []})

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.get(
        "/api/v2/events?run_id=run-77&limit=10&offset=5", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["limit"] == 10
    assert body["offset"] == 5
