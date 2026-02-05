from fastapi import APIRouter, Request
from ...engine.achievement_engine import load_achievements
from ...auth import require_roles

router = APIRouter()

@router.get("/achievements")
def list_achievements(request: Request):
    require_roles(request.state.user, ["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"])
    return {"items": load_achievements()}
