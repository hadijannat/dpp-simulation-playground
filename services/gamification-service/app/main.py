from fastapi import FastAPI, Request
from uuid import uuid4
from .api.router import api_router
from .auth import verify_request
from .engine.event_consumer import start_consumer
from .engine.achievement_engine import ensure_achievements
from .engine.point_rule_engine import ensure_point_rules
from .core.db import SessionLocal
from services.shared.error_handling import install_error_handlers

app = FastAPI(title="Gamification Service", version="0.1.0")
install_error_handlers(app)

@app.on_event("startup")
def start_stream_consumer():
    db = SessionLocal()
    try:
        ensure_achievements(db)
        ensure_point_rules(db)
    finally:
        db.close()
    start_consumer()

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id") or str(uuid4())
    is_probe = request.url.path.endswith("/health") or request.url.path.endswith("/ready")
    if not is_probe and request.method != "OPTIONS":
        verify_request(request)
    response = await call_next(request)
    response.headers["X-Request-ID"] = str(request.state.request_id)
    return response

app.include_router(api_router)
