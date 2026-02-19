from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict
from ...odrl.policy_builder import build_policy
from ...odrl.policy_evaluator import evaluate_policy
from ...auth import require_roles

router = APIRouter()

class PolicyRequest(BaseModel):
    purpose: str

class PolicyEvalRequest(BaseModel):
    purpose: str
    policy: Dict
    context: Dict | None = None

@router.post("/policies/build")
def build(request: Request, payload: PolicyRequest):
    require_roles(request.state.user, ["developer", "manufacturer", "admin"])
    return build_policy(payload.purpose)

@router.post("/policies/evaluate")
def evaluate(request: Request, payload: PolicyEvalRequest):
    require_roles(request.state.user, ["developer", "manufacturer", "admin", "regulator"])
    allowed = evaluate_policy(payload.policy, payload.purpose, context=payload.context or {})
    if not allowed:
        raise HTTPException(status_code=403, detail="Policy does not allow this purpose")
    return {"allowed": True}
