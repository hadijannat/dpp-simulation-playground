import json
from typing import Dict, Any
from redis import Redis
from .config import REDIS_URL


_client = Redis.from_url(REDIS_URL)


def save_item(key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    _client.set(key, json.dumps(payload))
    return payload


def load_item(key: str) -> Dict[str, Any] | None:
    raw = _client.get(key)
    if not raw:
        return None
    return json.loads(raw)
