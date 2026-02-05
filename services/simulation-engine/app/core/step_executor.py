from typing import Dict, Any
import requests
from sqlalchemy.orm import Session
from ..config import COMPLIANCE_URL, EDC_URL, BASYX_BASE_URL, BASYX_API_PREFIX
from .service_token import get_service_token
from ..aas.basyx_client import BasyxClient
from ..models.dpp_instance import DppInstance
from ..models.session import SimulationSession
from .aasx_storage import store_aasx_payload
from datetime import datetime, timezone
from uuid import uuid4


def _default_payload(payload: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    if payload:
        return payload
    if not params:
        return {}
    if params.get("payload") is not None:
        return params.get("payload") or {}
    return params


def execute_step(
    db: Session,
    action: str,
    params: Dict[str, Any],
    payload: Dict[str, Any],
    context: Dict[str, Any],
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    token = get_service_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if action == "user.input":
        return {"status": "awaiting_input", "prompt": params.get("prompt")}
    if action == "compliance.check":
        regulations = payload.get("regulations") or params.get("regulations") or []
        data = payload.get("data") if isinstance(payload, dict) else payload
        if not data:
            data = params.get("data")
        body = {
            "data": data,
            "regulations": regulations,
            "user_id": context.get("user_id"),
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
        payload = _default_payload(payload, params)
        if isinstance(payload, dict) and context.get("session_id") and not payload.get("session_id"):
            payload["session_id"] = context.get("session_id")
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
    if action == "edc.transfer":
        payload = _default_payload(payload, params)
        if isinstance(payload, dict) and context.get("session_id") and not payload.get("session_id"):
            payload["session_id"] = context.get("session_id")
        try:
            resp = requests.post(
                f"{EDC_URL}/api/v1/edc/transfers",
                json=payload,
                headers=headers,
                timeout=8,
            )
            resp.raise_for_status()
            return {"status": "ok", "data": resp.json()}
        except requests.RequestException as exc:
            return {"status": "error", "error": str(exc)}
    if action == "aas.create":
        payload = _default_payload(payload, params)
        client = BasyxClient(base_url=BASYX_BASE_URL, api_prefix=BASYX_API_PREFIX)
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
        try:
            db.add(dpp)
            db.commit()
        except Exception:
            db.rollback()
        return {"status": "created", "data": shell}
    if action == "aas.submodel.add":
        payload = _default_payload(payload, params)
        if not isinstance(payload, dict):
            return {"status": "error", "error": "Payload must be object"}
        submodel = payload.get("submodel") or payload
        client = BasyxClient(base_url=BASYX_BASE_URL, api_prefix=BASYX_API_PREFIX)
        try:
            created = client.create_submodel(submodel)
        except requests.RequestException as exc:
            return {"status": "error", "error": str(exc)}
        return {"status": "created", "data": created}
    if action == "aas.submodel.patch":
        payload = _default_payload(payload, params)
        if not isinstance(payload, dict):
            return {"status": "error", "error": "Payload must be object"}
        submodel_id = payload.get("submodel_id")
        elements = payload.get("elements")
        if not submodel_id or elements is None:
            return {"status": "error", "error": "Missing submodel_id or elements"}
        client = BasyxClient(base_url=BASYX_BASE_URL, api_prefix=BASYX_API_PREFIX)
        try:
            updated = client.patch_submodel_elements(submodel_id, elements)
        except requests.RequestException as exc:
            return {"status": "error", "error": str(exc)}
        return {"status": "updated", "data": updated}
    if action == "aas.update":
        payload = _default_payload(payload, params)
        update_name = None
        if isinstance(payload, dict):
            update_name = payload.get("update")
        if update_name and context.get("session_id"):
            session = db.query(SimulationSession).filter(SimulationSession.id == context.get("session_id")).first()
            if session:
                current_state = session.session_state or {}
                updates = current_state.get("aas_updates", [])
                updates.append(
                    {
                        "update": update_name,
                        "payload": payload,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                session.session_state = {**current_state, "aas_updates": updates}
                try:
                    db.commit()
                except Exception:
                    db.rollback()
        return {"status": "updated", "data": payload}
    if action == "aasx.upload":
        payload = _default_payload(payload, params)
        if not isinstance(payload, dict):
            return {"status": "error", "error": "Payload must be object"}
        filename = payload.get("filename") or "dpp.aasx"
        content = payload.get("content_base64") or payload.get("content")
        if not content:
            return {"status": "error", "error": "Missing content"}
        stored = store_aasx_payload(
            db=db,
            session_id=context.get("session_id"),
            filename=filename,
            content_base64=content,
            metadata=metadata or {},
        )
        return {"status": "stored", "data": stored}
    if action == "api.call":
        payload = _default_payload(payload, params)
        return {"status": "called", "data": payload}
    return {"status": "unknown_action", "action": action}
