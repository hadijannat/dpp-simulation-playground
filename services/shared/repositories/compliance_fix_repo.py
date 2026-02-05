from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from ..models.compliance_run_fix import ComplianceRunFix


def create_fix(
    db: Session, report_id, path: str, value, applied_by=None
) -> ComplianceRunFix:
    fix = ComplianceRunFix(
        id=uuid4(),
        report_id=report_id,
        path=path,
        value=value,
        applied_by=applied_by,
    )
    db.add(fix)
    db.commit()
    db.refresh(fix)
    return fix


def list_fixes_for_report(db: Session, report_id) -> list[ComplianceRunFix]:
    return (
        db.query(ComplianceRunFix)
        .filter(ComplianceRunFix.report_id == report_id)
        .order_by(ComplianceRunFix.applied_at)
        .all()
    )
