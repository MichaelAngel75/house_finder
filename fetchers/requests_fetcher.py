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
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "noscript"]):
                tag.extract()

            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            text = soup.get_text(" ", strip=True)

            return PageContent(
                url=url,
                title=title,
                text=text[:12000],
                status_code=response.status_code,
            )

        except Exception as exc:
            return PageContent(
                url=url,
                fetch_error=str(exc),
            )