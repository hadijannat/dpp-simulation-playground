from __future__ import annotations

from typing import Any

import requests
from fastapi import HTTPException, Request

from ..config import ALLOW_DEV_HEADERS


TRACE_HEADERS = ("traceparent", "tracestate", "baggage")


def _forward_context_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    if request_id:
        headers["X-Request-ID"] = str(request_id)
    idempotency_key = request.headers.get("idempotency-key")
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    for header in TRACE_HEADERS:
        value = request.headers.get(header)
        if value:
            headers[header] = value
    return headers


def _forward_headers(request: Request) -> dict[str, str]:
    headers = _forward_context_headers(request)
    auth = request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
        return headers

    if not ALLOW_DEV_HEADERS:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    user = getattr(request.state, "user", {}) or {}
    subject = user.get("preferred_username") or user.get("sub") or "platform-api-user"
    roles = user.get("realm_access", {}).get("roles", []) if isinstance(user, dict) else []
    headers["X-Dev-User"] = str(subject)
    if roles:
        headers["X-Dev-Roles"] = ",".join(str(role) for role in roles)
    return headers


def request_json(
    request: Request,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: int = 8,
) -> dict[str, Any]:
    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            headers=_forward_headers(request),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream unavailable: {exc}") from exc

    payload: Any = {}
    if response.content:
        try:
            payload = response.json()
        except ValueError:
            payload = {"detail": response.text}

    if not response.ok:
        if isinstance(payload, dict):
            detail = payload.get("detail") or payload.get("error") or payload
        else:
            detail = payload or "Upstream request failed"
        raise HTTPException(status_code=response.status_code, detail=detail)

    if isinstance(payload, dict):
        return payload
    return {"items": payload}
