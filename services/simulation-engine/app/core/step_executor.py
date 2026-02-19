from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

import requests
from sqlalchemy.orm import Session

from ..config import AAS_ADAPTER_URL, COMPLIANCE_URL, EDC_URL
from ..models.dpp_instance import DppInstance
from ..models.session import SimulationSession
from .aasx_storage import store_aasx_payload
from .service_token import get_service_token

StepHandler = Callable[
    [Session, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any] | None, dict[str, str]],
    dict[str, Any],
]


def _default_payload(payload: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    if payload:
        return payload
    if not params:
        return {}
    if params.get("payload") is not None:
        return params.get("payload") or {}
    return params


def _request_headers() -> dict[str, str]:
    token = get_service_token()
    return {"Authorization": f"Bearer {token}"} if token else {}


def _call_aas_adapter(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None,
    headers: dict[str, str],
) -> dict[str, Any]:
    response = requests.request(
        method=method,
        url=f"{AAS_ADAPTER_URL}{path}",
        json=json_body,
        headers=headers,
        timeout=8,
    )
    response.raise_for_status()
    if not response.content:
        return {}
    payload = response.json()
    return payload if isinstance(payload, dict) else {"items": payload}


def _execute_user_input(
    _db: Session,
    params: dict[str, Any],
    payload: dict[str, Any],
    _context: dict[str, Any],
    _metadata: dict[str, Any] | None,
    _headers: dict[str, str],
) -> dict[str, Any]:
    if payload:
        return {"status": "completed", "data": payload}
    return {"status": "awaiting_input", "prompt": params.get("prompt")}


def _execute_compliance_check(
    db: Session,
    params: dict[str, Any],
    payload: dict[str, Any],
    context: dict[str, Any],
    _metadata: dict[str, Any] | None,
    headers: dict[str, str],
) -> dict[str, Any]:
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
        response = requests.post(
            f"{COMPLIANCE_URL}/api/v1/compliance/check",
            json=body,
            headers=headers,
            timeout=8,
        )
        response.raise_for_status()
        result = response.json()
        # Keep digital twin compliance node in sync when a DPP exists.
        try:
            from services.shared.repositories import digital_twin_repo

            session_id = context.get("session_id")
            if session_id:
                dpp = db.query(DppInstance).filter(DppInstance.session_id == session_id).first()
                if dpp:
                    graph = digital_twin_repo.get_graph(db, dpp.id)
                    if graph:
                        for node in graph["nodes"]:
                            if node.node_key == "compliance":
                                node.payload = {"status": result.get("status", "unknown"), "result": result}
                                db.commit()
                                break
        except Exception:
            pass
        return {"status": result.get("status", "unknown"), "data": result}
    except requests.RequestException as exc:
        return {"status": "error", "error": str(exc)}


def _execute_edc_negotiation(
    _db: Session,
    params: dict[str, Any],
    payload: dict[str, Any],
    context: dict[str, Any],
    _metadata: dict[str, Any] | None,
    headers: dict[str, str],
) -> dict[str, Any]:
    outgoing = _default_payload(payload, params)
    if isinstance(outgoing, dict) and context.get("session_id") and not outgoing.get("session_id"):
        outgoing["session_id"] = context.get("session_id")
    try:
        response = requests.post(
            f"{EDC_URL}/api/v1/edc/negotiations",
            json=outgoing,
            headers=headers,
            timeout=8,
        )
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.RequestException as exc:
        return {"status": "error", "error": str(exc)}


def _execute_edc_transfer(
    _db: Session,
    params: dict[str, Any],
    payload: dict[str, Any],
    context: dict[str, Any],
    _metadata: dict[str, Any] | None,
    headers: dict[str, str],
) -> dict[str, Any]:
    outgoing = _default_payload(payload, params)
    if isinstance(outgoing, dict) and context.get("session_id") and not outgoing.get("session_id"):
        outgoing["session_id"] = context.get("session_id")
    try:
        response = requests.post(
            f"{EDC_URL}/api/v1/edc/transfers",
            json=outgoing,
            headers=headers,
            timeout=8,
        )
        response.raise_for_status()
        return {"status": "ok", "data": response.json()}
    except requests.RequestException as exc:
        return {"status": "error", "error": str(exc)}


def _execute_aas_create(
    db: Session,
    params: dict[str, Any],
    payload: dict[str, Any],
    context: dict[str, Any],
    _metadata: dict[str, Any] | None,
    headers: dict[str, str],
) -> dict[str, Any]:
    outgoing = _default_payload(payload, params)
    if not isinstance(outgoing, dict):
        return {"status": "error", "error": "Payload must be object"}

    aas_identifier = outgoing.get("aas_identifier") or outgoing.get("id")
    product_name = outgoing.get("product_name") or outgoing.get("idShort")
    asset_info = outgoing.get("assetInformation", {}) if isinstance(outgoing.get("assetInformation"), dict) else {}
    product_identifier = outgoing.get("product_identifier") or asset_info.get("globalAssetId")
    if not aas_identifier:
        return {"status": "error", "error": "Missing aas_identifier"}

    adapter_payload = {
        "aas_identifier": str(aas_identifier),
        "product_name": product_name,
        "product_identifier": product_identifier,
    }
    try:
        adapter_result = _call_aas_adapter(
            "POST",
            "/api/v2/aas/shells",
            json_body=adapter_payload,
            headers=headers,
        )
    except requests.RequestException as exc:
        return {"status": "error", "error": str(exc)}
    shell = adapter_result.get("shell") or adapter_result.get("aas") or outgoing
    status = adapter_result.get("status") or "created"

    dpp = DppInstance(
        id=uuid4(),
        session_id=context.get("session_id"),
        aas_identifier=str(aas_identifier),
        product_identifier=product_identifier,
        product_name=product_name,
        product_category=outgoing.get("product_category"),
        compliance_status={},
    )
    try:
        db.add(dpp)
        db.commit()
    except Exception:
        db.rollback()

    try:
        from services.shared.repositories import digital_twin_repo

        snapshot = digital_twin_repo.create_snapshot(db, dpp_instance_id=dpp.id, label="Initial DPP")
        digital_twin_repo.add_node(
            db,
            snapshot.id,
            "product",
            "asset",
            product_name or "Product",
            {"aas_id": str(dpp.aas_identifier)},
        )
        digital_twin_repo.add_node(db, snapshot.id, "compliance", "status", "Compliance", {"status": "pending"})
        digital_twin_repo.add_node(db, snapshot.id, "transfer", "dataspace", "Transfer", {})
        digital_twin_repo.add_edge(db, snapshot.id, "product-compliance", "product", "compliance", "validates")
        digital_twin_repo.add_edge(db, snapshot.id, "product-transfer", "product", "transfer", "transfers")
    except Exception:
        pass
    return {"status": status, "data": shell}


def _execute_aas_submodel_add(
    _db: Session,
    params: dict[str, Any],
    payload: dict[str, Any],
    _context: dict[str, Any],
    _metadata: dict[str, Any] | None,
    headers: dict[str, str],
) -> dict[str, Any]:
    outgoing = _default_payload(payload, params)
    if not isinstance(outgoing, dict):
        return {"status": "error", "error": "Payload must be object"}
    submodel = outgoing.get("submodel") or outgoing
    try:
        adapter_result = _call_aas_adapter(
            "POST",
            "/api/v2/aas/submodels",
            json_body={"submodel": submodel},
            headers=headers,
        )
    except requests.RequestException as exc:
        return {"status": "error", "error": str(exc)}
    return {
        "status": adapter_result.get("status") or "created",
        "data": adapter_result.get("submodel", submodel),
    }


def _execute_aas_submodel_patch(
    _db: Session,
    params: dict[str, Any],
    payload: dict[str, Any],
    _context: dict[str, Any],
    _metadata: dict[str, Any] | None,
    headers: dict[str, str],
) -> dict[str, Any]:
    outgoing = _default_payload(payload, params)
    if not isinstance(outgoing, dict):
        return {"status": "error", "error": "Payload must be object"}
    submodel_id = outgoing.get("submodel_id")
    elements = outgoing.get("elements")
    if not submodel_id or elements is None:
        return {"status": "error", "error": "Missing submodel_id or elements"}
    try:
        adapter_result = _call_aas_adapter(
            "PATCH",
            f"/api/v2/aas/submodels/{submodel_id}/elements",
            json_body={"elements": elements},
            headers=headers,
        )
    except requests.RequestException as exc:
        return {"status": "error", "error": str(exc)}
    return {
        "status": adapter_result.get("status") or "updated",
        "data": adapter_result.get("elements", elements),
    }


def _execute_aas_update(
    db: Session,
    params: dict[str, Any],
    payload: dict[str, Any],
    context: dict[str, Any],
    _metadata: dict[str, Any] | None,
    _headers: dict[str, str],
) -> dict[str, Any]:
    outgoing = _default_payload(payload, params)
    update_name = None
    if isinstance(outgoing, dict):
        update_name = outgoing.get("update")
    if update_name and context.get("session_id"):
        session = db.query(SimulationSession).filter(SimulationSession.id == context.get("session_id")).first()
        if session:
            current_state = session.session_state or {}
            updates = current_state.get("aas_updates", [])
            updates.append(
                {
                    "update": update_name,
                    "payload": outgoing,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            session.session_state = {**current_state, "aas_updates": updates}
            try:
                db.commit()
            except Exception:
                db.rollback()
    return {"status": "updated", "data": outgoing}


def _execute_aasx_upload(
    db: Session,
    params: dict[str, Any],
    payload: dict[str, Any],
    context: dict[str, Any],
    metadata: dict[str, Any] | None,
    _headers: dict[str, str],
) -> dict[str, Any]:
    outgoing = _default_payload(payload, params)
    if not isinstance(outgoing, dict):
        return {"status": "error", "error": "Payload must be object"}
    filename = outgoing.get("filename") or "dpp.aasx"
    content = outgoing.get("content_base64") or outgoing.get("content")
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


def _execute_api_call(
    _db: Session,
    params: dict[str, Any],
    payload: dict[str, Any],
    _context: dict[str, Any],
    _metadata: dict[str, Any] | None,
    _headers: dict[str, str],
) -> dict[str, Any]:
    outgoing = _default_payload(payload, params)
    return {"status": "called", "data": outgoing}


def _execute_json_patch(
    _db: Session,
    params: dict[str, Any],
    payload: dict[str, Any],
    _context: dict[str, Any],
    _metadata: dict[str, Any] | None,
    _headers: dict[str, str],
) -> dict[str, Any]:
    outgoing = _default_payload(payload, params)
    if not isinstance(outgoing, dict):
        return {"status": "error", "error": "Payload must be object"}
    document = outgoing.get("document")
    operations = outgoing.get("operations")
    if not isinstance(document, dict) or not isinstance(operations, list):
        return {"status": "patched", "data": outgoing}

    patched = dict(document)
    for operation in operations:
        if not isinstance(operation, dict):
            continue
        op = operation.get("op")
        path = str(operation.get("path", "")).strip("/")
        if not path:
            continue
        if op in {"add", "replace"}:
            patched[path] = operation.get("value")
        elif op == "remove":
            patched.pop(path, None)
    return {"status": "patched", "data": patched}


STEP_PLUGINS: dict[str, StepHandler] = {
    "user.input": _execute_user_input,
    "compliance.check": _execute_compliance_check,
    "compliance_check": _execute_compliance_check,
    "edc.negotiate": _execute_edc_negotiation,
    "edc_negotiation": _execute_edc_negotiation,
    "edc.transfer": _execute_edc_transfer,
    "aas.create": _execute_aas_create,
    "aas_create_shell": _execute_aas_create,
    "aas.submodel.add": _execute_aas_submodel_add,
    "aas.submodel.patch": _execute_aas_submodel_patch,
    "aas.update": _execute_aas_update,
    "aasx.upload": _execute_aasx_upload,
    "aas_upload_aasx": _execute_aasx_upload,
    "api.call": _execute_api_call,
    "http_call": _execute_api_call,
    "json_patch": _execute_json_patch,
}


def register_step_plugin(step_type: str, handler: StepHandler) -> None:
    STEP_PLUGINS[step_type] = handler


def list_registered_step_plugins() -> list[str]:
    return sorted(STEP_PLUGINS.keys())


def execute_step(
    db: Session,
    action: str,
    params: dict[str, Any],
    payload: dict[str, Any],
    context: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    handler = STEP_PLUGINS.get(action)
    if handler is None:
        return {
            "status": "unknown_action",
            "message": f"No step plugin is registered for '{action}'",
            "action": action,
        }
    headers = _request_headers()
    request_id = context.get("request_id")
    if request_id:
        headers["X-Request-ID"] = str(request_id)
    try:
        result = handler(db, params, payload, context, metadata, headers)
    except Exception as exc:
        return {"status": "error", "message": f"Step execution failed for '{action}'", "error": str(exc)}

    status = result.get("status", "completed")
    result.setdefault("status", status)
    result.setdefault("message", f"Step '{action}' finished with status '{status}'")
    return result
