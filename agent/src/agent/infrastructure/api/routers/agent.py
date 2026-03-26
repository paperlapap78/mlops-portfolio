"""
POST /agent — run the LangChain tool-use agent.

The agent receives a free-text message and decides which tools to call:
  - "Convert 100 CHF to EUR"  → currency tool
  - "Draft an email to ..."   → email drafting tool
  - anything else             → the LLM answers directly
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from agent.application.generation.agent_use_case import AgentUseCase
from agent.infrastructure.api.dependencies import get_agent_use_case

router = APIRouter(tags=["agent"])


class AgentRequest(BaseModel):
    message: str


class AgentResponse(BaseModel):
    response: str


@router.post("/agent", response_model=AgentResponse)
async def run_agent(
    req: AgentRequest,
    use_case: AgentUseCase = Depends(get_agent_use_case),
) -> AgentResponse:
    result = use_case.run(req.message)
    return AgentResponse(response=result)
