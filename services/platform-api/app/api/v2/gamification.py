from __future__ import annotations

from fastapi import APIRouter, Request

from ...auth import require_roles
from ...config import GAMIFICATION_URL
from ...core.proxy import request_json
from ...schemas.v2 import AchievementListResponse, LeaderboardResponse, StreakResponse

router = APIRouter()


@router.get("/gamification/achievements", response_model=AchievementListResponse)
def list_achievements(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    payload = request_json(request, "GET", f"{GAMIFICATION_URL}/api/v1/achievements")
    return {"items": payload.get("items", [])}


@router.get("/gamification/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(request: Request, limit: int = 10, offset: int = 0):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    payload = request_json(
        request,
        "GET",
        f"{GAMIFICATION_URL}/api/v1/leaderboard",
        params={"limit": limit, "offset": offset},
    )
    return {"items": payload.get("items", [])}


@router.get("/gamification/streaks", response_model=StreakResponse)
def get_streaks(request: Request):
    require_roles(request.state.user, ["manufacturer", "developer", "admin", "regulator", "consumer", "recycler"])
    payload = request_json(request, "GET", f"{GAMIFICATION_URL}/api/v1/streaks")
    return {"items": payload.get("items", [])}
