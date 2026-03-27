"""
Domain model for queries and responses.

Query represents a user's question to the RAG pipeline.
Response carries the generated answer alongside the source chunks
that were retrieved — important for explainability and evaluation (RAGAS).
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.domain.model.document import Chunk


@dataclass
class Query:
    """A user question sent to the RAG retrieval pipeline."""

    text: str
    top_k: int = 5  # how many chunks to retrieve from the vector store


@dataclass
class Response:
    """The generated answer, together with provenance and performance metadata."""

    answer: str
    source_chunks: list[Chunk]  # the retrieved chunks used to ground the answer
    model_id: str  # which Bedrock model generated the response
    latency_ms: float  # end-to-end latency — useful for CloudWatch
