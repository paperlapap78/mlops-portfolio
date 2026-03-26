"""
Port: WebScraper

Fetches a URL and returns its textual content as a Document.
The concrete adapter uses httpx + BeautifulSoup, but the application
layer is decoupled from any HTTP library.
"""

from abc import ABC, abstractmethod

from agent.domain.model.document import Document


class WebScraper(ABC):
    @abstractmethod
    def fetch(self, url: str) -> Document:
        """Fetch the given URL and return a Document containing its plain text."""
