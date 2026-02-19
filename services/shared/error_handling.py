from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "") or request.headers.get("x-request-id") or "")


def _response(status_code: int, request_id: str, payload: dict) -> JSONResponse:
    response = JSONResponse(status_code=status_code, content=payload)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        req_id = _request_id(request)
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        payload = {
            "code": f"http_{exc.status_code}",
            "message": message,
            "details": exc.detail,
            "request_id": req_id or None,
            # Compatibility field retained for existing clients/tests.
            "detail": exc.detail,
        }
        return _response(exc.status_code, req_id, payload)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = _request_id(request)
        detail = exc.errors()
        payload = {
            "code": "validation_error",
            "message": "Validation error",
            "details": detail,
            "request_id": req_id or None,
            "detail": detail,
        }
        return _response(422, req_id, payload)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        req_id = _request_id(request)
        payload = {
            "code": "internal_error",
            "message": "Internal server error",
            "details": str(exc),
            "request_id": req_id or None,
            "detail": "Internal server error",
        }
        return _response(500, req_id, payload)
