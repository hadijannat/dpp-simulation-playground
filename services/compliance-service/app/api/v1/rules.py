from fastapi import APIRouter
from ...engine.rule_loader import load_all_rules

router = APIRouter()

@router.get("/rules")
def list_rules():
    return load_all_rules()
