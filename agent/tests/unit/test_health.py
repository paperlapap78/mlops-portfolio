"""
Pragmatic smoke test for the API layer.
Verifies the app starts and /health responds — no AWS credentials needed.
"""

import os

import pytest
from fastapi.testclient import TestClient

# Set required env vars before importing the app
os.environ.setdefault("OPENSEARCH_ENDPOINT", "https://test.eu-central-1.aoss.amazonaws.com")
os.environ.setdefault("ENVIRONMENT", "development")


@pytest.fixture(scope="module")
def client() -> TestClient:
    from agent.infrastructure.api.main import app
    return TestClient(app, raise_server_exceptions=True)


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
