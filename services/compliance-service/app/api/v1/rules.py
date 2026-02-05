from fastapi import APIRouter, Request
from ...engine.rule_loader import load_all_rules
from ...auth import require_roles

router = APIRouter()

@router.get("/rules")
def list_rules(request: Request):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    return load_all_rules()
