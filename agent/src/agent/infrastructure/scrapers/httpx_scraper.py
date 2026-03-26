"""
Adapter: Web Scraper (httpx + BeautifulSoup)

Implements the WebScraper port. Fetches a URL with httpx, then uses
BeautifulSoup to strip HTML tags and return clean plain text.

httpx is OTel auto-instrumented (HTTPXClientInstrumentor in telemetry.py),
so every fetch appears as a span in X-Ray automatically.
"""

import httpx
import structlog
from bs4 import BeautifulSoup

from agent.domain.model.document import Document
from agent.domain.ports.scraper import WebScraper

logger = structlog.get_logger()


class HttpxScraper(WebScraper):
    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self._timeout = timeout_seconds

    def fetch(self, url: str) -> Document:
        logger.info("Fetching URL", url=url)

        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Remove script and style blocks — they add noise without semantic value
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        plain_text = soup.get_text(separator=" ", strip=True)
        logger.info("Fetched URL", url=url, text_length=len(plain_text))

        return Document.create(url=url, raw_text=plain_text)
