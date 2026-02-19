from __future__ import annotations

import logging
import os
import threading
import time

from sqlalchemy.orm import Session, sessionmaker

from .models.event_outbox import EventOutbox
from .redis_client import get_redis, publish_event
from .repositories import event_outbox_repo

logger = logging.getLogger(__name__)

_started_workers: set[str] = set()
_lock = threading.Lock()


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _enabled() -> bool:
    value = os.getenv("OUTBOX_WORKER_ENABLED", "true").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _run_loop(
    *,
    worker_name: str,
    session_factory: sessionmaker,
    redis_url: str,
    stream_maxlen: int | None,
) -> None:
    batch_size = _as_int("OUTBOX_PUBLISH_BATCH_SIZE", 50)
    interval_ms = _as_int("OUTBOX_PUBLISH_INTERVAL_MS", 1000)
    lock_timeout = _as_int("OUTBOX_LOCK_TIMEOUT_SECONDS", 60)

    client = get_redis(redis_url)

    while True:
        db: Session = session_factory()
        try:
            claimed = event_outbox_repo.claim_pending_events(
                db,
                limit=batch_size,
                lock_timeout_seconds=lock_timeout,
            )
            claimed_ids = [item.id for item in claimed]
            db.commit()

            for row_id in claimed_ids:
                row = db.query(EventOutbox).filter_by(id=row_id).first()
                if row is None:
                    continue

                ok, message_id = publish_event(
                    client,
                    row.stream,
                    row.payload if isinstance(row.payload, dict) else {},
                    maxlen=stream_maxlen,
                )
                if ok:
                    event_outbox_repo.mark_published(row, stream_message_id=message_id)
                else:
                    backoff = min(2 ** int(row.attempts or 0), 30)
                    event_outbox_repo.mark_retry(row, error="redis_publish_failed", backoff_seconds=backoff)
                db.commit()
        except Exception:
            db.rollback()
            logger.exception("Outbox worker iteration failed", extra={"worker": worker_name})
            time.sleep(max(interval_ms / 1000.0, 0.1))
        finally:
            db.close()

        time.sleep(max(interval_ms / 1000.0, 0.1))


def start_outbox_worker(
    *,
    worker_name: str,
    session_factory: sessionmaker,
    redis_url: str,
    stream_maxlen: int | None = None,
) -> None:
    if not _enabled():
        logger.info("Outbox worker disabled", extra={"worker": worker_name})
        return

    with _lock:
        if worker_name in _started_workers:
            return
        _started_workers.add(worker_name)

    thread = threading.Thread(
        target=_run_loop,
        kwargs={
            "worker_name": worker_name,
            "session_factory": session_factory,
            "redis_url": redis_url,
            "stream_maxlen": stream_maxlen,
        },
        daemon=True,
        name=f"outbox-worker-{worker_name}",
    )
    thread.start()
