from __future__ import annotations

from typing import Any

import requests
from fastapi import HTTPException, Request


def _forward_headers(request: Request) -> dict[str, str]:
    auth = request.headers.get("authorization")
    if auth:
        return {"Authorization": auth}

    user = getattr(request.state, "user", {}) or {}
    subject = user.get("preferred_username") or user.get("sub") or "platform-api-user"
    roles = user.get("realm_access", {}).get("roles", []) if isinstance(user, dict) else []
    headers = {"X-Dev-User": str(subject)}
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
