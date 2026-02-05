from fastapi import FastAPI
from .api.router import api_router
from .core.logging import configure_logging

app = FastAPI(title="Simulation Engine", version="0.1.0")
configure_logging("simulation-engine")

app.include_router(api_router)
