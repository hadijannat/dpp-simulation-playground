from fastapi import FastAPI, Request
from .api.router import api_router
from .auth import verify_request

app = FastAPI(title="Collaboration Service", version="0.1.0")

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.endswith("/health") or request.method == "OPTIONS":
        return await call_next(request)
    verify_request(request)
    return await call_next(request)

app.include_router(api_router)
