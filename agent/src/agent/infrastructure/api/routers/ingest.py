"""
POST /ingest — trigger ingestion of a URL into the vector store.

Returns 202 Accepted immediately after indexing completes.
In a future iteration this could become truly async (background task + status endpoint),
but for now synchronous ingestion is sufficient for the dev portfolio.
"""

from fastapi import APIRouter, Depends
from pydantic import AnyHttpUrl, BaseModel

from agent.application.ingestion.ingest_url_use_case import IngestUrlUseCase
from agent.infrastructure.api.dependencies import get_ingest_use_case

router = APIRouter(tags=["ingest"])


class IngestRequest(BaseModel):
    url: AnyHttpUrl


class IngestResponse(BaseModel):
    status: str
    url: str
    chunks_indexed: int


@router.post("/ingest", response_model=IngestResponse, status_code=202)
async def ingest(
    req: IngestRequest,
    use_case: IngestUrlUseCase = Depends(get_ingest_use_case),
) -> IngestResponse:
    count = use_case.execute(str(req.url))
    return IngestResponse(status="ingested", url=str(req.url), chunks_indexed=count)
