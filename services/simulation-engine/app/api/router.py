from fastapi import APIRouter
from .v1 import health, sessions, stories, steps, aas, progress

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1")
api_router.include_router(sessions.router, prefix="/api/v1")
api_router.include_router(stories.router, prefix="/api/v1")
api_router.include_router(steps.router, prefix="/api/v1")
api_router.include_router(aas.router, prefix="/api/v1")
api_router.include_router(progress.router, prefix="/api/v1")
