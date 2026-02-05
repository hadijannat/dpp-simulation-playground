from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
import requests
from fastapi.testclient import TestClient

from app.config import COLLABORATION_URL, EDC_URL, SIMULATION_URL
from app.main import app


client = TestClient(app)

HEADERS = {
    "X-Dev-User": "v2-error-tester",
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


@pytest.mark.parametrize(
    "method,path,body,expected_url,upstream_status,upstream_payload,expected_detail",
    [
        (
            "GET",
            "/api/v2/simulation/stories",
            None,
            f"{SIMULATION_URL}/api/v1/stories",
            404,
            {"detail": "Story not found"},
            "Story not found",
        ),
        (
            "POST",
            "/api/v2/edc/negotiations/neg-1/actions/request",
            None,
            f"{EDC_URL}/api/v1/edc/negotiations/neg-1/request",
            409,
            {"error": "Invalid transition"},
            "Invalid transition",
        ),
        (
            "POST",
            "/api/v2/collaboration/annotations",
            {"annotation_type": "comment", "content": "hello"},
            f"{COLLABORATION_URL}/api/v1/annotations",
            503,
            {"message": "upstream unavailable"},
            {"message": "upstream unavailable"},
        ),
    ],
)
def test_v2_proxy_error_passthrough(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    path: str,
    body: dict[str, Any] | None,
    expected_url: str,
    upstream_status: int,
    upstream_payload: dict[str, Any],
    expected_detail: str | dict[str, Any],
):
    calls: list[dict[str, Any]] = []

    def fake_request(method: str, url: str, params: dict[str, Any] | None, json: dict[str, Any] | None, **kwargs: Any):
        calls.append({"method": method, "url": url, "params": params, "json": json})
        return DummyResponse(upstream_payload, status_code=upstream_status)

    monkeypatch.setattr("app.core.proxy.requests.request", fake_request)

    request_kwargs: dict[str, Any] = {"headers": HEADERS}
    if body is not None:
        request_kwargs["json"] = body

    response = client.request(method, path, **request_kwargs)

    assert response.status_code == upstream_status
    assert response.json()["detail"] == expected_detail
    assert calls, "Expected v2 compatibility route to call upstream service"
    assert calls[0]["method"] == method
    assert calls[0]["url"] == expected_url


def test_v2_proxy_returns_502_for_request_exception(monkeypatch: pytest.MonkeyPatch):
    def fake_request(method: str, url: str, params: dict[str, Any] | None, json: dict[str, Any] | None, **kwargs: Any):
        raise requests.RequestException("network timeout")

    monkeypatch.setattr("app.core.proxy.requests.request", fake_request)

    response = client.get("/api/v2/simulation/stories", headers=HEADERS)
    assert response.status_code == 502
    assert "Upstream unavailable" in response.json()["detail"]
