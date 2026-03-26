"""
Port: LLM

Defines the contract for text generation.
The concrete adapter (BedrockLLM) calls Claude Haiku via boto3,
but the application layer only sees this simple interface.
"""

from abc import ABC, abstractmethod


class LLM(ABC):
    @abstractmethod
    def complete(self, prompt: str, *, max_tokens: int = 1024) -> str:
        """Send a prompt and return the generated text response."""
