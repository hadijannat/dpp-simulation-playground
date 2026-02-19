from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import COMPLIANCE_URL, PLATFORM_CORE_URL
from app.main import app

client = TestClient(app)

HEADERS = {
    "X-Dev-User": "v2-compliance-tester",
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


def test_v2_compliance_reports_normalized_with_new_shape(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, Any]] = []

    def fake_request(method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(
            {
                "items": [{"id": "r-1", "status": "non-compliant", "created_at": "2025-01-01T00:00:00"}],
                "total": 11,
                "limit": 5,
                "offset": 2,
            }
        )

    monkeypatch.setattr("app.core.proxy.requests.request", fake_request)

    response = client.get("/api/v2/compliance/reports?limit=5&offset=2", headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 11
    assert body["limit"] == 5
    assert body["offset"] == 2
    assert body["items"] == body["reports"]
    assert calls[0]["url"] == f"{COMPLIANCE_URL}/api/v1/reports"


def test_v2_compliance_reports_normalized_with_legacy_shape(monkeypatch: pytest.MonkeyPatch):
    def fake_request(method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any):
        return DummyResponse({"reports": [{"id": "r-legacy", "status": "compliant"}]})

    monkeypatch.setattr("app.core.proxy.requests.request", fake_request)

    response = client.get("/api/v2/compliance/reports", headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == "r-legacy"
    assert body["total"] == 1


def test_v2_apply_fix_forwards_json_patch_payload(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, Any]] = []

    def fake_request(method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse({"run_id": "run-1", "status": "compliant", "payload": {}})

    monkeypatch.setattr("app.core.proxy.requests.request", fake_request)

    response = client.post(
        "/api/v2/compliance/runs/run-1/apply-fix",
        json={"operations": [{"op": "replace", "path": "/battery/weight", "value": 10}]},
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert calls
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == f"{PLATFORM_CORE_URL}/api/v2/core/compliance/runs/run-1/apply-fix"
    assert calls[0]["json"]["operations"][0]["path"] == "/battery/weight"
