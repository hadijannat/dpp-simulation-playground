from fastapi import APIRouter
from .v1 import annotations, gap_reports, votes, comments, health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1")
api_router.include_router(annotations.router, prefix="/api/v1")
api_router.include_router(gap_reports.router, prefix="/api/v1")
api_router.include_router(votes.router, prefix="/api/v1")
api_router.include_router(comments.router, prefix="/api/v1")
