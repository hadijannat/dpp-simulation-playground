from fastapi import APIRouter
from .v1 import compliance, rules, reports, health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1")
api_router.include_router(compliance.router, prefix="/api/v1")
api_router.include_router(rules.router, prefix="/api/v1")
api_router.include_router(reports.router, prefix="/api/v1")
