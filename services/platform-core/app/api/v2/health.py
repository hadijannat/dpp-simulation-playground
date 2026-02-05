from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "platform-core"}


@router.get("/health/platform-core")
def service_health():
    return {"status": "ok"}
