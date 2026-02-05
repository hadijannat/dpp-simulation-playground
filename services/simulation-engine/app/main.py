from fastapi import FastAPI, Request
from .api.router import api_router
from .core.logging import configure_logging
from .auth import verify_request

app = FastAPI(title="Simulation Engine", version="0.1.0")
configure_logging("simulation-engine")

try:
    from services.shared.tracing import instrument_app
    instrument_app(app, service_name="simulation-engine")
except ImportError:
    pass

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.endswith("/health") or request.method == "OPTIONS":
        return await call_next(request)
    verify_request(request)
    return await call_next(request)

app.include_router(api_router)
