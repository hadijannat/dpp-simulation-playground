from fastapi import APIRouter, Request

from ...auth import require_roles

router = APIRouter()


@router.get("/core/compliance/status")
def compliance_status(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator"])
    return {"status": "ok", "module": "compliance"}
