from __future__ import annotations

import time
from uuid import uuid4

from fastapi.testclient import TestClient

from app import main


def _set_roles(roles: list[str]):
    def _verify(request):
        request.state.user = {"sub": "test-user", "realm_access": {"roles": roles}}

    return _verify


def _make_client(monkeypatch, roles: list[str] | None = None) -> TestClient:
    monkeypatch.setattr(main, "verify_request", _set_roles(roles or ["developer"]))
    return TestClient(main.app)


def test_catalog_contains_rich_dataset_fields(monkeypatch):
    monkeypatch.setattr("app.api.v1.assets.resolve_user_id", lambda *_args, **_kwargs: None)
    client = _make_client(monkeypatch, ["developer"])

    participant_id = f"provider-{uuid4()}"
    asset_id = f"asset-{uuid4()}"

    participant_resp = client.post(
        "/api/v1/edc/participants",
        json={
            "participant_id": participant_id,
            "name": "Provider A",
            "metadata": {"country": "DE"},
        },
    )
    assert participant_resp.status_code == 200

    asset_resp = client.post(
        "/api/v1/edc/assets",
        json={
            "asset_id": asset_id,
            "name": "Battery Passport",
            "policy_odrl": {
                "permission": [{"action": "use"}],
                "obligation": [{"action": "notify"}],
            },
            "data_address": {
                "provider_id": participant_id,
                "endpoint": "https://provider.example/data/battery",
                "format": "application/json",
                "keywords": ["battery", "passport"],
                "description": "Passport data",
            },
        },
    )
    assert asset_resp.status_code == 200

    catalog_resp = client.get("/api/v1/edc/catalog")
    assert catalog_resp.status_code == 200
    dataset = catalog_resp.json()["dataset"]
    target = next(item for item in dataset if item["id"] == asset_id)

    assert target["type"] == "Dataset"
    assert target["@type"] == "dcat:Dataset"
    assert target["publisher"]["id"] == participant_id
    assert target["distribution"][0]["format"] == "application/json"
    assert target["policySummary"] == {"permissions": 1, "prohibitions": 0, "obligations": 1}
    assert "battery" in target["keywords"]


def test_async_negotiation_simulation_reaches_finalized(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["developer"]))
    monkeypatch.setattr("app.api.v1.negotiations.publish_event", lambda *args, **kwargs: (True, "1-0"))
    monkeypatch.setattr("app.api.v1.negotiations.get_redis", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.api.v1.negotiations.resolve_user_id", lambda *_args, **_kwargs: None)
    client = TestClient(main.app)

    negotiation_resp = client.post(
        "/api/v1/edc/negotiations",
        json={
            "consumer_id": "consumer-a",
            "provider_id": "provider-a",
            "asset_id": f"asset-{uuid4()}",
            "policy": {},
            "simulate_async": True,
            "step_delay_ms": 0,
        },
    )
    assert negotiation_resp.status_code == 200
    negotiation_id = negotiation_resp.json()["id"]

    state = negotiation_resp.json()["state"]
    for _ in range(20):
        detail_resp = client.get(f"/api/v1/edc/negotiations/{negotiation_id}")
        assert detail_resp.status_code == 200
        state = detail_resp.json()["state"]
        if state == "FINALIZED":
            break
        time.sleep(0.02)

    assert state == "FINALIZED"


def test_async_transfer_simulation_reaches_completed(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["developer"]))
    monkeypatch.setattr("app.api.v1.transfers.publish_event", lambda *args, **kwargs: (True, "1-0"))
    monkeypatch.setattr("app.api.v1.transfers.get_redis", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.api.v1.transfers.resolve_user_id", lambda *_args, **_kwargs: None)
    client = TestClient(main.app)

    transfer_resp = client.post(
        "/api/v1/edc/transfers",
        json={
            "asset_id": f"asset-{uuid4()}",
            "consumer_id": "consumer-a",
            "provider_id": "provider-a",
            "simulate_async": True,
            "step_delay_ms": 0,
        },
    )
    assert transfer_resp.status_code == 200
    transfer_id = transfer_resp.json()["id"]

    state = transfer_resp.json()["state"]
    for _ in range(20):
        detail_resp = client.get(f"/api/v1/edc/transfers/{transfer_id}")
        assert detail_resp.status_code == 200
        state = detail_resp.json()["state"]
        if state == "COMPLETED":
            break
        time.sleep(0.02)

    assert state == "COMPLETED"


def test_simulated_webhook_endpoints(monkeypatch):
    client = _make_client(monkeypatch, ["developer"])

    post_resp = client.post(
        "/api/v1/edc/webhooks/simulated",
        json={"event_type": "sample", "object_id": "obj-1", "state": "REQUESTED", "metadata": {}},
    )
    assert post_resp.status_code == 200

    list_resp = client.get("/api/v1/edc/webhooks/simulated")
    assert list_resp.status_code == 200
    assert any(item["payload"].get("event_type") == "sample" for item in list_resp.json()["items"])

    delete_resp = client.delete("/api/v1/edc/webhooks/simulated")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] >= 1
