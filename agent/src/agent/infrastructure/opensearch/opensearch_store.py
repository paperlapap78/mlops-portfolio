"""
Adapter: OpenSearch Serverless vector store (via LlamaIndex)

Implements the DocumentStore port against Amazon OpenSearch Serverless (AOSS).

Key design points:
- Uses `opensearch-py` directly with SigV4 auth (RequestsAWSAuth, service="aoss")
- Uses LlamaIndex's OpenSearchVectorStore at the lower level (not VectorStoreIndex)
  because our domain model owns the chunking and lifecycle — not LlamaIndex
- ensure_index() creates the knn_vector index on first run; idempotent on subsequent runs
- Dimension 1536 matches Titan Embeddings v2 output — must match .env EMBEDDING_MODEL_ID

HNSW (Hierarchical Navigable Small World) is the approximate nearest-neighbour
algorithm used. Faiss engine gives best performance on OpenSearch Serverless.
"""

import structlog
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from llama_index.vector_stores.opensearch import OpensearchVectorStore, OpensearchVectorClient

from agent.domain.model.document import Chunk
from agent.domain.ports.document_store import DocumentStore

logger = structlog.get_logger()

_EMBEDDING_DIMENSION = 1536

_INDEX_BODY = {
    "settings": {
        "index.knn": True,
    },
    "mappings": {
        "properties": {
            "embedding": {
                "type": "knn_vector",
                "dimension": _EMBEDDING_DIMENSION,
                "method": {
                    "name": "hnsw",
                    "space_type": "l2",
                    "engine": "faiss",
                },
            },
            "content": {"type": "text"},
            "doc_id": {"type": "keyword"},
        }
    },
}


class OpenSearchStore(DocumentStore):
    def __init__(self, endpoint: str, index: str, region: str) -> None:
        self._index = index

        credentials = boto3.Session().get_credentials()
        auth = AWS4Auth(
            refreshable_credentials=credentials,
            region=region,
            service="aoss",
        )

        # Strip protocol prefix — opensearch-py expects just the host
        host = endpoint.replace("https://", "").replace("http://", "").rstrip("/")

        self._os_client = OpenSearch(
            hosts=[{"host": host, "port": 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )

        self._vector_client = OpensearchVectorClient(
            endpoint=endpoint,
            index=index,
            dim=_EMBEDDING_DIMENSION,
            embedding_field="embedding",
            text_field="content",
            http_auth=auth,
        )
        self._store = OpensearchVectorStore(self._vector_client)

        self._ensure_index()

    def _ensure_index(self) -> None:
        """Create the knn_vector index if it does not already exist."""
        if not self._os_client.indices.exists(index=self._index):
            self._os_client.indices.create(index=self._index, body=_INDEX_BODY)
            logger.info("Created OpenSearch index", index=self._index)
        else:
            logger.debug("OpenSearch index already exists", index=self._index)

    def index_chunks(self, chunks: list[Chunk]) -> None:
        from llama_index.core.schema import TextNode

        nodes = [
            TextNode(
                id_=chunk.id,
                text=chunk.text,
                embedding=list(chunk.embedding) if chunk.embedding else None,
                metadata={"doc_id": chunk.document_id},
            )
            for chunk in chunks
        ]
        self._store.add(nodes)
        logger.info("Indexed chunks", count=len(chunks), index=self._index)

    def similarity_search(self, embedding: list[float], top_k: int) -> list[Chunk]:
        from llama_index.core.vector_stores import VectorStoreQuery

        query = VectorStoreQuery(query_embedding=embedding, similarity_top_k=top_k)
        result = self._store.query(query)

        chunks = [
            Chunk(
                id=node.id_,
                document_id=node.metadata.get("doc_id", ""),
                text=node.text or "",
            )
            for node in (result.nodes or [])
        ]
        logger.debug("Similarity search completed", top_k=top_k, results=len(chunks))
        return chunks
