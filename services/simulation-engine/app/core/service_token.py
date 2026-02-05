import os
import time
import requests

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "dpp")
CLIENT_ID = os.getenv("SERVICE_CLIENT_ID", "dpp-services")
CLIENT_SECRET = os.getenv("SERVICE_CLIENT_SECRET", "dev-services-secret")
TOKEN_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"

_cache = {"token": None, "exp": 0}


def get_service_token() -> str | None:
    now = int(time.time())
    if _cache["token"] and now < _cache["exp"] - 30:
        return _cache["token"]
    try:
        resp = requests.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token")
        expires_in = int(data.get("expires_in", 60))
        _cache["token"] = token
        _cache["exp"] = now + expires_in
        return token
    except Exception:
        return None
