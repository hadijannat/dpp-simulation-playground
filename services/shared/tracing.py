"""Shared OpenTelemetry + Prometheus instrumentation for all backend services."""
import os

def instrument_app(app, service_name: str = "unknown"):
    """Add OpenTelemetry tracing and Prometheus /metrics to a FastAPI app.

    Safe no-op when dependencies are missing — services can import this
    even before the packages are installed.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        pass

    try:
        from prometheus_client import make_asgi_app
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
    except ImportError:
        pass
