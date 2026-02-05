import json
from typing import Dict, Any
from redis import Redis
from .config import REDIS_URL


_client = Redis.from_url(REDIS_URL)
_fallback: Dict[str, Dict[str, Any]] = {}


def save_item(key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        _client.set(key, json.dumps(payload))
    except Exception:
        _fallback[key] = payload
    return payload


def load_item(key: str) -> Dict[str, Any] | None:
    try:
        raw = _client.get(key)
        if raw:
            return json.loads(raw)
    except Exception:
        return _fallback.get(key)
    return None
