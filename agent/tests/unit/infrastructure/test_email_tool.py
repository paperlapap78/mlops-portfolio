"""
Unit tests for DraftEmailTool.

All tests use FakeLLM — no AWS credentials required.
"""

import json

import pytest

from agent.infrastructure.tools.email_tool import DraftEmailTool
from tests.conftest import FakeLLM

_TOOL_INPUT = json.dumps({
    "recipient": "alice@example.com",
    "subject": "Project Update",
    "key_points": ["Milestone reached", "Next steps defined"],
})


@pytest.fixture
def tool() -> DraftEmailTool:
    return DraftEmailTool(llm=FakeLLM(response="Dear Alice, ..."), model_id="test-model")


class TestDraftEmailTool:
    def test_returns_llm_response_as_string(self, tool: DraftEmailTool) -> None:
        result = tool._run(_TOOL_INPUT)
        assert result == "Dear Alice, ..."

    def test_prompt_contains_recipient_and_subject(self, tool: DraftEmailTool) -> None:
        # FakeLLM captures the last prompt — verify the domain fields are present
        fake_llm = tool._llm  # type: ignore[attr-defined]
        tool._run(_TOOL_INPUT)
        assert "alice@example.com" in fake_llm.last_prompt
        assert "Project Update" in fake_llm.last_prompt

    def test_prompt_contains_key_points(self, tool: DraftEmailTool) -> None:
        fake_llm = tool._llm  # type: ignore[attr-defined]
        tool._run(_TOOL_INPUT)
        assert "Milestone reached" in fake_llm.last_prompt
        assert "Next steps defined" in fake_llm.last_prompt
