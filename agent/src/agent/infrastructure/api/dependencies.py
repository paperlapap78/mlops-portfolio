"""
Composition root — the single place where ports are wired to adapters.

This file is the only place in the entire codebase where concrete infrastructure
adapters (BedrockLLM, OpenSearchStore, etc.) are imported and instantiated.
All use cases receive their dependencies through this file via FastAPI's Depends().

@lru_cache on each factory function ensures adapters are created once per process
(singletons), which is important because boto3 clients and OpenSearch connections
are expensive to initialise.
"""

from functools import lru_cache
from typing import cast

from agent.application.generation.agent_use_case import AgentExecutorPort, AgentUseCase
from agent.application.ingestion.ingest_url_use_case import IngestUrlUseCase
from agent.application.retrieval.answer_query_use_case import AnswerQueryUseCase
from agent.infrastructure.api.settings import Settings, get_settings
from agent.infrastructure.aws.bedrock_embedder import BedrockEmbedder
from agent.infrastructure.aws.bedrock_llm import BedrockLLM
from agent.infrastructure.langchain_splitter import LangChainDocumentSplitter
from agent.infrastructure.opensearch.opensearch_store import OpenSearchStore
from agent.infrastructure.scrapers.httpx_scraper import HttpxScraper


# ── Infrastructure singletons ──────────────────────────────────────────────────

@lru_cache
def _bedrock_llm(settings: Settings | None = None) -> BedrockLLM:
    s = settings or get_settings()
    return BedrockLLM(region=s.aws_region, model_id=s.llm_model_id)


@lru_cache
def _bedrock_embedder(settings: Settings | None = None) -> BedrockEmbedder:
    s = settings or get_settings()
    return BedrockEmbedder(region=s.aws_region, model_id=s.embedding_model_id)


@lru_cache
def _opensearch_store(settings: Settings | None = None) -> OpenSearchStore:
    s = settings or get_settings()
    return OpenSearchStore(
        endpoint=s.opensearch_endpoint,
        index=s.opensearch_index,
        region=s.aws_region,
    )


@lru_cache
def _httpx_scraper() -> HttpxScraper:
    return HttpxScraper()


@lru_cache
def _document_splitter() -> LangChainDocumentSplitter:
    return LangChainDocumentSplitter()


# ── Use case factories (called per request via FastAPI Depends) ────────────────

def get_ingest_use_case() -> IngestUrlUseCase:
    return IngestUrlUseCase(
        scraper=_httpx_scraper(),
        splitter=_document_splitter(),
        embedder=_bedrock_embedder(),
        store=_opensearch_store(),
    )


def get_answer_use_case() -> AnswerQueryUseCase:
    s = get_settings()
    return AnswerQueryUseCase(
        embedder=_bedrock_embedder(),
        store=_opensearch_store(),
        llm=_bedrock_llm(),
        model_id=s.llm_model_id,
    )


@lru_cache
def _agent_executor() -> AgentExecutorPort:
    """
    Build the LangChain AgentExecutor.
    This is the only place in the entire codebase that imports LangChain directly.
    Typed as AgentExecutorPort (Protocol) — no Any needed.
    """
    from langchain import hub  # type: ignore[attr-defined]
    from langchain.agents import AgentExecutor, create_tool_calling_agent  # type: ignore[attr-defined]
    from langchain_aws import ChatBedrock

    from agent.infrastructure.tools.currency_tool import CurrencyConversionTool
    from agent.infrastructure.tools.email_tool import DraftEmailTool

    s = get_settings()
    chat_llm = ChatBedrock(model_id=s.llm_model_id, region_name=s.aws_region)
    tools = [
        DraftEmailTool(llm=_bedrock_llm(), model_id=s.llm_model_id),
        CurrencyConversionTool(),
    ]
    prompt = hub.pull("hwchase17/openai-tools-agent")
    agent = create_tool_calling_agent(chat_llm, tools, prompt)
    return cast(AgentExecutorPort, AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=5))


def get_agent_use_case() -> AgentUseCase:
    return AgentUseCase(executor=_agent_executor())
