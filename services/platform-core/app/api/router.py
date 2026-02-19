from fastapi import APIRouter

from .v2 import health, simulation, compliance, gamification, collaboration, journeys, digital_twins, feedback, events

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v2")
api_router.include_router(simulation.router, prefix="/api/v2")
api_router.include_router(compliance.router, prefix="/api/v2")
api_router.include_router(gamification.router, prefix="/api/v2")
api_router.include_router(collaboration.router, prefix="/api/v2")
api_router.include_router(journeys.router, prefix="/api/v2")
api_router.include_router(digital_twins.router, prefix="/api/v2")
api_router.include_router(feedback.router, prefix="/api/v2")
api_router.include_router(events.router, prefix="/api/v2")
