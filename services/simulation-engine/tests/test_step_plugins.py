from __future__ import annotations

from typing import Any

from app.config import AAS_ADAPTER_URL
from app.core.step_executor import (
    execute_step,
    list_registered_step_plugins,
    register_step_plugin,
)


def test_default_plugins_include_core_step_types():
    plugins = list_registered_step_plugins()
    assert "compliance.check" in plugins
    assert "edc_negotiation" in plugins
    assert "aas_upload_aasx" in plugins


def test_register_plugin_and_execute():
    def _custom_handler(db, params, payload, context, metadata, headers):
        return {"status": "ok", "data": {"echo": payload}}

    register_step_plugin("custom.echo", _custom_handler)
    result = execute_step(
        db=None,
        action="custom.echo",
        params={},
        payload={"value": 7},
        context={},
    )
    assert result["status"] == "ok"
    assert result["data"]["echo"]["value"] == 7
    assert "message" in result


def test_unknown_plugin_returns_machine_and_human_readable_output():
    result = execute_step(
        db=None,
        action="does.not.exist",
        params={},
        payload={},
        context={},
    )
    assert result["status"] == "unknown_action"
    assert "message" in result


def test_aas_create_plugin_delegates_to_aas_adapter(monkeypatch):
    class _Db:
        def add(self, _obj):
            return None

        def commit(self):
            return None

        def rollback(self):
            return None

    class _DummyResponse:
        def __init__(self, payload: Any, status_code: int = 200):
            self._payload = payload
            self.status_code = status_code

        @property
        def content(self) -> bytes:
            import json

            return json.dumps(self._payload).encode()

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError("request failed")

        def json(self):
            return self._payload

    calls: list[dict[str, Any]] = []

    def _fake_request(
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 8,
        **_kwargs: Any,
    ):
        calls.append(
            {
                "method": method,
                "url": url,
                "json": json,
                "headers": headers or {},
                "timeout": timeout,
            }
        )
        return _DummyResponse(
            {"status": "created", "shell": {"id": "urn:uuid:us-02-01"}}
        )

    monkeypatch.setattr(
        "app.core.step_executor.get_service_token", lambda: "service-token"
    )
    monkeypatch.setattr("app.core.step_executor.pooled_request", _fake_request)

    result = execute_step(
        db=_Db(),
        action="aas.create",
        params={},
        payload={
            "id": "urn:uuid:us-02-01",
            "idShort": "DPP-Create",
            "assetInformation": {"globalAssetId": "urn:example:asset:us-02-01"},
        },
        context={
            "session_id": "s-1",
            "story_code": "US-02-01",
            "user_id": "u-1",
            "request_id": "req-step-1",
        },
    )

    assert result["status"] == "created"
    assert calls
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == f"{AAS_ADAPTER_URL}/api/v2/aas/shells"
    assert calls[0]["headers"]["Authorization"] == "Bearer service-token"
    assert calls[0]["headers"]["X-Request-ID"] == "req-step-1"
