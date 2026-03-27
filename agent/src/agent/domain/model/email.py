"""
Domain model for email drafting requests and results.

Used by the LangChain email tool — the tool translates the agent's
natural language request into a DraftEmailRequest, which the LLM
then fulfils and returns as a DraftEmailResult.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DraftEmailRequest:
    recipient: str
    subject: str
    key_points: list[str]  # bullet points the email body should cover


@dataclass
class DraftEmailResult:
    body: str  # the drafted email body
    model_id: str  # which Bedrock model was used
