from typing import Protocol
from agent.domain.model.document import Document, Chunk

class DocumentSplitterPort(Protocol):
    """
    Interface (Port) for splitting documents into chunks.
    
    The Application layer (business logic) depends ONLY on this pure Python interface. 
    It has no idea if the underlying engine doing the splitting is LangChain, LlamaIndex, 
    or a custom pure-Python function.
    """
    def split(self, document: Document) -> list[Chunk]:
        ...
