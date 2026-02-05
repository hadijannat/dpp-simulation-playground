from fastapi.testclient import TestClient
from app import main


def _set_roles(roles):
    def _verify(request):
        request.state.user = {"realm_access": {"roles": roles}}
    return _verify


def test_annotations_denied(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["consumer"]))
    client = TestClient(main.app)
    resp = client.get("/api/v1/annotations")
    assert resp.status_code == 403


def test_annotations_allowed(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["regulator"]))
    client = TestClient(main.app)
    resp = client.get("/api/v1/annotations")
    assert resp.status_code == 200
