from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
from ...odrl.policy_builder import build_policy
from ...odrl.policy_evaluator import evaluate_policy

router = APIRouter()

class PolicyRequest(BaseModel):
    purpose: str

class PolicyEvalRequest(BaseModel):
    purpose: str
    policy: Dict

@router.post("/policies/build")
def build(payload: PolicyRequest):
    return build_policy(payload.purpose)

@router.post("/policies/evaluate")
def evaluate(payload: PolicyEvalRequest):
    return {"allowed": evaluate_policy(payload.policy, payload.purpose)}
