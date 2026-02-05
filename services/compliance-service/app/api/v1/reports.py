from fastapi import APIRouter, Request
from ...auth import require_roles

router = APIRouter()

@router.get("/reports")
def list_reports(request: Request):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    return {"reports": []}
