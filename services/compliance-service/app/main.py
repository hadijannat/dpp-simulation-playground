from fastapi import FastAPI
from .api.router import api_router

app = FastAPI(title="Compliance Service", version="0.1.0")
app.include_router(api_router)
