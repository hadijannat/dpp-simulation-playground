from __future__ import annotations

from fastapi.testclient import TestClient

from app import main


def _set_roles(roles):
    def _verify(request):
        request.state.user = {"realm_access": {"roles": roles}}

    return _verify


def _base_policy():
    return {
        "permission": [
            {
                "constraint": {
                    "leftOperand": "purpose",
                    "operator": "eq",
                    "rightOperand": "analytics",
                }
            }
        ]
    }


def test_policy_evaluate_allows_when_policy_matches(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["regulator"]))
    client = TestClient(main.app)

    response = client.post(
        "/api/v1/edc/policies/evaluate",
        json={"purpose": "analytics", "policy": _base_policy()},
    )
    assert response.status_code == 200
    assert response.json() == {"allowed": True}


def test_policy_evaluate_returns_403_when_denied(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["regulator"]))
    client = TestClient(main.app)

    response = client.post(
        "/api/v1/edc/policies/evaluate",
        json={"purpose": "restricted", "policy": _base_policy()},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Policy does not allow this purpose"


def test_policy_evaluate_uses_context_for_composed_constraints(monkeypatch):
    monkeypatch.setattr(main, "verify_request", _set_roles(["regulator"]))
    client = TestClient(main.app)

    policy = {
        "permission": [
            {
                "constraint": {
                    "and": [
                        {"leftOperand": "purpose", "operator": "eq", "rightOperand": "analytics"},
                        {"leftOperand": "region", "operator": "in", "rightOperand": ["eu", "us"]},
                    ]
                }
            }
        ]
    }

    denied = client.post(
        "/api/v1/edc/policies/evaluate",
        json={"purpose": "analytics", "policy": policy, "context": {"region": "apac"}},
    )
    assert denied.status_code == 403

    allowed = client.post(
        "/api/v1/edc/policies/evaluate",
        json={"purpose": "analytics", "policy": policy, "context": {"region": "eu"}},
    )
    assert allowed.status_code == 200
    assert allowed.json() == {"allowed": True}
