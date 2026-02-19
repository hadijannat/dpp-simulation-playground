import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dpp:dpp@postgres:5432/dpp_playground")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


STREAM_MAXLEN = _as_int("STREAM_MAXLEN", 50000)
RETRY_STREAM_MAXLEN = _as_int("RETRY_STREAM_MAXLEN", 20000)
DLQ_STREAM_MAXLEN = _as_int("DLQ_STREAM_MAXLEN", 20000)
STREAM_TRIM_INTERVAL_SECONDS = _as_int("STREAM_TRIM_INTERVAL_SECONDS", 300)
