from __future__ import annotations

import os

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from .api.router import api_router
from .auth import verify_request
from services.shared.app_factory import create_service_app


DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS")
    if not raw:
        return list(DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _verify_request(request: Request):
    return verify_request(request)


app = create_service_app(
    title="Platform API",
    version="0.2.0",
    router=api_router,
    service_name="platform-api",
    verify_request=_verify_request,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
