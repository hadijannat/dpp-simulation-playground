from fastapi import APIRouter, HTTPException
from redis import Redis
from sqlalchemy import text

from ...config import REDIS_URL
from ...core.db import engine

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "service": "simulation-engine"}


@router.get("/health/{service_name}")
def health_named(service_name: str):
    return {"status": "ok", "service": service_name}


@router.get("/ready")
def ready():
    checks = {"database": False, "redis": False}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
    try:
        checks["redis"] = bool(Redis.from_url(REDIS_URL).ping())
    except Exception:
        checks["redis"] = False
    if not all(checks.values()):
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "service": "simulation-engine", "checks": checks}
