from __future__ import annotations

from fastapi import Request

from .api.router import api_router
from .auth import verify_request
from services.shared.app_factory import create_service_app


def _verify_request(request: Request):
    return verify_request(request)


app = create_service_app(
    title="Compliance Service",
    version="0.1.0",
    router=api_router,
    service_name="compliance-service",
    verify_request=_verify_request,
)
