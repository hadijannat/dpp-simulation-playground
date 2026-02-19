from fastapi import FastAPI, Request
from uuid import uuid4
from .api.router import api_router
from .auth import verify_request
from services.shared.error_handling import install_error_handlers

app = FastAPI(title="EDC Simulator", version="0.1.0")
install_error_handlers(app)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id") or str(uuid4())
    is_probe = request.url.path.endswith("/health") or request.url.path.endswith("/ready")
    if not is_probe and request.method != "OPTIONS":
        verify_request(request)
    response = await call_next(request)
    response.headers["X-Request-ID"] = str(request.state.request_id)
    return response

app.include_router(api_router)
