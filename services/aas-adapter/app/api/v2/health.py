from __future__ import annotations

import requests
from fastapi import APIRouter, HTTPException

from ...config import BASYX_BASE_URL

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
        response = requests.get(BASYX_BASE_URL, timeout=1.5)
        checks["basyx"] = response.status_code < 500
    except Exception:
        checks["basyx"] = False
    if not all(checks.values()):
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "service": "aas-adapter", "checks": checks}
