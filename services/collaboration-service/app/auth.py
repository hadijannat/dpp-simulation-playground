import os
import time
import requests
from jose import jwt
from fastapi import HTTPException, Request

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "dpp")
JWKS_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
ISSUER = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"

_cache = {"keys": None, "fetched": 0}


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


def verify_request(request: Request) -> None:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth.split(" ", 1)[1]
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    keys = _get_jwks()
    key = next((k for k in keys if k.get("kid") == kid), None)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid token key")
    payload = jwt.decode(token, key, algorithms=["RS256"], options={"verify_aud": False}, issuer=ISSUER)
    request.state.user = payload
