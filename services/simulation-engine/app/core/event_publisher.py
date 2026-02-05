from typing import Dict, Any
from ..config import REDIS_URL
from redis import Redis


def publish_event(stream: str, payload: Dict[str, Any]) -> None:
    client = Redis.from_url(REDIS_URL)
    client.xadd(stream, payload)
