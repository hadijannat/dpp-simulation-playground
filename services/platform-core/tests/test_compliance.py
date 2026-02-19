from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import pytest

from services.shared.models.compliance_report import ComplianceReport
from services.shared.models.compliance_run_fix import ComplianceRunFix  # noqa: F401
from services.shared.models.audit_log import AuditLog


HEADERS = {
    "X-Dev-User": "test-user",
    "X-Dev-Roles": "developer,manufacturer,admin,regulator,consumer,recycler",
}


@dataclass
class DummyComplianceResponse:
    payload: dict[str, Any]
    status_code: int = 200

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("upstream error")

    def json(self) -> dict[str, Any]:
        return self.payload


def _seed_report(db_session, *, payload: dict[str, Any]) -> ComplianceReport:
    report = ComplianceReport(
        id=uuid4(),
        user_id=None,
        session_id=None,
        story_code=None,
        regulations=["ESPR"],
        status="non-compliant",
        report={
            "payload": payload,
            "violations": [{"id": "v1", "path": "$.battery.weight"}],
            "warnings": [],
            "recommendations": [],
            "summary": {"violations": 1, "warnings": 0, "recommendations": 0},
        },
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


def test_apply_fix_legacy_payload_is_wrapped_and_applied(client, db_session, monkeypatch: pytest.MonkeyPatch):
    report = _seed_report(db_session, payload={"battery": {"weight": 5}})

    def fake_post(*args, **kwargs):
        return DummyComplianceResponse(
            {
                "status": "compliant",
                "violations": [],
                "warnings": [],
                "recommendations": [],
                "summary": {"violations": 0, "warnings": 0, "recommendations": 0},
            }
        )

    monkeypatch.setattr("app.api.v2.compliance.requests.post", fake_post)

    response = client.post(
        f"/api/v2/core/compliance/runs/{report.id}/apply-fix",
        json={"path": "$.battery.weight", "value": 10},
        headers=HEADERS,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "compliant"
    assert body["payload"]["battery"]["weight"] == 10
    assert body["operations_applied"] == [{"op": "replace", "path": "/battery/weight", "value": 10}]
    assert body["deltas"]["violations"] == -1
    audit_entry = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "compliance.fix_applied", AuditLog.object_id == str(report.id))
        .first()
    )
    assert audit_entry is not None
    assert audit_entry.payload_hash


def test_apply_fix_json_patch_remove_operation(client, db_session, monkeypatch: pytest.MonkeyPatch):
    report = _seed_report(db_session, payload={"battery": {"weight": 5, "unit": "kg"}})

    def fake_post(*args, **kwargs):
        return DummyComplianceResponse(
            {
                "status": "non-compliant",
                "violations": [{"id": "v2", "path": "/battery/weight"}],
                "warnings": [],
                "recommendations": [],
                "summary": {"violations": 1, "warnings": 0, "recommendations": 0},
            }
        )

    monkeypatch.setattr("app.api.v2.compliance.requests.post", fake_post)

    response = client.post(
        f"/api/v2/core/compliance/runs/{report.id}/apply-fix",
        json={"operations": [{"op": "remove", "path": "/battery/unit"}]},
        headers=HEADERS,
    )

    assert response.status_code == 200
    body = response.json()
    assert "unit" not in body["payload"]["battery"]
    assert body["operations_applied"] == [{"op": "remove", "path": "/battery/unit"}]


def test_create_run_writes_audit_entry(client, db_session, monkeypatch: pytest.MonkeyPatch):
    def fake_post(*args, **kwargs):
        return DummyComplianceResponse(
            {
                "status": "non-compliant",
                "violations": [{"id": "v1"}],
                "warnings": [],
                "recommendations": [],
                "summary": {"violations": 1, "warnings": 0, "recommendations": 0},
            }
        )

    monkeypatch.setattr("app.api.v2.compliance.requests.post", fake_post)

    response = client.post(
        "/api/v2/core/compliance/runs",
        json={"regulations": ["ESPR"], "payload": {"product": {"name": "Battery"}}},
        headers=HEADERS,
    )
    assert response.status_code == 200
    run_id = response.json()["id"]
    audit_entry = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "compliance.run_created", AuditLog.object_id == run_id)
        .first()
    )
    assert audit_entry is not None
    assert audit_entry.payload_hash


def test_apply_fix_rejects_invalid_json_pointer(client, db_session, monkeypatch: pytest.MonkeyPatch):
    report = _seed_report(db_session, payload={"battery": {"weight": 5}})

    def fake_post(*args, **kwargs):
        return DummyComplianceResponse({"status": "compliant", "violations": []})

    monkeypatch.setattr("app.api.v2.compliance.requests.post", fake_post)

    response = client.post(
        f"/api/v2/core/compliance/runs/{report.id}/apply-fix",
        json={"operations": [{"op": "replace", "path": "battery/weight", "value": 10}]},
        headers=HEADERS,
    )

    assert response.status_code == 422
