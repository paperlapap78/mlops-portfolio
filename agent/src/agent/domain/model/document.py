"""
Domain model for documents and chunks.

A Document is a raw webpage fetched from a URL.
A Chunk is a fixed-size piece of a Document's text, ready for embedding.

These are pure Python dataclasses — no external dependencies.
The split_into_chunks function is a pure function that can be unit-tested
without any AWS, LangChain, or LlamaIndex involvement.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Document:
    """A webpage fetched from a URL, before any chunking or embedding."""

    id: str          # deterministic: sha256(url)[:12] — same URL always yields same ID
    url: str
    raw_text: str
    fetched_at: datetime

    @staticmethod
    def create(url: str, raw_text: str) -> "Document":
        """Factory that generates a deterministic ID from the URL."""
        doc_id = hashlib.sha256(url.encode()).hexdigest()[:12]
        return Document(
            id=doc_id,
            url=url,
            raw_text=raw_text,
            fetched_at=datetime.now(timezone.utc),
        )


@dataclass(frozen=True)
class Chunk:
    """A fixed-size slice of a Document's text, optionally carrying its embedding vector."""

    id: str                              # f"{document_id}_{chunk_index}"
    document_id: str
    text: str
    embedding: tuple[float, ...] | None = field(default=None)

    def with_embedding(self, embedding: list[float]) -> "Chunk":
        """Return a new Chunk with the embedding attached (dataclass is frozen)."""
        return Chunk(
            id=self.id,
            document_id=self.document_id,
            text=self.text,
            embedding=tuple(embedding),
        )


