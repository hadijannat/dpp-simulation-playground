from fastapi.testclient import TestClient
from app import main


def _set_roles(roles):
    def _verify(request):
        request.state.user = {"realm_access": {"roles": roles}}
    return _verify


def test_edc_denies_consumer(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["consumer"]))
    client = TestClient(main.app)
    resp = client.post("/api/v1/edc/negotiations", json={"consumer_id": "c", "provider_id": "p", "asset_id": "a", "policy": {}})
    assert resp.status_code == 403


def test_edc_allows_developer(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["developer"]))
    client = TestClient(main.app)
    resp = client.post("/api/v1/edc/negotiations", json={"consumer_id": "c", "provider_id": "p", "asset_id": "a", "policy": {}})
    assert resp.status_code == 200
