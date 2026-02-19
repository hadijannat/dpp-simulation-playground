from typing import Dict, Any
from ..config import REDIS_URL
from services.shared.redis_client import get_redis, publish_event as shared_publish_event


def publish_event(stream: str, payload: Dict[str, Any]) -> None:
    client = get_redis(REDIS_URL)
    ok, _ = shared_publish_event(client, stream, payload, retries=3)
    if not ok:
        raise RuntimeError("Failed to publish event")
