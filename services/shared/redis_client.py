from __future__ import annotations

import time
import redis


def get_redis(url: str) -> redis.Redis:
    return redis.from_url(url)


def ensure_stream_group(client: redis.Redis, stream: str, group: str) -> None:
    try:
        client.xgroup_create(stream, group, id="0-0", mkstream=True)
    except Exception:
        return


def xadd_with_retry(client: redis.Redis, stream: str, payload: dict, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            return client.xadd(stream, payload)
        except Exception:
            time.sleep(min(2 ** attempt, 4))
    return None
