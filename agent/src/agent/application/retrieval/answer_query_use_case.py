"""
Use case: Answer a user question using RAG (Retrieval-Augmented Generation).

Pipeline:
  1. Embed the user's question
  2. Search the vector store for the most relevant chunks
  3. Build a grounded prompt: context chunks + question
  4. Send to the LLM and return the answer with source provenance

Keeping source_chunks in the Response enables:
  - Explainability: "here's what I based that on"
  - RAGAS evaluation: did the answer come from the retrieved context?
  - CloudWatch monitoring: log chunk IDs for debugging retrieval quality
"""

import time

import structlog

from agent.domain.model.query import Query, Response
from agent.domain.ports.document_store import DocumentStore
from agent.domain.ports.embedder import Embedder
from agent.domain.ports.llm import LLM

logger = structlog.get_logger()

_PROMPT_TEMPLATE = """\
You are a helpful assistant. Answer the question using ONLY the context provided below.
If the context does not contain enough information to answer, say so clearly.

Context:
{context}

Question: {question}

Answer:"""


class AnswerQueryUseCase:
    def __init__(
        self,
        embedder: Embedder,
        store: DocumentStore,
        llm: LLM,
        model_id: str = "unknown",
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._llm = llm
        self._model_id = model_id

    def execute(self, query: Query) -> Response:
        start = time.monotonic()

        # Embed the question using the same model used during ingestion
        [query_embedding] = self._embedder.embed_texts([query.text])

        # Retrieve the top-k most semantically similar chunks
        source_chunks = self._store.similarity_search(query_embedding, query.top_k)

        if not source_chunks:
            logger.warning("No chunks retrieved — vector store may be empty", query=query.text)

        # Ground the LLM with the retrieved context
        context = "\n\n".join(chunk.text for chunk in source_chunks)
        prompt = _PROMPT_TEMPLATE.format(context=context, question=query.text)

        answer = self._llm.complete(prompt)

        latency_ms = (time.monotonic() - start) * 1000
        logger.info(
            "Query answered",
            latency_ms=round(latency_ms, 1),
            source_chunk_count=len(source_chunks),
        )

        return Response(
            answer=answer,
            source_chunks=source_chunks,
            model_id=self._model_id,
            latency_ms=latency_ms,
        )
