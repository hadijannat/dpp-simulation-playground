from fastapi import APIRouter

from ...schemas.v2 import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "service": "platform-api"}


@router.get("/health/platform-api", response_model=HealthResponse)
def service_health():
    return {"status": "ok"}
