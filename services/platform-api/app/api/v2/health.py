from __future__ import annotations

import requests
from fastapi import APIRouter, HTTPException

from ...config import (
    AAS_ADAPTER_URL,
    COLLABORATION_URL,
    COMPLIANCE_URL,
    EDC_URL,
    GAMIFICATION_URL,
    PLATFORM_CORE_URL,
    SIMULATION_URL,
)
from ...schemas.v2 import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "service": "platform-api"}


@router.get("/health/platform-api", response_model=HealthResponse)
def service_health():
    return {"status": "ok"}


def _upstream_ok(url: str) -> bool:
    for path in ("/api/v1/health", "/api/v2/health", "/health"):
        try:
            response = requests.get(f"{url}{path}", timeout=1.5)
            if response.ok:
                return True
        except Exception:
            continue
    return False


@router.get("/ready")
def ready():
    checks = {
        "simulation_engine": _upstream_ok(SIMULATION_URL),
        "compliance_service": _upstream_ok(COMPLIANCE_URL),
        "gamification_service": _upstream_ok(GAMIFICATION_URL),
        "edc_simulator": _upstream_ok(EDC_URL),
        "collaboration_service": _upstream_ok(COLLABORATION_URL),
        # v2 services
        "platform_core": _upstream_ok(PLATFORM_CORE_URL),
        "aas_adapter": _upstream_ok(AAS_ADAPTER_URL),
    }
    if not all(checks.values()):
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "service": "platform-api", "checks": checks}
