from fastapi import APIRouter

from .v2 import health, aas

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v2")
api_router.include_router(aas.router, prefix="/api/v2")
