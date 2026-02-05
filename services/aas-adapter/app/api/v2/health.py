from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "aas-adapter"}


@router.get("/health/aas-adapter")
def service_health():
    return {"status": "ok"}
