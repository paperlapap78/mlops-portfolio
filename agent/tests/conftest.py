"""
In-memory fakes for all domain ports.

These are concrete implementations of the port ABCs that work entirely
in-memory — no AWS credentials, no network, no Docker required.
Pytest discovers them here and makes them available to every test via fixtures.

Using fakes (not mocks) keeps tests readable and refactor-proof:
if a port's interface changes, mypy will catch it here immediately.
"""

import pytest

from agent.application.ports.document_splitter import DocumentSplitterPort
from agent.domain.model.document import Chunk, Document
from agent.domain.ports.currency_service import CurrencyService
from agent.domain.ports.document_store import DocumentStore
from agent.domain.ports.embedder import Embedder
from agent.domain.ports.llm import LLM
from agent.domain.ports.scraper import WebScraper


class FakeDocumentStore(DocumentStore):
    """Stores chunks in a plain list; similarity_search returns them in insertion order."""

    def __init__(self) -> None:
        self.indexed: list[Chunk] = []

    def index_chunks(self, chunks: list[Chunk]) -> None:
        self.indexed.extend(chunks)

    def similarity_search(self, embedding: list[float], top_k: int) -> list[Chunk]:
        return self.indexed[:top_k]


class FakeEmbedder(Embedder):
    """Returns a deterministic non-zero vector for each text (avoids all-zeros edge cases)."""

    DIMENSION = 1536

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t) % 10 + 1)] * self.DIMENSION for t in texts]


class FakeLLM(LLM):
    """Returns a configurable canned response — lets tests assert on the answer."""

    def __init__(self, response: str = "This is a test answer.") -> None:
        self.response = response
        self.last_prompt: str = ""

    def complete(self, prompt: str, *, max_tokens: int = 1024) -> str:
        self.last_prompt = prompt
        return self.response


class FakeSplitter(DocumentSplitterPort):
    """Splits on whitespace into fixed-size word chunks — deterministic, no LangChain needed."""

    def __init__(self, chunk_size: int = 5) -> None:
        self.chunk_size = chunk_size

    def split(self, document: Document) -> list[Chunk]:
        words = document.raw_text.split()
        if not words:
            return []
        return [
            Chunk(
                id=f"{document.id}_{i}",
                document_id=document.id,
                text=" ".join(words[i : i + self.chunk_size]),
            )
            for i in range(0, len(words), self.chunk_size)
        ]


class FakeScraper(WebScraper):
    """Returns a Document with configurable text — no HTTP calls made."""

    def __init__(self, text: str = "Hello world this is a test page.") -> None:
        self.text = text

    def fetch(self, url: str) -> Document:
        return Document.create(url=url, raw_text=self.text)


class FakeCurrencyService(CurrencyService):
    """Always returns amount * rate regardless of currencies — useful for asserting math."""

    def __init__(self, rate: float = 0.95) -> None:
        self.rate = rate

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        return round(amount * self.rate, 2)


# ── Pytest fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def fake_splitter() -> FakeSplitter:
    return FakeSplitter()


@pytest.fixture
def fake_store() -> FakeDocumentStore:
    return FakeDocumentStore()


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def fake_scraper() -> FakeScraper:
    return FakeScraper()
