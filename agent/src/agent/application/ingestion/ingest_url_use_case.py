"""
Use case: Ingest a URL into the vector store.

Orchestrates the full ingestion pipeline:
  1. Fetch the URL → Document
  2. Split the Document into Chunks (via injected DocumentSplitterPort)
  3. Embed all Chunks in one batch
  4. Attach embeddings to Chunks
  5. Index the Chunks in the vector store

This class imports only domain/application ports and models — no boto3, no LangChain.
The concrete adapters are injected at startup via infrastructure/api/dependencies.py.
"""

import structlog

from agent.application.ports.document_splitter import DocumentSplitterPort
from agent.domain.ports.document_store import DocumentStore
from agent.domain.ports.embedder import Embedder
from agent.domain.ports.scraper import WebScraper

logger = structlog.get_logger()


class IngestUrlUseCase:
    def __init__(
        self,
        scraper: WebScraper,
        splitter: DocumentSplitterPort,
        embedder: Embedder,
        store: DocumentStore,
    ) -> None:
        self._scraper = scraper
        self._splitter = splitter
        self._embedder = embedder
        self._store = store

    def execute(self, url: str) -> int:
        """
        Ingest the given URL.
        Returns the number of chunks indexed.
        """
        doc = self._scraper.fetch(url)
        chunks = self._splitter.split(doc)

        if not chunks:
            logger.warning("No chunks produced — page may be empty", url=url)
            return 0

        # Batch embed all chunk texts in a single API call
        texts = [chunk.text for chunk in chunks]
        embeddings = self._embedder.embed_texts(texts)

        # Attach embeddings — creates new frozen Chunk instances (domain model is immutable)
        embedded_chunks = [
            chunk.with_embedding(embedding)
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]

        self._store.index_chunks(embedded_chunks)

        logger.info("Ingested URL", url=url, chunk_count=len(embedded_chunks))
        return len(embedded_chunks)
