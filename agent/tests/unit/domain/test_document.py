"""
Unit tests for Document, Chunk, and split_into_chunks.

These are pure domain tests — no fixtures needed, no AWS, no network.
They run in milliseconds and can be executed anywhere.
"""

from agent.domain.model.document import Chunk, Document


class TestDocumentCreate:
    def test_id_is_deterministic(self) -> None:
        url = "https://example.com"
        d1 = Document.create(url=url, raw_text="text")
        d2 = Document.create(url=url, raw_text="different text")
        assert d1.id == d2.id  # same URL → same ID regardless of content

    def test_different_urls_give_different_ids(self) -> None:
        d1 = Document.create(url="https://example.com", raw_text="text")
        d2 = Document.create(url="https://other.com", raw_text="text")
        assert d1.id != d2.id

    def test_id_is_12_chars(self) -> None:
        doc = Document.create(url="https://example.com", raw_text="text")
        assert len(doc.id) == 12


class TestChunkWithEmbedding:
    def test_returns_new_chunk_with_embedding(self) -> None:
        chunk = Chunk(id="abc_0", document_id="abc", text="hello world")
        embedding = [0.1, 0.2, 0.3]
        result = chunk.with_embedding(embedding)

        assert result.embedding == tuple(embedding)
        assert result.id == chunk.id
        assert result.text == chunk.text

    def test_original_chunk_unchanged(self) -> None:
        chunk = Chunk(id="abc_0", document_id="abc", text="hello world")
        chunk.with_embedding([0.1])
        assert chunk.embedding is None  # frozen dataclass — original untouched


