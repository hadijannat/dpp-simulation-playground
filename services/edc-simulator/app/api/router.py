from fastapi import APIRouter
from .v1 import catalog, negotiations, transfers, policies, participants, health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1")
api_router.include_router(catalog.router, prefix="/api/v1/edc")
api_router.include_router(negotiations.router, prefix="/api/v1/edc")
api_router.include_router(transfers.router, prefix="/api/v1/edc")
api_router.include_router(policies.router, prefix="/api/v1/edc")
api_router.include_router(participants.router, prefix="/api/v1/edc")
