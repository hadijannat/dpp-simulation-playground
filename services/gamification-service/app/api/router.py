from fastapi import APIRouter
from .v1 import points, achievements, leaderboard, streaks, health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1")
api_router.include_router(points.router, prefix="/api/v1")
api_router.include_router(achievements.router, prefix="/api/v1")
api_router.include_router(leaderboard.router, prefix="/api/v1")
api_router.include_router(streaks.router, prefix="/api/v1")
