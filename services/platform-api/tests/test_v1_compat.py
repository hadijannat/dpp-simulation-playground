from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
import requests
from fastapi.testclient import TestClient

from app.main import app
from app.config import (
    AAS_ADAPTER_URL,
    COLLABORATION_URL,
    COMPLIANCE_URL,
    EDC_URL,
    GAMIFICATION_URL,
    SIMULATION_URL,
)


client = TestClient(app)

HEADERS = {
    "X-Dev-User": "compat-tester",
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
        return b"{}"

    def json(self) -> Any:
        return self.payload


def test_v1_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "method,path,body,expected_url,upstream_payload",
    [
        (
            "GET",
            "/api/v1/stories",
            None,
            f"{SIMULATION_URL}/api/v1/stories",
            {"items": [{"code": "US-01", "title": "Story", "steps": []}]},
        ),
        (
            "POST",
            "/api/v1/sessions",
            {"role": "manufacturer", "state": {}},
            f"{SIMULATION_URL}/api/v1/sessions",
            {"id": "s-1", "user_id": "u-1", "role": "manufacturer", "state": {}},
        ),
        (
            "POST",
            "/api/v1/sessions/s-1/pause",
            None,
            f"{SIMULATION_URL}/api/v1/sessions/s-1/pause",
            {
                "id": "s-1",
                "user_id": "u-1",
                "role": "manufacturer",
                "state": {"lifecycle_state": "paused"},
            },
        ),
        (
            "GET",
            "/api/v1/progress?limit=5&offset=1",
            None,
            f"{SIMULATION_URL}/api/v1/progress",
            {"items": [], "total": 0, "limit": 5, "offset": 1, "progress": []},
        ),
        (
            "POST",
            "/api/v1/sessions/s-1/stories/US-01/steps/0/execute",
            {"payload": {"key": "value"}, "metadata": {"role": "manufacturer"}},
            f"{SIMULATION_URL}/api/v1/sessions/s-1/stories/US-01/steps/0/execute",
            {"result": {"status": "ok"}},
        ),
        (
            "GET",
            "/api/v1/aas/shells",
            None,
            f"{AAS_ADAPTER_URL}/api/v2/aas/shells",
            {"items": [{"id": "urn:uuid:example"}]},
        ),
        (
            "PATCH",
            "/api/v1/aas/submodels/sub-1/elements",
            {"elements": [{"idShort": "fieldA", "value": 7}]},
            f"{AAS_ADAPTER_URL}/api/v2/aas/submodels/sub-1/elements",
            {
                "status": "updated",
                "submodel_id": "sub-1",
                "elements": [{"idShort": "fieldA", "value": 7}],
            },
        ),
        (
            "POST",
            "/api/v1/compliance/check",
            {"data": {"product_name": "Battery"}, "regulations": ["ESPR"]},
            f"{COMPLIANCE_URL}/api/v1/compliance/check",
            {"status": "non-compliant", "violations": [{"path": "$.product_name"}]},
        ),
        (
            "GET",
            "/api/v1/reports?session_id=s-1&limit=5",
            None,
            f"{COMPLIANCE_URL}/api/v1/reports",
            {"reports": []},
        ),
        (
            "POST",
            "/api/v1/edc/negotiations",
            {
                "asset_id": "asset-1",
                "consumer_id": "BPNL000000000001",
                "provider_id": "BPNL000000000002",
                "policy": {},
            },
            f"{EDC_URL}/api/v1/edc/negotiations",
            {"id": "neg-1", "state": "INITIAL"},
        ),
        (
            "POST",
            "/api/v1/edc/negotiations/neg-1/request",
            {},
            f"{EDC_URL}/api/v1/edc/negotiations/neg-1/request",
            {"id": "neg-1", "state": "REQUESTING"},
        ),
        (
            "GET",
            "/api/v1/leaderboard?limit=5&offset=2",
            None,
            f"{GAMIFICATION_URL}/api/v1/leaderboard",
            {"items": [{"user_id": "u-1", "total_points": 100, "level": 2}]},
        ),
        (
            "POST",
            "/api/v1/annotations",
            {"story_id": 1, "annotation_type": "comment", "content": "Looks good"},
            f"{COLLABORATION_URL}/api/v1/annotations",
            {"id": "a-1", "content": "Looks good"},
        ),
        (
            "POST",
            "/api/v1/gap_reports",
            {"story_id": 1, "description": "Missing disposal guidance"},
            f"{COLLABORATION_URL}/api/v1/gap_reports",
            {"id": "g-1", "description": "Missing disposal guidance"},
        ),
    ],
)
def test_v1_compat_routes_proxy_to_upstream(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    path: str,
    body: dict[str, Any] | None,
    expected_url: str,
    upstream_payload: dict[str, Any],
):
    calls: list[dict[str, Any]] = []

    def fake_request(
        method: str,
        url: str,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
        **kwargs: Any,
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    request_kwargs: dict[str, Any] = {"headers": HEADERS}
    if body is not None:
        request_kwargs["json"] = body

    response = client.request(method, path, **request_kwargs)
    assert response.status_code == 200
    assert response.json() == upstream_payload
    assert calls, "Expected compatibility endpoint to call upstream service"
    assert calls[0]["method"] == method
    assert calls[0]["url"] == expected_url


def test_v1_aas_validate_requires_regulator_or_admin():
    response = client.post(
        "/api/v1/aas/validate",
        json={"templates": ["DigitalNameplate"], "data": {}},
        headers={"X-Dev-User": "viewer", "X-Dev-Roles": "consumer"},
    )
    assert response.status_code == 403


@pytest.mark.parametrize(
    "upstream_status,upstream_payload,expected_detail",
    [
        (422, {"detail": "Invalid payload"}, "Invalid payload"),
        (409, {"error": "Conflict state transition"}, "Conflict state transition"),
        (503, {"message": "service unavailable"}, {"message": "service unavailable"}),
    ],
)
def test_v1_compat_passthrough_upstream_errors(
    monkeypatch: pytest.MonkeyPatch,
    upstream_status: int,
    upstream_payload: dict[str, Any],
    expected_detail: str | dict[str, Any],
):
    def fake_request(
        method: str,
        url: str,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
        **kwargs: Any,
    ):
        return DummyResponse(upstream_payload, status_code=upstream_status)

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.post(
        "/api/v1/compliance/check",
        json={"data": {"product_name": "Battery"}, "regulations": ["ESPR"]},
        headers=HEADERS,
    )

    assert response.status_code == upstream_status
    assert response.json()["detail"] == expected_detail


def test_v1_compat_returns_502_when_upstream_unavailable(
    monkeypatch: pytest.MonkeyPatch,
):
    def fake_request(
        method: str,
        url: str,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
        **kwargs: Any,
    ):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.get("/api/v1/stories", headers=HEADERS)
    assert response.status_code == 502
    assert "Upstream unavailable" in response.json()["detail"]


def test_v1_create_shell_maps_legacy_payload_to_aas_adapter(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[dict[str, Any]] = []

    def fake_request(
        method: str,
        url: str,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
        **kwargs: Any,
    ):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(
            {"status": "created", "shell": {"id": "urn:uuid:us-02-01"}}
        )

    monkeypatch.setattr("app.core.proxy.pooled_request", fake_request)

    response = client.post(
        "/api/v1/aas/shells",
        json={
            "id": "urn:uuid:us-02-01",
            "idShort": "DPP-Create",
            "assetInformation": {"globalAssetId": "urn:example:asset:us-02-01"},
        },
        headers=HEADERS,
    )

    assert response.status_code == 200
    assert calls
    assert calls[0]["url"] == f"{AAS_ADAPTER_URL}/api/v2/aas/shells"
    assert calls[0]["json"] == {
        "aas_identifier": "urn:uuid:us-02-01",
        "product_name": "DPP-Create",
        "product_identifier": "urn:example:asset:us-02-01",
    }
