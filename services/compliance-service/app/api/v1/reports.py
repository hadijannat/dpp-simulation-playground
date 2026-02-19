from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.compliance_report import ComplianceReport
from ...auth import require_roles

router = APIRouter()

@router.get("/reports")
def list_reports(
    request: Request,
    session_id: str | None = None,
    story_code: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    query = db.query(ComplianceReport)
    if session_id:
        query = query.filter(ComplianceReport.session_id == session_id)
    if story_code:
        query = query.filter(ComplianceReport.story_code == story_code)
    if status:
        query = query.filter(ComplianceReport.status == status)
    total = query.count()
    items = (
        query.order_by(ComplianceReport.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    rows = [
        {
            "id": str(item.id),
            "session_id": str(item.session_id) if item.session_id else None,
            "story_code": item.story_code,
            "status": item.status,
            "regulations": item.regulations,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]
    return {
        "items": rows,
        "total": total,
        "limit": limit,
        "offset": offset,
        # Backward-compatible alias for existing clients.
        "reports": rows,
    }


@router.get("/reports/{report_id}")
def get_report(request: Request, report_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, ["regulator", "developer", "admin"])
    item = db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": str(item.id),
        "session_id": str(item.session_id) if item.session_id else None,
        "story_code": item.story_code,
        "status": item.status,
        "regulations": item.regulations,
        "report": item.report,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }
