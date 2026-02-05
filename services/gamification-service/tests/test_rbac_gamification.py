from fastapi.testclient import TestClient
from app import main


def _set_roles(roles):
    def _verify(request):
        request.state.user = {"realm_access": {"roles": roles}}
    return _verify


class _Record:
    def __init__(self):
        self.user_id = "1"
        self.total_points = 1


def test_points_requires_role(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["consumer"]))
    client = TestClient(main.app)
    resp = client.post("/api/v1/points", json={"user_id": "1", "points": 1})
    assert resp.status_code == 403


def test_points_allows_developer(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["developer"]))
    monkeypatch.setattr("app.api.v1.points.add_points", lambda *_args, **_kwargs: _Record())
    client = TestClient(main.app)
    resp = client.post("/api/v1/points", json={"user_id": "1", "points": 1})
    assert resp.status_code == 200
