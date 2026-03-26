"""
POST /query — answer a question using RAG against the ingested vector store.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from agent.application.retrieval.answer_query_use_case import AnswerQueryUseCase
from agent.domain.model.query import Query
from agent.infrastructure.api.dependencies import get_answer_use_case

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    source_chunk_ids: list[str]    # for explainability and RAGAS evaluation
    model_id: str
    latency_ms: float


@router.post("/query", response_model=QueryResponse)
async def query(
    req: QueryRequest,
    use_case: AnswerQueryUseCase = Depends(get_answer_use_case),
) -> QueryResponse:
    response = use_case.execute(Query(text=req.question, top_k=req.top_k))
    return QueryResponse(
        answer=response.answer,
        source_chunk_ids=[chunk.id for chunk in response.source_chunks],
        model_id=response.model_id,
        latency_ms=round(response.latency_ms, 1),
    )
