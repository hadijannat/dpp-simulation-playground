from typing import Dict, Any
import requests
from sqlalchemy.orm import Session
from ..config import COMPLIANCE_URL, EDC_URL, BASYX_BASE_URL
from .service_token import get_service_token
from ..aas.basyx_client import BasyxClient
from ..models.dpp_instance import DppInstance
from uuid import uuid4


def execute_step(
    db: Session,
    action: str,
    params: Dict[str, Any],
    payload: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    token = get_service_token()
    headers = {"Authorization": f"Bearer {token}"}
    if action == "user.input":
        return {"status": "awaiting_input", "prompt": params.get("prompt")}
    if action == "compliance.check":
        regulations = payload.get("regulations") or params.get("regulations") or []
        data = payload.get("data") if isinstance(payload, dict) else payload
        body = {
            "data": data,
            "regulations": regulations,
            "session_id": context.get("session_id"),
            "story_code": context.get("story_code"),
        }
        try:
            resp = requests.post(
                f"{COMPLIANCE_URL}/api/v1/compliance/check",
                json=body,
                headers=headers,
                timeout=8,
            )
            resp.raise_for_status()
            return {"status": "ok", "data": resp.json()}
        except requests.RequestException as exc:
            return {"status": "error", "error": str(exc)}
    if action == "edc.negotiate":
        try:
            resp = requests.post(
                f"{EDC_URL}/api/v1/edc/negotiations",
                json=payload,
                headers=headers,
                timeout=8,
            )
            resp.raise_for_status()
            return {"status": "ok", "data": resp.json()}
        except requests.RequestException as exc:
            return {"status": "error", "error": str(exc)}
    if action == "aas.create":
        client = BasyxClient(base_url=BASYX_BASE_URL)
        try:
            shell = client.create_shell(payload)
        except requests.RequestException as exc:
            return {"status": "error", "error": str(exc)}
        dpp = DppInstance(
            id=uuid4(),
            session_id=context.get("session_id"),
            aas_identifier=payload.get("id") or payload.get("aas_identifier"),
            product_identifier=payload.get("product_identifier"),
            product_name=payload.get("product_name"),
            product_category=payload.get("product_category"),
            compliance_status={},
        )
        db.add(dpp)
        db.commit()
        return {"status": "created", "data": shell}
    if action == "aas.update":
        return {"status": "updated", "data": payload}
    if action == "api.call":
        return {"status": "called", "data": payload}
    return {"status": "unknown_action", "action": action}
