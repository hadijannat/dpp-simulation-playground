from fastapi.testclient import TestClient
from app import main


def _set_roles(roles):
    def _verify(request):
        request.state.user = {"realm_access": {"roles": roles}}
    return _verify


def test_aas_requires_role(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["consumer"]))
    client = TestClient(main.app)
    resp = client.post("/api/v1/aas/shells", json={"aas_identifier": "x"})
    assert resp.status_code == 403


def test_aas_allows_manufacturer(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["manufacturer"]))

    class _DummyResponse:
        status_code = 200

        @property
        def content(self):
            return b'{"status":"created","shell":{"id":"x"}}'

        @property
        def ok(self):
            return True

        def json(self):
            return {"status": "created", "shell": {"id": "x"}}

    monkeypatch.setattr("app.api.v1.aas.requests.request", lambda *args, **kwargs: _DummyResponse())
    client = TestClient(main.app)
    resp = client.post("/api/v1/aas/shells", json={"aas_identifier": "x"})
    assert resp.status_code == 200
