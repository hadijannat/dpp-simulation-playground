from fastapi import APIRouter
from pydantic import BaseModel
from ...odrl.policy_builder import build_policy
from ...odrl.policy_evaluator import evaluate_policy

router = APIRouter()

class PolicyRequest(BaseModel):
    purpose: str

@router.post("/policies/build")
def build(payload: PolicyRequest):
    return build_policy(payload.purpose)

@router.post("/policies/evaluate")
def evaluate(payload: PolicyRequest, policy: dict):
    return {"allowed": evaluate_policy(policy, payload.purpose)}
