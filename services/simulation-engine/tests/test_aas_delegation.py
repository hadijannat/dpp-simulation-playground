from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app import main
from app.config import AAS_ADAPTER_URL


def _set_roles(roles: list[str]):
    def _verify(request):
        request.state.user = {"realm_access": {"roles": roles}}

    return _verify


class DummyResponse:
    def __init__(self, payload: Any, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def content(self) -> bytes:
        import json

        return json.dumps(self._payload).encode()

    def json(self) -> Any:
        return self._payload


def test_create_shell_delegates_to_aas_adapter(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["manufacturer"]))
    calls: list[dict[str, Any]] = []

    def fake_request(
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 8,
    ):
        calls.append({"method": method, "url": url, "json": json, "headers": headers or {}, "timeout": timeout})
        return DummyResponse({"status": "created", "shell": {"id": "urn:uuid:demo"}})

    monkeypatch.setattr("app.api.v1.aas.requests.request", fake_request)

    client = TestClient(main.app)
    response = client.post(
        "/api/v1/aas/shells",
        json={"aas_identifier": "urn:uuid:demo", "product_name": "Demo Product", "session_id": "s-1"},
        headers={"x-request-id": "req-123"},
    )
    assert response.status_code == 200
    assert response.headers["Deprecation"] == "true"
    assert calls
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == f"{AAS_ADAPTER_URL}/api/v2/aas/shells"
    assert calls[0]["headers"].get("X-Request-ID") == "req-123"
    assert response.json()["status"] == "created"


def test_get_submodel_elements_delegates_to_aas_adapter(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["developer"]))
    calls: list[dict[str, Any]] = []

    def fake_request(
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 8,
    ):
        calls.append({"method": method, "url": url, "json": json, "headers": headers or {}, "timeout": timeout})
        return DummyResponse({"submodel_id": "sub-1", "items": [{"idShort": "batteryType"}]})

    monkeypatch.setattr("app.api.v1.aas.requests.request", fake_request)

    client = TestClient(main.app)
    response = client.get("/api/v1/aas/submodels/sub-1/elements", headers={"x-request-id": "req-456"})
    assert response.status_code == 200
    assert response.headers["Deprecation"] == "true"
    assert response.json()["submodel_id"] == "sub-1"
    assert calls[0]["url"] == f"{AAS_ADAPTER_URL}/api/v2/aas/submodels/sub-1/elements"
