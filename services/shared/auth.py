import os
import time
from typing import Iterable, List
import requests
from jose import jwt
from fastapi import HTTPException, Request

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "dpp")
JWKS_URL = os.getenv(
    "KEYCLOAK_JWKS_URL",
    f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs",
)
DEV_BYPASS_AUTH = os.getenv("DEV_BYPASS_AUTH", "false").lower() in ("1", "true", "yes")

_cache = {"keys": None, "fetched": 0}


def _build_default_issuers() -> List[str]:
    base = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
    return list(
        {
            base,
            f"http://localhost:8080/realms/{KEYCLOAK_REALM}",
            f"http://keycloak:8080/realms/{KEYCLOAK_REALM}",
        }
    )


def _allowed_issuers() -> List[str]:
    override = os.getenv("KEYCLOAK_ISSUERS")
    if override:
        return [item.strip() for item in override.split(",") if item.strip()]
    return _build_default_issuers()


def _get_jwks():
    now = time.time()
    if _cache["keys"] and now - _cache["fetched"] < 3600:
        return _cache["keys"]
    resp = requests.get(JWKS_URL, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    _cache["keys"] = data.get("keys", [])
    _cache["fetched"] = now
    return _cache["keys"]


def _parse_roles(value: str | None) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _dev_bypass(request: Request) -> dict | None:
    if not DEV_BYPASS_AUTH:
        return None
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return None
    user = request.headers.get("x-dev-user") or "dev-user"
    roles = _parse_roles(request.headers.get("x-dev-roles")) or ["developer"]
    payload = {
        "sub": user,
        "preferred_username": user,
        "iss": "dev-bypass",
        "realm_access": {"roles": roles},
    }
    request.state.user = payload
    return payload


def _pick_key(keys: Iterable[dict], kid: str | None) -> dict | None:
    if not kid:
        return None
    return next((k for k in keys if k.get("kid") == kid), None)


def verify_request(request: Request) -> dict:
    dev_payload = _dev_bypass(request)
    if dev_payload:
        return dev_payload

    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth.split(" ", 1)[1]
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    keys = _get_jwks()
    key = _pick_key(keys, kid)
    if not key:
        _cache["keys"] = None
        keys = _get_jwks()
        key = _pick_key(keys, kid)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid token key")
    payload = jwt.decode(token, key, algorithms=["RS256"], options={"verify_aud": False})
    issuer = payload.get("iss")
    if issuer not in _allowed_issuers():
        raise HTTPException(status_code=401, detail="Invalid token issuer")
    request.state.user = payload
    return payload


def require_roles(user: dict, roles: list[str]) -> None:
    realm_roles = user.get("realm_access", {}).get("roles", [])
    if not any(role in realm_roles for role in roles):
        raise HTTPException(status_code=403, detail="Insufficient role")
