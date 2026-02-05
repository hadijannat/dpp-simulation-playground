from fastapi import APIRouter, Request

from ...auth import require_roles

router = APIRouter()


@router.get("/core/gamification/status")
def gamification_status(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    return {"status": "ok", "module": "gamification"}
