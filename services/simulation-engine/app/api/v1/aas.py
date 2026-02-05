from fastapi import APIRouter, Request
from ...schemas.aas_schema import AasCreate
from ...auth import require_roles

router = APIRouter()

@router.post("/aas/shells")
def create_shell(request: Request, payload: AasCreate):
    require_roles(request.state.user, ["manufacturer", "developer", "admin"])
    return {"status": "created", "aas_identifier": payload.aas_identifier}

@router.get("/aas/shells")
def list_shells(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    return {"items": []}

@router.post("/aas/validate")
def validate_aas(request: Request):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    return {"status": "ok"}
