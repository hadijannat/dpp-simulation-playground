from __future__ import annotations
from fastapi import APIRouter, HTTPException

from ...config import BASYX_BASE_URL
from services.shared.http_client import request as pooled_request

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "aas-adapter"}


@router.get("/health/aas-adapter")
def service_health():
    return {"status": "ok"}


@router.get("/ready")
def ready():
    checks = {"basyx": False}
    try:
        response = pooled_request(
            method="GET",
            url=BASYX_BASE_URL,
            timeout=1.5,
            session_name="aas-adapter-health",
        )
        checks["basyx"] = response.status_code < 500
    except Exception:
        checks["basyx"] = False
    if not all(checks.values()):
        raise HTTPException(
            status_code=503, detail={"status": "not_ready", "checks": checks}
        )
    return {"status": "ready", "service": "aas-adapter", "checks": checks}
