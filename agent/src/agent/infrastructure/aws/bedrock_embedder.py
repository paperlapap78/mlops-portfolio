"""
Adapter: Bedrock Embedder (Titan Embeddings v2)

Implements the Embedder port using Amazon Titan Embeddings v2.
Output dimension: 1536 — must match the OpenSearch index mapping.

Titan accepts one text per API call, so embed_texts loops over the input.
A batch optimisation (asyncio.gather) is a future improvement if latency
becomes an issue during ingestion of large documents.
"""

import json

import boto3
import structlog
from opentelemetry import trace

from agent.domain.ports.embedder import Embedder

logger = structlog.get_logger()
_tracer = trace.get_tracer(__name__)


class BedrockEmbedder(Embedder):
    def __init__(self, region: str, model_id: str) -> None:
        self._model_id = model_id
        self._client = boto3.client("bedrock-runtime", region_name=region)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []

        with _tracer.start_as_current_span("bedrock.embed") as span:
            span.set_attribute("embed.model_id", self._model_id)
            span.set_attribute("embed.text_count", len(texts))

            for text in texts:
                body = {"inputText": text}
                response = self._client.invoke_model(
                    modelId=self._model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json",
                )
                result = json.loads(response["body"].read())
                embeddings.append(result["embedding"])

        logger.debug("Embedded texts", model_id=self._model_id, count=len(texts))
        return embeddings
