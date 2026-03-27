"""
Structured logging configuration using structlog.

Two modes, selected by the ENVIRONMENT setting:

  development  →  colored, human-readable output in your terminal:
                  2026-03-25 10:00:01 [info] Ingested chunks  url=https://example.com chunk_count=42

  production   →  JSON to stdout, picked up by EKS Fluent Bit and shipped to CloudWatch.
                  Each line is a JSON object queryable in CloudWatch Log Insights:
                  {"timestamp": "...", "level": "info", "event": "Ingested chunks",
                   "chunk_count": 42, "trace_id": "abc123"}

Call configure_logging() once at application startup (api/main.py lifespan),
before configure_telemetry(), so the trace_id processor can find an active span.
"""

import logging
import sys
from typing import Any

import structlog
from opentelemetry import trace


def _inject_trace_id(
    logger: Any,  # noqa: ANN401
    method: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """
    structlog processor that adds the current OTel trace_id to every log line.
    Links CloudWatch log entries to X-Ray traces — invaluable for debugging.
    If no span is active (e.g. during startup or in unit tests), the field is omitted.
    """
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
    return event_dict


def configure_logging(environment: str, service_name: str) -> None:
    """
    Configure structlog for the given environment.

    Parameters
    ----------
    environment:  "development" or "production"
    service_name: injected into every log line as the "service" key
    """
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,  # request-scoped fields (e.g. request_id)
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _inject_trace_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if environment == "development":
        renderer: Any = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # JSON to stdout — CloudWatch Log Insights can filter/aggregate on any field
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Bind service name globally so every log line carries it
    structlog.contextvars.bind_contextvars(service=service_name)

    # Redirect stdlib logging (e.g. from uvicorn, boto3) through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
