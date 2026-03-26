"""
Unit tests for IngestUrlUseCase.

All AWS infrastructure is replaced by fakes from conftest.py.
Tests focus on the orchestration logic: does the use case call the right
ports in the right order with the right data?
"""

import pytest

from agent.application.ingestion.ingest_url_use_case import IngestUrlUseCase
from tests.conftest import FakeDocumentStore, FakeEmbedder, FakeScraper, FakeSplitter


@pytest.fixture
def use_case(
    fake_scraper: FakeScraper,
    fake_splitter: FakeSplitter,
    fake_embedder: FakeEmbedder,
    fake_store: FakeDocumentStore,
) -> IngestUrlUseCase:
    return IngestUrlUseCase(
        scraper=fake_scraper,
        splitter=fake_splitter,
        embedder=fake_embedder,
        store=fake_store,
    )


class TestIngestUrlUseCase:
    def test_returns_chunk_count(self, use_case: IngestUrlUseCase) -> None:
        count = use_case.execute("https://example.com")
        assert count > 0

    def test_chunks_are_indexed_in_store(
        self,
        use_case: IngestUrlUseCase,
        fake_store: FakeDocumentStore,
    ) -> None:
        use_case.execute("https://example.com")
        assert len(fake_store.indexed) > 0

    def test_indexed_chunks_have_embeddings(
        self,
        use_case: IngestUrlUseCase,
        fake_store: FakeDocumentStore,
    ) -> None:
        use_case.execute("https://example.com")
        for chunk in fake_store.indexed:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == FakeEmbedder.DIMENSION

    def test_empty_page_returns_zero(
        self,
        fake_splitter: FakeSplitter,
        fake_embedder: FakeEmbedder,
        fake_store: FakeDocumentStore,
    ) -> None:
        empty_scraper = FakeScraper(text="   ")
        uc = IngestUrlUseCase(
            scraper=empty_scraper,
            splitter=fake_splitter,
            embedder=fake_embedder,
            store=fake_store,
        )
        assert uc.execute("https://example.com") == 0
        assert len(fake_store.indexed) == 0

    def test_chunk_document_id_matches_url(
        self,
        use_case: IngestUrlUseCase,
        fake_store: FakeDocumentStore,
    ) -> None:
        from agent.domain.model.document import Document
        url = "https://example.com"
        expected_doc_id = Document.create(url=url, raw_text="").id
        use_case.execute(url)
        for chunk in fake_store.indexed:
            assert chunk.document_id == expected_doc_id
