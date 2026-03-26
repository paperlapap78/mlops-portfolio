"""
Health check endpoint — required by Kubernetes liveness and readiness probes.

This endpoint intentionally has no AWS dependencies. It must return 200
even if Bedrock or OpenSearch is unreachable, so the pod is not restarted
due to downstream service issues.
"""

from importlib.metadata import version

from fastapi import APIRouter

router = APIRouter(tags=["health"])

_VERSION = version("mlops-agent")   # read once at import time from package metadata


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mlops-agent", "version": _VERSION}
