"""
Use case: Run the LangChain tool-use agent.

AgentExecutorPort is a Protocol that describes the one method we need from
LangChain's AgentExecutor — invoke(). Using a Protocol instead of importing
LangChain directly keeps the application layer free of infrastructure dependencies,
while still giving mypy full type-safety (no Any needed).

The concrete LangChain AgentExecutor satisfies this Protocol structurally
(duck typing) without needing to subclass it.
"""

from typing import Protocol

import structlog

logger = structlog.get_logger()


class AgentExecutorPort(Protocol):
    """
    Structural interface for anything that can run an agent given an input dict.
    LangChain's AgentExecutor satisfies this Protocol without modification.
    """

    def invoke(self, input: dict[str, str]) -> dict[str, str]:
        ...


class AgentUseCase:
    def __init__(self, executor: AgentExecutorPort) -> None:
        self._executor = executor

    def run(self, message: str) -> str:
        """
        Run the agent with the given user message.
        The agent decides which tools (email drafting, currency conversion)
        to invoke based on the message content.
        """
        logger.info("Agent invoked", message_length=len(message))
        result = self._executor.invoke({"input": message})
        output = result.get("output", "")
        logger.info("Agent completed", response_length=len(output))
        return output
