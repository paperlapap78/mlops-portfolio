"""
Port: DocumentStore

Defines the contract for storing and searching document chunks.
The application layer calls this interface — it has no knowledge of
whether the underlying store is OpenSearch, pgvector, or an in-memory dict.
"""

from abc import ABC, abstractmethod

from agent.domain.model.document import Chunk


class DocumentStore(ABC):
    @abstractmethod
    def index_chunks(self, chunks: list[Chunk]) -> None:
        """Persist a batch of embedded chunks to the vector store."""

    @abstractmethod
    def similarity_search(self, embedding: list[float], top_k: int) -> list[Chunk]:
        """Return the top_k chunks most similar to the given embedding vector."""
