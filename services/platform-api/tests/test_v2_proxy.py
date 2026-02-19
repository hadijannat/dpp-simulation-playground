"""Tests for the v2 proxy routes on platform-api.

Verifies that platform-api correctly proxies requests to platform-core
for journeys, digital-twins, and feedback endpoints.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import PLATFORM_CORE_URL
from app.main import app


client = TestClient(app)

HEADERS = {
    "X-Dev-User": "v2-proxy-tester",
    "X-Dev-Roles": "developer,manufacturer,admin,regulator,consumer,recycler",
}


@dataclass
class DummyResponse:
    """Minimal stand-in for ``requests.Response``."""
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


# ---- Journeys -----------------------------------------------------------------

def test_create_run_proxies_to_platform_core(monkeypatch: pytest.MonkeyPatch):
    """POST /api/v2/journeys/runs proxies to platform-core's
    POST /api/v2/core/journeys/runs."""
    calls: list[dict[str, Any]] = []
    upstream_payload = {
        "id": "run-001",
        "template_code": "manufacturer-core-e2e",
        "role": "manufacturer",
        "locale": "en",
        "status": "active",
        "current_step": "create-product",
        "steps": [],
        "metadata": {},
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
    }

    def fake_request(method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.requests.request", fake_request)

    response = client.post(
        "/api/v2/journeys/runs",
        json={"template_code": "manufacturer-core-e2e", "role": "manufacturer", "locale": "en"},
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls, "Expected v2 proxy to call platform-core"
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == f"{PLATFORM_CORE_URL}/api/v2/core/journeys/runs"
    assert calls[0]["json"]["template_code"] == "manufacturer-core-e2e"


def test_get_run_proxies_to_platform_core(monkeypatch: pytest.MonkeyPatch):
    """GET /api/v2/journeys/runs/{run_id} proxies to platform-core's
    GET /api/v2/core/journeys/runs/{run_id}."""
    calls: list[dict[str, Any]] = []
    run_id = "run-abc-123"
    upstream_payload = {
        "id": run_id,
        "template_code": "manufacturer-core-e2e",
        "role": "manufacturer",
        "locale": "en",
        "status": "active",
        "current_step": "create-product",
        "steps": [],
        "metadata": {},
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
    }

    def fake_request(method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.requests.request", fake_request)

    response = client.get(f"/api/v2/journeys/runs/{run_id}", headers=HEADERS)
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls, "Expected v2 proxy to call platform-core"
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == f"{PLATFORM_CORE_URL}/api/v2/core/journeys/runs/{run_id}"


# ---- Digital Twins -----------------------------------------------------------

def test_get_digital_twin_proxies_to_platform_core(monkeypatch: pytest.MonkeyPatch):
    """GET /api/v2/digital-twins/{dpp_id} proxies to platform-core's
    GET /api/v2/core/digital-twins/{dpp_id}."""
    calls: list[dict[str, Any]] = []
    dpp_id = "dpp-twin-999"
    upstream_payload = {
        "dpp_id": dpp_id,
        "nodes": [
            {"id": "n1", "label": "Battery", "type": "product", "payload": {}}
        ],
        "edges": [],
        "timeline": [],
    }

    def fake_request(method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.requests.request", fake_request)

    response = client.get(f"/api/v2/digital-twins/{dpp_id}", headers=HEADERS)
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls, "Expected v2 proxy to call platform-core"
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == f"{PLATFORM_CORE_URL}/api/v2/core/digital-twins/{dpp_id}"


# ---- Feedback ----------------------------------------------------------------

def test_submit_csat_proxies_to_platform_core(monkeypatch: pytest.MonkeyPatch):
    """POST /api/v2/feedback/csat proxies to platform-core's
    POST /api/v2/core/feedback/csat."""
    calls: list[dict[str, Any]] = []
    upstream_payload = {
        "id": "fb-001",
        "score": 5,
        "locale": "en",
        "role": "manufacturer",
        "flow": "manufacturer-core-e2e",
        "comment": "Excellent",
        "created_at": "2025-01-01T00:00:00",
    }

    def fake_request(method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.requests.request", fake_request)

    response = client.post(
        "/api/v2/feedback/csat",
        json={
            "score": 5,
            "locale": "en",
            "role": "manufacturer",
            "flow": "manufacturer-core-e2e",
            "comment": "Excellent",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls, "Expected v2 proxy to call platform-core"
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == f"{PLATFORM_CORE_URL}/api/v2/core/feedback/csat"
    assert calls[0]["json"]["score"] == 5
    assert calls[0]["json"]["comment"] == "Excellent"


# ---- Error handling -----------------------------------------------------------

@pytest.mark.parametrize(
    "method,path,body,expected_url",
    [
        (
            "POST",
            "/api/v2/journeys/runs",
            {"template_code": "x", "role": "manufacturer"},
            f"{PLATFORM_CORE_URL}/api/v2/core/journeys/runs",
        ),
        (
            "GET",
            "/api/v2/journeys/runs/r-1",
            None,
            f"{PLATFORM_CORE_URL}/api/v2/core/journeys/runs/r-1",
        ),
        (
            "GET",
            "/api/v2/digital-twins/dt-1",
            None,
            f"{PLATFORM_CORE_URL}/api/v2/core/digital-twins/dt-1",
        ),
        (
            "POST",
            "/api/v2/feedback/csat",
            {"score": 3, "role": "developer"},
            f"{PLATFORM_CORE_URL}/api/v2/core/feedback/csat",
        ),
    ],
)
def test_v2_proxy_forwards_upstream_errors(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    path: str,
    body: dict[str, Any] | None,
    expected_url: str,
):
    """When platform-core returns an error, platform-api should forward
    the upstream status code and detail."""

    def fake_request(method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any):
        return DummyResponse({"detail": "Upstream not found"}, status_code=404)

    monkeypatch.setattr("app.core.proxy.requests.request", fake_request)

    request_kwargs: dict[str, Any] = {"headers": HEADERS}
    if body is not None:
        request_kwargs["json"] = body

    response = client.request(method, path, **request_kwargs)
    assert response.status_code == 404
    assert response.json()["detail"] == "Upstream not found"


def test_v2_proxy_forwards_request_id_header(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, Any]] = []

    def fake_request(method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any):
        calls.append(
            {
                "method": method,
                "url": url,
                "params": params,
                "json": json,
                "headers": kwargs.get("headers", {}),
            }
        )
        return DummyResponse({"items": []})

    monkeypatch.setattr("app.core.proxy.requests.request", fake_request)

    request_id = "req-test-123"
    response = client.get(
        "/api/v2/journeys/templates",
        headers={**HEADERS, "X-Request-ID": request_id},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == request_id
    assert calls, "Expected v2 proxy to call platform-core"
    assert calls[0]["headers"].get("X-Request-ID") == request_id


def test_v2_proxy_rejects_missing_bearer_when_dev_headers_disallowed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.core.proxy.ALLOW_DEV_HEADERS", False)
    response = client.get("/api/v2/journeys/templates", headers=HEADERS)
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"
