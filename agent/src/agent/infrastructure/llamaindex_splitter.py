from llama_index.core.node_parser import SentenceSplitter

from agent.application.ports.document_splitter import DocumentSplitterPort
from agent.domain.model.document import Chunk, Document


class LlamaIndexDocumentSplitter(DocumentSplitterPort):
    """
    Concrete Adapter that implements the DocumentSplitterPort using LlamaIndex.

    This replaces the LangChain dependency with LlamaIndex natively, while keeping
    the exact same Application and Domain layer compatibility perfectly intact.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        # LlamaIndex's premier semantic chunking tool
        self.splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def split(self, document: Document) -> list[Chunk]:
        if not document.raw_text.strip():
            return []

        # 1. Use LlamaIndex to do the heavy semantic splitting
        text_chunks = self.splitter.split_text(document.raw_text)

        # 2. Map the vendor-specific output back to our Pure Python Context
        chunks: list[Chunk] = []
        for index, text in enumerate(text_chunks):
            chunks.append(Chunk(id=f"{document.id}_{index}", document_id=document.id, text=text))

        return chunks
