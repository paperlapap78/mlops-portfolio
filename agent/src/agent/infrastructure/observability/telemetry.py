"""
OpenTelemetry configuration.

In production (on EKS), traces are exported via OTLP gRPC to the AWS
Distro for OpenTelemetry (ADOT) collector sidecar running at localhost:4317.
The ADOT sidecar converts them to X-Ray format and forwards to CloudWatch.

In development (ENVIRONMENT=development), this function is a no-op — there
is no ADOT sidecar locally. Logs provide observability instead.

The FastAPI and httpx auto-instrumentors create spans for every inbound
HTTP request and every outbound HTTP call (to Frankfurter, OpenSearch)
without any changes to route handler code.
"""

import structlog

logger = structlog.get_logger()


def configure_telemetry(environment: str, service_name: str, otlp_endpoint: str) -> None:
    """
    Set up OpenTelemetry tracing.

    Parameters
    ----------
    environment:    "development" skips setup entirely (no-op)
    service_name:   appears as the service name in X-Ray traces
    otlp_endpoint:  gRPC endpoint of the ADOT sidecar, e.g. "http://localhost:4317"
    """
    if environment == "development":
        logger.info("OTel tracing disabled in development mode")
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_global_tracer_provider(provider)

    # Auto-instrument FastAPI — creates spans for every HTTP request handled
    FastAPIInstrumentor().instrument()

    # Auto-instrument httpx — creates spans for every outbound HTTP call
    # (Frankfurter API, any other external calls)
    HTTPXClientInstrumentor().instrument()

    logger.info("OTel tracing enabled", otlp_endpoint=otlp_endpoint, service=service_name)
