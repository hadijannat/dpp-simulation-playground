from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "service": "collaboration-service"}


@router.get("/health/{service_name}")
def health_named(service_name: str):
    return {"status": "ok", "service": service_name}
