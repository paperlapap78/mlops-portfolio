from langchain_text_splitters import RecursiveCharacterTextSplitter

from agent.application.ports.document_splitter import DocumentSplitterPort
from agent.domain.model.document import Chunk, Document


class LangChainDocumentSplitter(DocumentSplitterPort):
    """
    Concrete Adapter that implements the DocumentSplitterPort using LangChain.

    This safely quarantines all LangChain dependencies (and their potential breaking
    changes) strictly inside the Infrastructure layer.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        # We explicitly configure the semantic recursive strategy
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # It tries to split on paragraph first, then line, then space.
            separators=["\n\n", "\n", " ", ""],
        )

    def split(self, document: Document) -> list[Chunk]:
        if not document.raw_text.strip():
            return []

        # 1. Use LangChain to do the heavy semantic splitting
        text_chunks = self.splitter.split_text(document.raw_text)

        # 2. Map the vendor-specific output back to our Pure Python Context
        chunks: list[Chunk] = []
        for index, text in enumerate(text_chunks):
            chunks.append(Chunk(id=f"{document.id}_{index}", document_id=document.id, text=text))

        return chunks
