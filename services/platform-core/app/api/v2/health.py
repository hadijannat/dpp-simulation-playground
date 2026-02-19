from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from ...core.db import engine

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "platform-core"}


@router.get("/health/platform-core")
def service_health():
    return {"status": "ok"}


@router.get("/ready")
def ready():
    checks = {"database": False}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
    if not all(checks.values()):
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "service": "platform-core", "checks": checks}
