from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from ...auth import require_roles
from ...config import COMPLIANCE_URL
from ...core.db import get_db
from services.shared.models.compliance_report import ComplianceReport
from services.shared.repositories import compliance_fix_repo
from services.shared.user_registry import resolve_user_id

router = APIRouter()

COMPLIANCE_ROLES = ["manufacturer", "developer", "admin", "regulator"]
TRACE_HEADERS = ("traceparent", "tracestate", "baggage")


class ComplianceRunCreateRequest(BaseModel):
    dpp_id: str | None = None
    regulations: list[str] = Field(default_factory=lambda: ["ESPR", "Battery Regulation", "WEEE", "RoHS"])
    payload: dict[str, Any] = Field(default_factory=dict)


class JsonPatchOperation(BaseModel):
    op: Literal["add", "replace", "remove"]
    path: str
    value: Any | None = None

    @model_validator(mode="after")
    def validate_value(self):
        if self.op in {"add", "replace"} and self.value is None:
            raise ValueError("value is required for add/replace operations")
        return self


class ComplianceFixApplyRequest(BaseModel):
    # Legacy compatibility fields.
    path: str | None = None
    value: Any | None = None
    # New JSON Patch subset.
    operations: list[JsonPatchOperation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self):
        if self.operations:
            return self
        if not self.path:
            raise ValueError("Either operations or path must be provided")
        return self


def _to_uuid(value: str, *, field_name: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid {field_name}") from exc


def _forward_upstream_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    if request_id:
        headers["X-Request-ID"] = str(request_id)

    authorization = request.headers.get("authorization")
    if authorization:
        headers["Authorization"] = authorization
    else:
        dev_user = request.headers.get("x-dev-user")
        dev_roles = request.headers.get("x-dev-roles")
        if dev_user:
            headers["X-Dev-User"] = dev_user
        if dev_roles:
            headers["X-Dev-Roles"] = dev_roles

    for header in TRACE_HEADERS:
        value = request.headers.get(header)
        if value:
            headers[header] = value
    return headers


def _run_compliance_check(request: Request, payload: dict[str, Any], regulations: list[str]) -> dict[str, Any]:
    try:
        response = requests.post(
            f"{COMPLIANCE_URL}/api/v1/compliance/check",
            json={"data": payload, "regulations": regulations},
            headers=_forward_upstream_headers(request),
            timeout=8,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Compliance service unavailable: {exc}") from exc


def _decode_pointer(path: str) -> list[str]:
    if path == "":
        return []
    if not path.startswith("/"):
        raise ValueError("path must use JSON Pointer syntax (must start with '/')")
    return [part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")]


def _pointer_from_legacy_path(path: str) -> str:
    value = (path or "").strip()
    if not value:
        raise ValueError("path is required")
    if value.startswith("/"):
        return value
    if value == "$":
        return ""
    if value.startswith("$."):
        tokens = [token for token in value[2:].split(".") if token]
    elif value.startswith("$"):
        tokens = [token for token in value[1:].split(".") if token]
    else:
        tokens = [token for token in value.split(".") if token]
    escaped = [token.replace("~", "~0").replace("/", "~1") for token in tokens]
    return "/" + "/".join(escaped)


def _parse_list_index(token: str, *, length: int, allow_end: bool) -> int:
    if token == "-" and allow_end:
        return length
    if not token.isdigit():
        raise ValueError(f"invalid array index '{token}'")
    index = int(token)
    if allow_end and index == length:
        return index
    if index < 0 or index >= length:
        raise ValueError(f"array index out of bounds '{token}'")
    return index


def _resolve_parent(document: Any, path_tokens: list[str]) -> tuple[Any, str]:
    if not path_tokens:
        raise ValueError("empty pointer has no parent")
    current = document
    for token in path_tokens[:-1]:
        if isinstance(current, dict):
            if token not in current:
                raise ValueError(f"path segment '{token}' not found")
            current = current[token]
            continue
        if isinstance(current, list):
            idx = _parse_list_index(token, length=len(current), allow_end=False)
            current = current[idx]
            continue
        raise ValueError("cannot traverse non-container value")
    return current, path_tokens[-1]


def _apply_single_operation(document: Any, operation: JsonPatchOperation) -> Any:
    tokens = _decode_pointer(operation.path)
    if not tokens:
        if operation.op == "remove":
            raise ValueError("cannot remove root document")
        return deepcopy(operation.value)

    parent, token = _resolve_parent(document, tokens)
    if isinstance(parent, dict):
        if operation.op == "add":
            parent[token] = deepcopy(operation.value)
            return document
        if operation.op == "replace":
            if token not in parent:
                raise ValueError(f"path '{operation.path}' does not exist for replace")
            parent[token] = deepcopy(operation.value)
            return document
        if token not in parent:
            raise ValueError(f"path '{operation.path}' does not exist for remove")
        del parent[token]
        return document

    if isinstance(parent, list):
        if operation.op == "add":
            idx = _parse_list_index(token, length=len(parent), allow_end=True)
            parent.insert(idx, deepcopy(operation.value))
            return document
        if operation.op == "replace":
            idx = _parse_list_index(token, length=len(parent), allow_end=False)
            parent[idx] = deepcopy(operation.value)
            return document
        idx = _parse_list_index(token, length=len(parent), allow_end=False)
        parent.pop(idx)
        return document

    raise ValueError("target parent is not an object or array")


def _apply_patch(document: Any, operations: list[JsonPatchOperation]) -> Any:
    patched = deepcopy(document)
    for operation in operations:
        patched = _apply_single_operation(patched, operation)
    return patched


def _normalize_operations(payload: ComplianceFixApplyRequest) -> list[JsonPatchOperation]:
    if payload.operations:
        return payload.operations
    pointer = _pointer_from_legacy_path(payload.path or "")
    return [JsonPatchOperation(op="replace", path=pointer, value=payload.value)]


def _serialize_fix_history(report_id: UUID, db: Session) -> list[dict[str, Any]]:
    fixes = compliance_fix_repo.list_fixes_for_report(db, report_id)
    return [
        {
            "id": str(item.id),
            "path": item.path,
            "value": item.value,
            "applied_by": str(item.applied_by) if item.applied_by else None,
            "applied_at": item.applied_at.isoformat() if item.applied_at else None,
        }
        for item in fixes
    ]


def _resolve_actor_user_id(db: Session, user: dict | None) -> str | None:
    try:
        return resolve_user_id(db, user)
    except Exception:
        db.rollback()
        return None


@router.get("/core/compliance/status")
def compliance_status(request: Request):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    return {"status": "ok", "module": "compliance"}


@router.post("/core/compliance/runs")
def create_run(request: Request, payload: ComplianceRunCreateRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    upstream = _run_compliance_check(request, payload.payload, payload.regulations)

    user_id = _resolve_actor_user_id(db, getattr(request.state, "user", None))
    report = ComplianceReport(
        id=uuid4(),
        user_id=user_id,
        story_code=None,
        regulations=payload.regulations,
        status=upstream.get("status", "unknown"),
        report={
            "violations": upstream.get("violations", []),
            "warnings": upstream.get("warnings", []),
            "recommendations": upstream.get("recommendations", []),
            "summary": upstream.get("summary"),
            "payload": payload.payload,
            "dpp_id": payload.dpp_id,
        },
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(report.id),
        "status": report.status,
        "dpp_id": payload.dpp_id,
        "regulations": payload.regulations,
        "payload": payload.payload,
        "violations": upstream.get("violations", []),
        "warnings": upstream.get("warnings", []),
        "recommendations": upstream.get("recommendations", []),
        "summary": upstream.get("summary"),
        "created_at": now,
        "updated_at": now,
    }


@router.get("/core/compliance/runs/{run_id}")
def get_run(request: Request, run_id: str, db: Session = Depends(get_db)):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    run_uuid = _to_uuid(run_id, field_name="run_id")
    report = db.query(ComplianceReport).filter(ComplianceReport.id == run_uuid).first()
    if not report:
        raise HTTPException(status_code=404, detail="Compliance run not found")
    data = report.report or {}
    return {
        "id": str(report.id),
        "status": report.status,
        "dpp_id": data.get("dpp_id"),
        "regulations": report.regulations or [],
        "payload": data.get("payload", {}),
        "violations": data.get("violations", []),
        "warnings": data.get("warnings", []),
        "recommendations": data.get("recommendations", []),
        "summary": data.get("summary"),
        "fixes": _serialize_fix_history(report.id, db),
        "created_at": report.created_at.isoformat() if report.created_at else "",
        "updated_at": report.created_at.isoformat() if report.created_at else "",
    }


@router.post("/core/compliance/runs/{run_id}/apply-fix")
def apply_fix(request: Request, run_id: str, payload: ComplianceFixApplyRequest, db: Session = Depends(get_db)):
    require_roles(request.state.user, COMPLIANCE_ROLES)
    run_uuid = _to_uuid(run_id, field_name="run_id")
    report = db.query(ComplianceReport).filter(ComplianceReport.id == run_uuid).first()
    if not report:
        raise HTTPException(status_code=404, detail="Compliance run not found")

    operations = _normalize_operations(payload)

    data = dict(report.report or {})
    original_payload = data.get("payload")
    if not isinstance(original_payload, dict):
        raise HTTPException(status_code=409, detail="Compliance run payload is not patchable")
    before_payload = deepcopy(original_payload)
    before_violations = list(data.get("violations") or [])
    before_warnings = list(data.get("warnings") or [])
    before_recommendations = list(data.get("recommendations") or [])

    try:
        patched_payload = _apply_patch(before_payload, operations)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid patch operation: {exc}") from exc
    if not isinstance(patched_payload, dict):
        raise HTTPException(status_code=422, detail="Patched payload must be an object")

    user_id = _resolve_actor_user_id(db, getattr(request.state, "user", None))
    for operation in operations:
        stored_value = {"op": operation.op}
        if operation.op in {"add", "replace"}:
            stored_value["value"] = operation.value
        compliance_fix_repo.create_fix(
            db,
            report_id=report.id,
            path=operation.path,
            value=stored_value,
            applied_by=user_id,
            commit=False,
        )

    upstream = _run_compliance_check(request, patched_payload, report.regulations or [])
    data["payload"] = patched_payload
    data["violations"] = upstream.get("violations", [])
    data["warnings"] = upstream.get("warnings", [])
    data["recommendations"] = upstream.get("recommendations", [])
    data["summary"] = upstream.get("summary")
    report.report = data
    report.status = upstream.get("status", report.status)
    db.add(report)
    db.commit()
    db.refresh(report)

    before_counts = {
        "violations": len(before_violations),
        "warnings": len(before_warnings),
        "recommendations": len(before_recommendations),
    }
    after_counts = {
        "violations": len(data["violations"]),
        "warnings": len(data["warnings"]),
        "recommendations": len(data["recommendations"]),
    }
    deltas = {
        key: after_counts[key] - before_counts[key]
        for key in before_counts
    }
    return {
        "run_id": str(report.id),
        "status": report.status,
        "payload": patched_payload,
        "operations_applied": [operation.model_dump(exclude_none=True) for operation in operations],
        "before": {"summary": before_counts},
        "after": {"summary": after_counts},
        "deltas": deltas,
        "fixes": _serialize_fix_history(report.id, db),
    }
