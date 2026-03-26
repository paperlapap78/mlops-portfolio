"""
Port: Embedder

Converts text strings into dense vector representations.
The concrete adapter (BedrockEmbedder) calls Titan Embeddings v2,
but the application layer doesn't know or care about that.
"""

from abc import ABC, abstractmethod


class Embedder(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of texts and return one vector per text.
        Vectors must be 1536-dimensional (Titan Embeddings v2 output size).
        """
