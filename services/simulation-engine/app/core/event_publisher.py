from typing import Dict, Any
import json
from ..config import REDIS_URL
from redis import Redis


def publish_event(stream: str, payload: Dict[str, Any]) -> None:
    client = Redis.from_url(REDIS_URL)
    normalized = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bytes)):
            normalized[key] = value
        else:
            normalized[key] = json.dumps(value)
    client.xadd(stream, normalized)
