from fastapi import APIRouter, Request
from ...auth import require_roles

router = APIRouter()

@router.get("/participants")
def list_participants(request: Request):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator"])
    return {"items": []}
