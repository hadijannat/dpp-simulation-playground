from fastapi import APIRouter
from ...schemas.aas_schema import AasCreate

router = APIRouter()

@router.post("/aas/shells")
def create_shell(payload: AasCreate):
    return {"status": "created", "aas_identifier": payload.aas_identifier}

@router.get("/aas/shells")
def list_shells():
    return {"items": []}

@router.post("/aas/validate")
def validate_aas():
    return {"status": "ok"}
