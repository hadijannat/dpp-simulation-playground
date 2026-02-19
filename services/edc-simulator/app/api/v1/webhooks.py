from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ...auth import require_roles
from ...core.webhook_store import clear_webhook_events, list_webhook_events, record_webhook_event

router = APIRouter()

ALL_ROLES = ["developer", "manufacturer", "admin", "regulator", "consumer", "recycler"]


class SimulatedWebhookPayload(BaseModel):
    source: str = "external"
    event_type: str
    object_id: str | None = None
    state: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.get("/webhooks/simulated")
def get_simulated_webhooks(request: Request, limit: int = 100):
    require_roles(request.state.user, ALL_ROLES)
    return {"items": list_webhook_events(limit=limit)}


@router.post("/webhooks/simulated")
def receive_simulated_webhook(request: Request, payload: SimulatedWebhookPayload):
    require_roles(request.state.user, ALL_ROLES)
    entry = record_webhook_event(channel="inbound", payload=payload.model_dump())
    return {"status": "accepted", "item": entry}


@router.delete("/webhooks/simulated")
def delete_simulated_webhooks(request: Request):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    deleted = clear_webhook_events()
    return {"deleted": deleted}
