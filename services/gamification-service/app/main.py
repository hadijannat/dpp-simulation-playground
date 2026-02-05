from fastapi import FastAPI, Request
from .api.router import api_router
from .auth import verify_request
from .engine.event_consumer import start_consumer
from .engine.achievement_engine import ensure_achievements
from .core.db import SessionLocal

app = FastAPI(title="Gamification Service", version="0.1.0")

@app.on_event("startup")
def start_stream_consumer():
    db = SessionLocal()
    try:
        ensure_achievements(db)
    finally:
        db.close()
    start_consumer()

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.endswith("/health") or request.method == "OPTIONS":
        return await call_next(request)
    verify_request(request)
    return await call_next(request)

app.include_router(api_router)
