from fastapi import APIRouter, Request
from ...auth import require_roles

router = APIRouter()

@router.get("/leaderboard")
def leaderboard(request: Request):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"])
    return {"items": []}
