"""
Application settings loaded from environment variables (or .env file).

pydantic-settings reads values from the environment automatically.
In local dev: copy .env.example to .env and fill in OPENSEARCH_ENDPOINT.
On EKS: values come from the Helm ConfigMap; secrets via IRSA (no explicit key/secret).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment — controls log format and OTel behaviour
    environment: str = "development"

    # AWS
    aws_region: str = "eu-central-1"

    # Bedrock model IDs
    llm_model_id: str = "anthropic.claude-haiku-20240307-v1:0"
    embedding_model_id: str = "amazon.titan-embed-text-v2:0"

    # OpenSearch Serverless
    opensearch_endpoint: str
    opensearch_index: str = "agent-chunks"

    # Observability
    service_name: str = "mlops-agent"
    otlp_endpoint: str = "http://localhost:4317"


@lru_cache
def get_settings() -> Settings:
    """Singleton settings — reads env vars once and caches the result."""
    return Settings()  # type: ignore[call-arg]
