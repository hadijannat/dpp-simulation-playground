from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from ...schemas.compliance_schema import ComplianceCheckRequest
from ...engine.rule_engine import evaluate_payload
from ...core.db import get_db
from ...models.compliance_report import ComplianceReport
from ...auth import require_roles

router = APIRouter()

@router.post("/compliance/check")
def check(request: Request, payload: ComplianceCheckRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["manufacturer", "regulator", "developer", "admin"])
    result = evaluate_payload(payload.data, payload.regulations)
    report = ComplianceReport(
        id=uuid4(),
        user_id=request.state.user.get("sub"),
        session_id=payload.session_id,
        story_code=payload.story_code,
        regulations=payload.regulations,
        status=result.get("status"),
        report=result,
    )
    try:
        db.add(report)
        db.commit()
    except Exception:
        db.rollback()
    return result
