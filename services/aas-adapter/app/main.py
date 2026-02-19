from __future__ import annotations

from fastapi import Request

from .api.router import api_router
from .auth import verify_request
from services.shared.app_factory import create_service_app


def _verify_request(request: Request):
    return verify_request(request)


app = create_service_app(
    title="AAS Adapter",
    version="0.2.0",
    router=api_router,
    service_name="aas-adapter",
    verify_request=_verify_request,
)
