from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app import main


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
    def content(self) -> bytes:
        import json

        return json.dumps(self._payload).encode()

    def json(self) -> Any:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"status {self.status_code}")


def test_get_submodel_elements_maps_payload(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["developer"]))
    calls: list[dict[str, Any]] = []

    def fake_request(
        *,
        method: str,
        url: str,
        json: Any = None,
        timeout: int = 8,
        session_name: str | None = None,
    ):
        calls.append(
            {
                "method": method,
                "url": url,
                "json": json,
                "timeout": timeout,
                "session_name": session_name,
            }
        )
        return DummyResponse(
            {"submodelElements": [{"idShort": "batteryType", "value": "Li-Ion"}]}
        )

    monkeypatch.setattr("app.api.v2.aas.pooled_request", fake_request)

    client = TestClient(main.app)
    response = client.get("/api/v2/aas/submodels/submodel-1/elements")
    assert response.status_code == 200
    assert response.json()["submodel_id"] == "submodel-1"
    assert response.json()["items"] == [{"idShort": "batteryType", "value": "Li-Ion"}]
    assert calls
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"].endswith("/submodels/submodel-1/submodel-elements")


def test_patch_submodel_elements_passes_elements(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["manufacturer"]))
    calls: list[dict[str, Any]] = []

    def fake_request(
        *,
        method: str,
        url: str,
        json: Any = None,
        timeout: int = 8,
        session_name: str | None = None,
    ):
        calls.append(
            {
                "method": method,
                "url": url,
                "json": json,
                "timeout": timeout,
                "session_name": session_name,
            }
        )
        return DummyResponse([{"idShort": "batteryType", "value": "NMC"}])

    monkeypatch.setattr("app.api.v2.aas.pooled_request", fake_request)

    client = TestClient(main.app)
    response = client.patch(
        "/api/v2/aas/submodels/submodel-1/elements",
        json={"elements": [{"idShort": "batteryType", "value": "NMC"}]},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "updated"
    assert calls
    assert calls[0]["method"] in {"PATCH", "PUT"}
    assert calls[0]["json"] == [{"idShort": "batteryType", "value": "NMC"}]
