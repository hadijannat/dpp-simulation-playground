from __future__ import annotations

from fastapi import Request

from .api.router import api_router
from .auth import verify_request
from .config import EVENT_STREAM_MAXLEN, REDIS_URL
from .core.db import SessionLocal
from services.shared.app_factory import create_service_app
from services.shared.outbox_worker import start_outbox_worker


def _verify_request(request: Request):
    return verify_request(request)


app = create_service_app(
    title="EDC Simulator",
    version="0.1.0",
    router=api_router,
    service_name="edc-simulator",
    verify_request=_verify_request,
)


@app.on_event("startup")
def start_event_outbox_worker():
    start_outbox_worker(
        worker_name="edc-simulator",
        session_factory=SessionLocal,
        redis_url=REDIS_URL,
        stream_maxlen=EVENT_STREAM_MAXLEN,
    )
