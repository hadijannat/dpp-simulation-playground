from __future__ import annotations

import logging
from typing import Any, Callable
from uuid import uuid4

from fastapi import FastAPI, Request

from .error_handling import install_error_handlers

AuthVerifier = Callable[[Request], Any]

logger = logging.getLogger(__name__)


def _is_probe_request(path: str, probe_paths: tuple[str, ...]) -> bool:
    return any(path.endswith(candidate) for candidate in probe_paths)


def create_service_app(
    *,
    title: str,
    version: str,
    router: Any,
    service_name: str,
    verify_request: AuthVerifier | None = None,
    enable_tracing: bool = True,
    probe_paths: tuple[str, ...] = ("/health", "/ready"),
) -> FastAPI:
    app = FastAPI(title=title, version=version)
    install_error_handlers(app)

    if enable_tracing:
        try:
            from .tracing import instrument_app, instrument_requests_client

            instrument_app(app, service_name=service_name)
            instrument_requests_client(service_name=service_name)
        except Exception:
            logger.debug("Tracing setup unavailable", exc_info=True)

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id") or str(uuid4())
        is_probe = _is_probe_request(request.url.path, probe_paths)

        if verify_request and request.method != "OPTIONS" and not is_probe:
            verify_request(request)

        response = await call_next(request)
        response.headers["X-Request-ID"] = str(request.state.request_id)
        return response

    app.include_router(router)
    return app
