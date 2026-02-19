from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...core.db import get_db
from ...engine.rule_loader import (
    get_active_rule_version,
    list_rule_versions,
    load_all_rules,
    load_rules_for,
    validate_ruleset,
)
from services.shared.models.compliance_rule_version import ComplianceRuleVersion

router = APIRouter()

RULE_ADMIN_ROLES = ["regulator", "developer", "admin"]


class RuleVersionCreateRequest(BaseModel):
    regulation: str
    version: str
    rules: list[dict] = Field(default_factory=list)
    activate: bool = False


def _to_uuid(value: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid rule version id") from exc


def _serialize_rule(item: ComplianceRuleVersion, *, active_id: str | None) -> dict:
    item_id = str(item.id)
    return {
        "id": item_id,
        "regulation": item.regulation,
        "version": item.version,
        "rules": item.rules if isinstance(item.rules, list) else [],
        "active": item_id == active_id,
        "effective_from": item.effective_from.isoformat() if item.effective_from else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("/rules")
def list_rules(
    request: Request,
    regulation: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_versions: bool = False,
    db: Session = Depends(get_db),
):
    require_roles(request.state.user, RULE_ADMIN_ROLES)
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    if not include_versions:
        if regulation:
            return {regulation: load_rules_for(regulation, db=db)}
        return load_all_rules(db=db)

    items, total = list_rule_versions(db, regulation=regulation, limit=limit, offset=offset)
    active_ids: dict[str, str | None] = {}
    for reg in {item.regulation for item in items}:
        active = get_active_rule_version(db, reg)
        active_ids[reg.lower()] = str(active.id) if active else None
    rows = [
        _serialize_rule(item, active_id=active_ids.get(str(item.regulation).lower()))
        for item in items
    ]
    legacy_rules = {regulation: load_rules_for(regulation, db=db)} if regulation else load_all_rules(db=db)
    return {
        "items": rows,
        "total": total,
        "limit": limit,
        "offset": offset,
        # Backward-compatible alias for earlier simple rules listing consumers.
        "rules": legacy_rules,
    }


@router.post("/rules")
def upload_rules(request: Request, payload: RuleVersionCreateRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, RULE_ADMIN_ROLES)
    regulation = payload.regulation.strip()
    version = payload.version.strip()
    if not regulation:
        raise HTTPException(status_code=422, detail="regulation is required")
    if not version:
        raise HTTPException(status_code=422, detail="version is required")

    errors = validate_ruleset(payload.rules)
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "Invalid ruleset", "errors": errors},
        )

    active = get_active_rule_version(db, regulation)
    should_activate = payload.activate or active is None
    effective_from = datetime.now(timezone.utc) if should_activate else datetime(1970, 1, 1, tzinfo=timezone.utc)
    model = ComplianceRuleVersion(
        id=uuid4(),
        regulation=regulation,
        version=version,
        rules=payload.rules,
        effective_from=effective_from,
    )
    try:
        db.add(model)
        db.commit()
        db.refresh(model)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Rule version already exists for regulation") from exc

    return _serialize_rule(model, active_id=str(model.id) if should_activate else None)


@router.post("/rules/{rule_version_id}/activate")
def activate_rules(request: Request, rule_version_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, RULE_ADMIN_ROLES)
    version_id = _to_uuid(rule_version_id)
    model = db.query(ComplianceRuleVersion).filter(ComplianceRuleVersion.id == version_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Rule version not found")

    model.effective_from = datetime.now(timezone.utc)
    db.add(model)
    db.commit()
    db.refresh(model)
    return _serialize_rule(model, active_id=str(model.id))
