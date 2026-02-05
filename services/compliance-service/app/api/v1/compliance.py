from fastapi import APIRouter
from ...schemas.compliance_schema import ComplianceCheckRequest
from ...engine.rule_engine import evaluate_payload

router = APIRouter()

@router.post("/compliance/check")
def check(payload: ComplianceCheckRequest):
    return evaluate_payload(payload.data, payload.regulations)
