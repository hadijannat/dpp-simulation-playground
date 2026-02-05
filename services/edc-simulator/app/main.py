from fastapi import FastAPI
from .api.router import api_router

app = FastAPI(title="EDC Simulator", version="0.1.0")
app.include_router(api_router)
