from fastapi import APIRouter, Request
from ...schemas.compliance_schema import ComplianceCheckRequest
from ...engine.rule_engine import evaluate_payload
from ...auth import require_roles

router = APIRouter()

@router.post("/compliance/check")
def check(request: Request, payload: ComplianceCheckRequest):
    require_roles(request.state.user, ["manufacturer", "regulator", "developer", "admin"])
    return evaluate_payload(payload.data, payload.regulations)
