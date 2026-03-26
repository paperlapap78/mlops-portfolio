"""
FastAPI application factory.

The lifespan context manager runs at startup and shutdown:
  1. configure_logging()   — must be first so all subsequent log calls are formatted
  2. configure_telemetry() — OTel setup (no-op in development)

Routers are mounted with their URL prefixes here.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from agent.infrastructure.api.routers import agent, health, ingest, query
from agent.infrastructure.api.settings import get_settings
from agent.infrastructure.observability.logging import configure_logging
from agent.infrastructure.observability.telemetry import configure_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    # Logging first — ensures every subsequent log (including OTel setup) is formatted
    configure_logging(
        environment=settings.environment,
        service_name=settings.service_name,
    )

    configure_telemetry(
        environment=settings.environment,
        service_name=settings.service_name,
        otlp_endpoint=settings.otlp_endpoint,
    )

    import structlog
    log = structlog.get_logger()
    log.info(
        "Application started",
        environment=settings.environment,
        region=settings.aws_region,
    )

    yield  # application runs here

    log.info("Application shutting down")


app = FastAPI(
    title="MLOps Agent",
    description="RAG + tool-use agent powered by AWS Bedrock and OpenSearch Serverless",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(agent.router)
