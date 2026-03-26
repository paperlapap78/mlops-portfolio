"""
LangChain tool: Draft Email

The LangChain agent calls this tool when the user asks it to write an email.
The tool takes the agent's structured input, calls the LLM port (not boto3 directly),
and returns the drafted email body as a plain string.

Injecting the LLM port (rather than hardcoding BedrockLLM) means this tool
can be unit-tested with FakeLLM from conftest.py without any AWS credentials.
"""

import json

import structlog
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from agent.domain.model.email import DraftEmailRequest, DraftEmailResult
from agent.domain.ports.llm import LLM

logger = structlog.get_logger()

_EMAIL_PROMPT = """\
Write a professional email with the following details:
- Recipient: {recipient}
- Subject: {subject}
- Key points to cover:
{key_points}

Write only the email body. Start with a greeting and end with a sign-off.
Keep the tone professional and concise."""


class _EmailInput(BaseModel):
    recipient: str = Field(description="Email address or name of the recipient")
    subject: str = Field(description="Subject line of the email")
    key_points: list[str] = Field(description="List of points the email body should cover")


class DraftEmailTool(BaseTool):
    name: str = "draft_email"
    description: str = (
        "Draft a professional email. "
        'Input must be JSON with keys: "recipient" (str), "subject" (str), '
        '"key_points" (list of strings).'
    )

    # LangChain BaseTool uses Pydantic — private fields must bypass model validation
    _llm: LLM
    _model_id: str

    def __init__(self, llm: LLM, model_id: str) -> None:
        super().__init__()
        object.__setattr__(self, "_llm", llm)
        object.__setattr__(self, "_model_id", model_id)

    def _run(self, tool_input: str) -> str:
        # _EmailInput validates the raw JSON from the LangChain agent
        validated = _EmailInput(**json.loads(tool_input))

        # Map to the domain model — canonical representation inside this adapter
        request = DraftEmailRequest(
            recipient=validated.recipient,
            subject=validated.subject,
            key_points=validated.key_points,
        )

        key_points_text = "\n".join(f"  - {point}" for point in request.key_points)
        prompt = _EMAIL_PROMPT.format(
            recipient=request.recipient,
            subject=request.subject,
            key_points=key_points_text,
        )

        body = self._llm.complete(prompt)
        email_result = DraftEmailResult(body=body, model_id=self._model_id)
        logger.info("Email drafted", recipient=request.recipient, subject=request.subject)
        return email_result.body  # LangChain expects str
