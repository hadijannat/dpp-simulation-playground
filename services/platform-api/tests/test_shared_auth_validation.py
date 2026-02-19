from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from services.shared import auth


def _request_with_bearer() -> SimpleNamespace:
    return SimpleNamespace(headers={"authorization": "Bearer token"}, state=SimpleNamespace())


def test_verify_request_rejects_missing_required_audience(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("REQUIRE_TOKEN_AUDIENCE", "true")
    monkeypatch.delenv("KEYCLOAK_AUDIENCES", raising=False)
    monkeypatch.delenv("KEYCLOAK_AUDIENCE", raising=False)
    monkeypatch.setattr(auth, "_bypass_enabled", lambda: False)
    monkeypatch.setattr(auth, "_get_jwks", lambda: [{"kid": "kid-1"}])
    monkeypatch.setattr(auth.jwt, "get_unverified_header", lambda token: {"kid": "kid-1"})
    monkeypatch.setattr(
        auth.jwt,
        "decode",
        lambda *args, **kwargs: {
            "sub": "u-1",
            "iss": "http://keycloak:8080/realms/dpp",
            "realm_access": {"roles": ["developer"]},
        },
    )

    with pytest.raises(HTTPException) as exc_info:
        auth.verify_request(_request_with_bearer())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing token audience"


def test_verify_request_rejects_audience_mismatch(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("REQUIRE_TOKEN_AUDIENCE", "true")
    monkeypatch.setenv("KEYCLOAK_AUDIENCES", "dpp-platform")
    monkeypatch.setattr(auth, "_bypass_enabled", lambda: False)
    monkeypatch.setattr(auth, "_get_jwks", lambda: [{"kid": "kid-1"}])
    monkeypatch.setattr(auth.jwt, "get_unverified_header", lambda token: {"kid": "kid-1"})
    monkeypatch.setattr(
        auth.jwt,
        "decode",
        lambda *args, **kwargs: {
            "sub": "u-1",
            "iss": "http://keycloak:8080/realms/dpp",
            "aud": "other-service",
            "realm_access": {"roles": ["developer"]},
        },
    )

    with pytest.raises(HTTPException) as exc_info:
        auth.verify_request(_request_with_bearer())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token audience"


def test_verify_request_applies_clock_skew_leeway(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {}

    monkeypatch.setenv("REQUIRE_TOKEN_AUDIENCE", "true")
    monkeypatch.setenv("KEYCLOAK_AUDIENCES", "dpp-platform")
    monkeypatch.setenv("JWT_CLOCK_SKEW_SECONDS", "90")
    monkeypatch.setattr(auth, "_bypass_enabled", lambda: False)
    monkeypatch.setattr(auth, "_get_jwks", lambda: [{"kid": "kid-1"}])
    monkeypatch.setattr(auth.jwt, "get_unverified_header", lambda token: {"kid": "kid-1"})

    def _decode(*args, **kwargs):
        captured["options"] = kwargs.get("options")
        return {
            "sub": "u-1",
            "iss": "http://keycloak:8080/realms/dpp",
            "aud": "dpp-platform",
            "realm_access": {"roles": ["developer"]},
        }

    monkeypatch.setattr(auth.jwt, "decode", _decode)
    request = _request_with_bearer()
    payload = auth.verify_request(request)

    assert payload["sub"] == "u-1"
    assert captured["options"] == {"verify_aud": False, "leeway": 90}
    assert request.state.user["aud"] == "dpp-platform"
