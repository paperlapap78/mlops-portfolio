"""
Unit tests for AnswerQueryUseCase.

Verifies that the use case correctly orchestrates embed → retrieve → generate,
and that the Response carries the right provenance data.
"""

import pytest

from agent.application.retrieval.answer_query_use_case import AnswerQueryUseCase
from agent.domain.model.document import Chunk
from agent.domain.model.query import Query
from tests.conftest import FakeDocumentStore, FakeEmbedder, FakeLLM


@pytest.fixture
def pre_populated_store(fake_store: FakeDocumentStore) -> FakeDocumentStore:
    """A store that already contains some indexed chunks."""
    fake_store.indexed = [
        Chunk(id="abc_0", document_id="abc", text="Paris is the capital of France."),
        Chunk(id="abc_1", document_id="abc", text="The Eiffel Tower is in Paris."),
    ]
    return fake_store


@pytest.fixture
def use_case(
    fake_embedder: FakeEmbedder,
    pre_populated_store: FakeDocumentStore,
    fake_llm: FakeLLM,
) -> AnswerQueryUseCase:
    return AnswerQueryUseCase(
        embedder=fake_embedder,
        store=pre_populated_store,
        llm=fake_llm,
        model_id="test-model",
    )


class TestAnswerQueryUseCase:
    def test_returns_response_with_answer(self, use_case: AnswerQueryUseCase) -> None:
        response = use_case.execute(Query(text="What is the capital of France?"))
        assert response.answer == "This is a test answer."

    def test_response_includes_source_chunks(
        self,
        use_case: AnswerQueryUseCase,
        pre_populated_store: FakeDocumentStore,
    ) -> None:
        response = use_case.execute(Query(text="Tell me about Paris", top_k=2))
        assert len(response.source_chunks) == 2

    def test_response_includes_model_id(self, use_case: AnswerQueryUseCase) -> None:
        response = use_case.execute(Query(text="question"))
        assert response.model_id == "test-model"

    def test_response_includes_latency(self, use_case: AnswerQueryUseCase) -> None:
        response = use_case.execute(Query(text="question"))
        assert response.latency_ms >= 0

    def test_prompt_contains_retrieved_context(
        self,
        use_case: AnswerQueryUseCase,
        fake_llm: FakeLLM,
    ) -> None:
        use_case.execute(Query(text="Tell me about Paris"))
        # The LLM's prompt should contain text from the retrieved chunks
        assert "Paris" in fake_llm.last_prompt

    def test_top_k_limits_source_chunks(
        self,
        fake_embedder: FakeEmbedder,
        pre_populated_store: FakeDocumentStore,
        fake_llm: FakeLLM,
    ) -> None:
        uc = AnswerQueryUseCase(embedder=fake_embedder, store=pre_populated_store, llm=fake_llm)
        response = uc.execute(Query(text="question", top_k=1))
        assert len(response.source_chunks) <= 1
