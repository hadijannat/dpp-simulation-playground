from fastapi.testclient import TestClient
from app import main


def _set_roles(roles):
    def _verify(request):
        request.state.user = {"realm_access": {"roles": roles}}
    return _verify


def test_compliance_requires_role(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["consumer"]))
    client = TestClient(main.app)
    resp = client.post("/api/v1/compliance/check", json={"data": {"aas_identifier": "x"}, "regulations": ["ESPR"]})
    assert resp.status_code == 403


def test_compliance_allows_regulator(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["regulator"]))
    client = TestClient(main.app)
    resp = client.post("/api/v1/compliance/check", json={"data": {"aas_identifier": "x"}, "regulations": ["ESPR"]})
    assert resp.status_code == 200
