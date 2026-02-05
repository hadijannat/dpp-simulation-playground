from fastapi import FastAPI, Request

from .api.router import api_router
from .auth import verify_request

app = FastAPI(title="Platform API", version="0.2.0")

try:
    from services.shared.tracing import instrument_app
    instrument_app(app, service_name="platform-api")
except ImportError:
    pass


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path.endswith("/health"):
        return await call_next(request)
    verify_request(request)
    return await call_next(request)


app.include_router(api_router)
