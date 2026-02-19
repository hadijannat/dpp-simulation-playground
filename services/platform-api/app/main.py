from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request

from .api.router import api_router
from .auth import verify_request
from services.shared.error_handling import install_error_handlers

app = FastAPI(title="Platform API", version="0.2.0")

try:
    from services.shared.tracing import instrument_app
    instrument_app(app, service_name="platform-api")
except ImportError:
    pass

install_error_handlers(app)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id") or str(uuid4())
    is_probe = request.url.path.endswith("/health") or request.url.path.endswith("/ready")
    if request.method != "OPTIONS" and not is_probe:
        verify_request(request)
    response = await call_next(request)
    response.headers["X-Request-ID"] = str(request.state.request_id)
    return response


app.include_router(api_router)
