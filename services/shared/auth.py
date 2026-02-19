import os
import time
from typing import Iterable, List
import requests
from jose import jwt
from fastapi import HTTPException, Request
from uuid import uuid4

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "dpp")
JWKS_URL = os.getenv(
    "KEYCLOAK_JWKS_URL",
    f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs",
)
DEV_BYPASS_AUTH = os.getenv("DEV_BYPASS_AUTH", "false").lower() in ("1", "true", "yes")
AUTH_MODE = os.getenv("AUTH_MODE", "auto").lower()

_cache = {"keys": None, "fetched": 0, "keycloak_ok": None, "keycloak_checked": 0}


def _as_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _clock_skew_seconds() -> int:
    raw = os.getenv("JWT_CLOCK_SKEW_SECONDS", "30").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 30


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


def _allowed_audiences() -> List[str]:
    configured = os.getenv("KEYCLOAK_AUDIENCES") or os.getenv("KEYCLOAK_AUDIENCE")
    if configured:
        return [item.strip() for item in configured.split(",") if item.strip()]
    fallback = os.getenv("KEYCLOAK_CLIENT_ID")
    if fallback:
        return [fallback]
    return []


def _require_audience_check() -> bool:
    return _as_bool(os.getenv("REQUIRE_TOKEN_AUDIENCE"), default=True)


def _keycloak_available() -> bool:
    now = time.time()
    cached = _cache.get("keycloak_ok")
    if cached is not None and now - _cache.get("keycloak_checked", 0) < 30:
        return bool(cached)
    try:
        resp = requests.get(f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}", timeout=1.5)
        ok = resp.status_code == 200
    except Exception:
        ok = False
    _cache["keycloak_ok"] = ok
    _cache["keycloak_checked"] = now
    return ok


def _bypass_enabled() -> bool:
    if DEV_BYPASS_AUTH:
        return True
    if AUTH_MODE == "bypass":
        return True
    if AUTH_MODE == "keycloak":
        return False
    if AUTH_MODE == "auto":
        return not _keycloak_available()
    return False


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
    if not _bypass_enabled():
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


def _validate_issuer(payload: dict) -> None:
    issuer = payload.get("iss")
    if issuer not in _allowed_issuers():
        raise HTTPException(status_code=401, detail="Invalid token issuer")


def _validate_audience(payload: dict) -> None:
    if not _require_audience_check():
        return

    token_audience = payload.get("aud")
    audiences: set[str] = set()
    if isinstance(token_audience, str) and token_audience.strip():
        audiences.add(token_audience.strip())
    elif isinstance(token_audience, list):
        audiences.update(str(item).strip() for item in token_audience if str(item).strip())

    if not audiences:
        raise HTTPException(status_code=401, detail="Missing token audience")

    allowed = set(_allowed_audiences())
    if allowed and audiences.isdisjoint(allowed):
        raise HTTPException(status_code=401, detail="Invalid token audience")


def verify_request(request: Request) -> dict:
    if not getattr(request.state, "request_id", None):
        request.state.request_id = request.headers.get("x-request-id") or str(uuid4())
    dev_payload = _dev_bypass(request)
    if dev_payload:
        return dev_payload

    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth.split(" ", 1)[1]
    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Malformed bearer token") from exc
    kid = header.get("kid")
    keys = _get_jwks()
    key = _pick_key(keys, kid)
    if not key:
        _cache["keys"] = None
        keys = _get_jwks()
        key = _pick_key(keys, kid)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid token key")
    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False, "leeway": _clock_skew_seconds()},
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid bearer token") from exc

    _validate_issuer(payload)
    _validate_audience(payload)
    request.state.user = payload
    return payload


def require_roles(user: dict, roles: list[str]) -> None:
    realm_roles = user.get("realm_access", {}).get("roles", [])
    if not any(role in realm_roles for role in roles):
        raise HTTPException(status_code=403, detail="Insufficient role")
