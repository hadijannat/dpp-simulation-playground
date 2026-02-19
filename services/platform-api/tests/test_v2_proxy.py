"""Tests for the v2 proxy routes on platform-api.

Verifies that platform-api correctly proxies requests to platform-core
for journeys, digital-twins, and feedback endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import COLLABORATION_URL, EDC_URL, GAMIFICATION_URL, PLATFORM_CORE_URL
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

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.post(
        "/api/v2/journeys/runs",
        json={
            "template_code": "manufacturer-core-e2e",
            "role": "manufacturer",
            "locale": "en",
        },
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

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

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
        "nodes": [{"id": "n1", "label": "Battery", "type": "product", "payload": {}}],
        "edges": [],
        "timeline": [],
    }

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.get(f"/api/v2/digital-twins/{dpp_id}", headers=HEADERS)
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls, "Expected v2 proxy to call platform-core"
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == f"{PLATFORM_CORE_URL}/api/v2/core/digital-twins/{dpp_id}"


def test_get_digital_twin_history_proxies_to_platform_core(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[dict[str, Any]] = []
    dpp_id = "dpp-twin-999"
    upstream_payload = {
        "dpp_id": dpp_id,
        "items": [
            {
                "snapshot_id": "s1",
                "label": "v1",
                "created_at": "2025-01-01T00:00:00",
                "metadata": {},
                "node_count": 1,
                "edge_count": 0,
            }
        ],
        "total": 1,
        "limit": 10,
        "offset": 0,
    }

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.get(
        f"/api/v2/digital-twins/{dpp_id}/history", params={"limit": 10}, headers=HEADERS
    )
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls, "Expected v2 proxy to call platform-core"
    assert calls[0]["method"] == "GET"
    assert (
        calls[0]["url"]
        == f"{PLATFORM_CORE_URL}/api/v2/core/digital-twins/{dpp_id}/history"
    )
    assert calls[0]["params"] == {"limit": 10, "offset": 0}


def test_get_digital_twin_diff_proxies_to_platform_core(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[dict[str, Any]] = []
    dpp_id = "dpp-twin-999"
    upstream_payload = {
        "dpp_id": dpp_id,
        "from_snapshot": {
            "snapshot_id": "s1",
            "label": "before",
            "created_at": "2025-01-01T00:00:00",
            "metadata": {},
            "node_count": 1,
            "edge_count": 0,
        },
        "to_snapshot": {
            "snapshot_id": "s2",
            "label": "after",
            "created_at": "2025-01-01T00:01:00",
            "metadata": {},
            "node_count": 2,
            "edge_count": 1,
        },
        "diff": {
            "summary": {
                "nodes_added": 1,
                "nodes_removed": 0,
                "nodes_changed": 0,
                "edges_added": 1,
                "edges_removed": 0,
                "edges_changed": 0,
            },
            "nodes": {"added": [{"id": "transfer"}], "removed": [], "changed": []},
            "edges": {
                "added": [{"id": "product-transfer"}],
                "removed": [],
                "changed": [],
            },
            "generated_at": "2025-01-01T00:02:00",
        },
    }

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.get(
        f"/api/v2/digital-twins/{dpp_id}/diff",
        params={"from": "s1", "to": "s2"},
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls, "Expected v2 proxy to call platform-core"
    assert calls[0]["method"] == "GET"
    assert (
        calls[0]["url"]
        == f"{PLATFORM_CORE_URL}/api/v2/core/digital-twins/{dpp_id}/diff"
    )
    assert calls[0]["params"] == {"from": "s1", "to": "s2"}


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

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

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


# ---- EDC ---------------------------------------------------------------------


def test_simulate_negotiation_proxies_to_edc(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, Any]] = []
    negotiation_id = "neg-123"
    upstream_payload = {
        "id": negotiation_id,
        "state": "REQUESTING",
        "policy": {},
        "asset_id": "asset-1",
        "consumer_id": "consumer",
        "provider_id": "provider",
        "state_history": [],
        "session_id": None,
    }

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.post(
        f"/api/v2/edc/negotiations/{negotiation_id}/simulate",
        json={"step_delay_ms": 0},
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls
    assert calls[0]["method"] == "POST"
    assert (
        calls[0]["url"]
        == f"{EDC_URL}/api/v1/edc/negotiations/{negotiation_id}/simulate"
    )
    assert calls[0]["json"] == {"step_delay_ms": 0, "callback_url": None}


def test_simulate_transfer_proxies_to_edc(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, Any]] = []
    transfer_id = "tr-123"
    upstream_payload = {
        "id": transfer_id,
        "state": "PROVISIONING",
        "asset_id": "asset-1",
        "consumer_id": "consumer",
        "provider_id": "provider",
        "state_history": [],
        "session_id": None,
    }

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.post(
        f"/api/v2/edc/transfers/{transfer_id}/simulate",
        json={"step_delay_ms": 0},
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == f"{EDC_URL}/api/v1/edc/transfers/{transfer_id}/simulate"
    assert calls[0]["json"] == {"step_delay_ms": 0, "callback_url": None}


# ---- Gamification -------------------------------------------------------------


def test_get_leaderboard_proxies_window_and_role_params(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[dict[str, Any]] = []
    upstream_payload = {
        "items": [
            {
                "user_id": "u-1",
                "total_points": 55,
                "level": 1,
                "window": "weekly",
                "role": "manufacturer",
            }
        ],
        "window": "weekly",
        "role": "manufacturer",
    }

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.get(
        "/api/v2/gamification/leaderboard?limit=5&offset=1&window=weekly&role=manufacturer",
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == f"{GAMIFICATION_URL}/api/v1/leaderboard"
    assert calls[0]["params"] == {
        "limit": 5,
        "offset": 1,
        "window": "weekly",
        "role": "manufacturer",
    }


# ---- Collaboration -------------------------------------------------------------


def test_list_comments_proxies_to_collaboration(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, Any]] = []
    upstream_payload = {
        "items": [
            {
                "id": "c-1",
                "target_id": "gap-1",
                "content": "Looks good",
                "created_at": "2025-01-01T00:00:00",
            }
        ]
    }

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.get(
        "/api/v2/collaboration/comments?target_id=gap-1&limit=10&offset=2",
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == f"{COLLABORATION_URL}/api/v1/comments"
    assert calls[0]["params"] == {"target_id": "gap-1", "limit": 10, "offset": 2}


def test_add_comment_proxies_to_collaboration(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, Any]] = []
    upstream_payload = {
        "id": "c-2",
        "target_id": "gap-1",
        "content": "Need more detail",
        "created_at": "2025-01-01T00:00:01",
    }

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.post(
        "/api/v2/collaboration/comments",
        json={"target_id": "gap-1", "content": "Need more detail"},
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == f"{COLLABORATION_URL}/api/v1/comments"
    assert calls[0]["json"] == {"target_id": "gap-1", "content": "Need more detail"}


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
            "GET",
            "/api/v2/digital-twins/dt-1/history",
            None,
            f"{PLATFORM_CORE_URL}/api/v2/core/digital-twins/dt-1/history",
        ),
        (
            "POST",
            "/api/v2/feedback/csat",
            {"score": 3, "role": "developer"},
            f"{PLATFORM_CORE_URL}/api/v2/core/feedback/csat",
        ),
        (
            "GET",
            "/api/v2/gamification/leaderboard",
            None,
            f"{GAMIFICATION_URL}/api/v1/leaderboard",
        ),
        (
            "GET",
            "/api/v2/collaboration/comments",
            None,
            f"{COLLABORATION_URL}/api/v1/comments",
        ),
        (
            "POST",
            "/api/v2/edc/negotiations/neg-1/simulate",
            {"step_delay_ms": 10},
            f"{EDC_URL}/api/v1/edc/negotiations/neg-1/simulate",
        ),
        (
            "POST",
            "/api/v2/edc/transfers/tr-1/simulate",
            {"step_delay_ms": 10},
            f"{EDC_URL}/api/v1/edc/transfers/tr-1/simulate",
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

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
        return DummyResponse({"detail": "Upstream not found"}, status_code=404)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    request_kwargs: dict[str, Any] = {"headers": HEADERS}
    if body is not None:
        request_kwargs["json"] = body
    if path.endswith("/history"):
        request_kwargs["params"] = {"limit": 25, "offset": 0}

    response = client.request(method, path, **request_kwargs)
    assert response.status_code == 404
    assert response.json()["detail"] == "Upstream not found"


def test_v2_proxy_forwards_request_id_header(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict[str, Any]] = []

    def fake_request(
        method: str, url: str, params: Any = None, json: Any = None, **kwargs: Any
    ):
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

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    request_id = "req-test-123"
    response = client.get(
        "/api/v2/journeys/templates",
        headers={**HEADERS, "X-Request-ID": request_id},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == request_id
    assert calls, "Expected v2 proxy to call platform-core"
    assert calls[0]["headers"].get("X-Request-ID") == request_id


def test_v2_proxy_rejects_missing_bearer_when_dev_headers_disallowed(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("app.core.proxy.ALLOW_DEV_HEADERS", False)
    response = client.get("/api/v2/journeys/templates", headers=HEADERS)
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"
