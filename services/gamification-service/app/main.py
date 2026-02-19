from __future__ import annotations

from fastapi import Request

from .api.router import api_router
from .auth import verify_request
from .core.db import SessionLocal
from .engine.achievement_engine import ensure_achievements
from .engine.event_consumer import start_consumer
from .engine.point_rule_engine import ensure_point_rules
from services.shared.app_factory import create_service_app


def _verify_request(request: Request):
    return verify_request(request)


app = create_service_app(
    title="Gamification Service",
    version="0.1.0",
    router=api_router,
    service_name="gamification-service",
    verify_request=_verify_request,
)


@app.on_event("startup")
def start_stream_consumer():
    db = SessionLocal()
    try:
        ensure_achievements(db)
        ensure_point_rules(db)
    finally:
        db.close()
    start_consumer()
