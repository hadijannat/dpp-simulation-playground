from typing import Dict, Any
import requests
from ..config import COMPLIANCE_URL, EDC_URL
from .service_token import get_service_token


def execute_step(action: str, params: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    token = get_service_token()
    headers = {"Authorization": f"Bearer {token}"}
    if action == "user.input":
        return {"status": "awaiting_input", "prompt": params.get("prompt")}
    if action == "compliance.check":
        resp = requests.post(f"{COMPLIANCE_URL}/api/v1/compliance/check", json=payload, headers=headers)
        return resp.json()
    if action == "edc.negotiate":
        resp = requests.post(f"{EDC_URL}/api/v1/edc/negotiations", json=payload, headers=headers)
        return resp.json()
    if action == "aas.create":
        return {"status": "created", "data": payload}
    if action == "aas.update":
        return {"status": "updated", "data": payload}
    if action == "api.call":
        return {"status": "called", "data": payload}
    return {"status": "unknown_action", "action": action}
