from fastapi import FastAPI
from .api.router import api_router
from services.shared.logging_config import configure_logging

app = FastAPI(title="DPP Service")
configure_logging("service")

app.include_router(api_router)
