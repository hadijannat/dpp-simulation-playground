from fastapi import APIRouter, Request
from ...auth import require_roles

router = APIRouter()

@router.get("/progress")
def get_progress(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    return {"progress": []}
