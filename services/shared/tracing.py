"""Shared OpenTelemetry + Prometheus instrumentation for backend services."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_tracer_configured = False
_requests_instrumented = False
_sqlalchemy_instrumented_ids: set[int] = set()


def _parse_resource_attributes() -> dict[str, str]:
    attrs: dict[str, str] = {}
    raw = os.getenv("OTEL_RESOURCE_ATTRIBUTES", "").strip()
    if not raw:
        return attrs
    for item in raw.split(","):
        key, _, value = item.partition("=")
        key = key.strip()
        value = value.strip()
        if key and value:
            attrs[key] = value
    return attrs


def _configure_provider(service_name: str) -> None:
    global _tracer_configured

    if _tracer_configured:
        return

    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider

    attrs = _parse_resource_attributes()
    attrs["service.name"] = service_name

    provider = TracerProvider(resource=Resource.create(attrs))

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        )

    trace.set_tracer_provider(provider)
    _tracer_configured = True


def instrument_app(app: Any, service_name: str = "unknown") -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        _configure_provider(service_name)
        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        logger.debug("FastAPI tracing instrumentation unavailable", exc_info=True)

    try:
        from prometheus_client import make_asgi_app

        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
    except Exception:
        logger.debug("Prometheus metrics mount unavailable", exc_info=True)


def instrument_requests_client(service_name: str = "unknown") -> None:
    global _requests_instrumented
    if _requests_instrumented:
        return

    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        _configure_provider(service_name)
        RequestsInstrumentor().instrument()
        _requests_instrumented = True
    except Exception:
        logger.debug("Requests tracing instrumentation unavailable", exc_info=True)


def instrument_sqlalchemy_engine(engine: Any, service_name: str = "unknown") -> None:
    engine_id = id(engine)
    if engine_id in _sqlalchemy_instrumented_ids:
        return

    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        _configure_provider(service_name)
        SQLAlchemyInstrumentor().instrument(engine=engine)
        _sqlalchemy_instrumented_ids.add(engine_id)
    except Exception:
        logger.debug("SQLAlchemy tracing instrumentation unavailable", exc_info=True)
