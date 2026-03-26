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

    # LangChain BaseTool uses Pydantic — fields must be declared at class level
    _llm: LLM

    def __init__(self, llm: LLM) -> None:
        super().__init__()
        object.__setattr__(self, "_llm", llm)

    def _run(self, tool_input: str) -> str:
        data = json.loads(tool_input)
        validated = _EmailInput(**data)

        key_points_text = "\n".join(f"  - {point}" for point in validated.key_points)
        prompt = _EMAIL_PROMPT.format(
            recipient=validated.recipient,
            subject=validated.subject,
            key_points=key_points_text,
        )

        result = self._llm.complete(prompt)
        logger.info("Email drafted", recipient=validated.recipient, subject=validated.subject)
        return result
