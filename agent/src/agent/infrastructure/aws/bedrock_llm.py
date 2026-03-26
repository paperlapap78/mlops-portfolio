"""
Adapter: Bedrock LLM (Claude Haiku)

Implements the LLM port using AWS Bedrock's `invoke_model` API.
Uses the Anthropic Messages format, which is what Claude models expect on Bedrock.

An OTel span wraps each invocation so X-Ray traces show Bedrock call duration
and prompt/response sizes — useful for cost attribution in CloudWatch.
"""

import json

import boto3
import structlog
from opentelemetry import trace

from agent.domain.ports.llm import LLM

logger = structlog.get_logger()
_tracer = trace.get_tracer(__name__)


class BedrockLLM(LLM):
    def __init__(self, region: str, model_id: str) -> None:
        self._model_id = model_id
        self._client = boto3.client("bedrock-runtime", region_name=region)

    def complete(self, prompt: str, *, max_tokens: int = 1024) -> str:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        with _tracer.start_as_current_span("bedrock.complete") as span:
            span.set_attribute("llm.model_id", self._model_id)
            span.set_attribute("llm.prompt_length", len(prompt))

            logger.debug("Invoking Bedrock LLM", model_id=self._model_id, prompt_length=len(prompt))

            response = self._client.invoke_model(
                modelId=self._model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            result = json.loads(response["body"].read())
            answer: str = result["content"][0]["text"]

            span.set_attribute("llm.response_length", len(answer))
            logger.debug("Bedrock LLM responded", response_length=len(answer))

        return answer
