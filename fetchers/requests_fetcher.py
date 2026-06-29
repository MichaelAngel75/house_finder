from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT_SECONDS
from models import PageContent
from fetchers.base import PageFetcher


class RequestsFetcher(PageFetcher):
    def fetch(self, url: str) -> PageContent:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                # timeout=REQUEST_TIMEOUT_SECONDS,
                timeout=(10, 15),   # Meaning: 10 seconds to connect, 15 seconds to read.
                allow_redirects=True,
            )

            html = response.text or ""

            soup = BeautifulSoup(html, "html.parser")

            for tag in soup(["script", "style", "noscript"]):
                tag.extract()

            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            text = soup.get_text(" ", strip=True)

            fetch_error = None
            if response.status_code >= 400:
                fetch_error = f"HTTP {response.status_code}"

            return PageContent(
                url=url,
                title=title,
                text=text[:20000],
                html=html[:300000],
                status_code=response.status_code,
                fetch_error=fetch_error,
            )

        except Exception as exc:
            return PageContent(
                url=url,
                title="",
                text="",
                html="",
                status_code=None,
                fetch_error=str(exc),
            )