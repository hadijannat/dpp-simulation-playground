from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import SIMULATION_URL
from app.main import app

client = TestClient(app)

HEADERS = {
    "X-Dev-User": "v2-simulation-tester",
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


def test_v2_pause_session_proxies_to_simulation_service(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[dict[str, Any]] = []

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(
            {"id": "s-1", "user_id": "u-1", "role": "manufacturer", "state": {}}
        )

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.post("/api/v2/simulation/sessions/s-1/pause", headers=HEADERS)
    assert response.status_code == 200
    assert calls
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == f"{SIMULATION_URL}/api/v1/sessions/s-1/pause"


def test_v2_progress_normalizes_items_and_alias(monkeypatch: pytest.MonkeyPatch):
    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        return DummyResponse(
            {
                "items": [
                    {
                        "id": "p-1",
                        "status": "in_progress",
                        "completion_percentage": 30,
                        "steps_completed": [],
                    }
                ],
                "total": 1,
                "limit": 10,
                "offset": 0,
            }
        )

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.get(
        "/api/v2/simulation/progress?limit=10&offset=0", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == body["progress"]
    assert body["total"] == 1
