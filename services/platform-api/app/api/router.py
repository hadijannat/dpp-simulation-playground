from fastapi import APIRouter

from .v1 import compat
from .v2 import (
    aas,
    collaboration,
    compliance,
    digital_twins,
    edc,
    feedback,
    gamification,
    health,
    journeys,
    simulation,
)

api_router = APIRouter()
api_router.include_router(compat.router, prefix="/api/v1")
api_router.include_router(health.router, prefix="/api/v2")
api_router.include_router(simulation.router, prefix="/api/v2")
api_router.include_router(aas.router, prefix="/api/v2")
api_router.include_router(journeys.router, prefix="/api/v2")
api_router.include_router(compliance.router, prefix="/api/v2")
api_router.include_router(edc.router, prefix="/api/v2")
api_router.include_router(gamification.router, prefix="/api/v2")
api_router.include_router(digital_twins.router, prefix="/api/v2")
api_router.include_router(collaboration.router, prefix="/api/v2")
api_router.include_router(feedback.router, prefix="/api/v2")
