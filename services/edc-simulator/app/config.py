import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./edc_simulator.db"


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


EVENT_STREAM_MAXLEN = _as_int("EVENT_STREAM_MAXLEN", 50000)
ASYNC_SIMULATION_DEFAULT_STEP_DELAY_MS = _as_int("ASYNC_SIMULATION_DEFAULT_STEP_DELAY_MS", 250)
ASYNC_SIMULATION_CALLBACK_TIMEOUT_SECONDS = _as_int("ASYNC_SIMULATION_CALLBACK_TIMEOUT_SECONDS", 5)
