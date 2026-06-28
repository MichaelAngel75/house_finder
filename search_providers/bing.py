from __future__ import annotations

import requests

from config import (
    BING_API_KEY,
    BING_ENDPOINT,
    MAX_RESULTS_PER_QUERY,
    REQUEST_TIMEOUT_SECONDS,
)
from dedupe import normalize_url, domain_from_url
from models import SearchResult
from search_providers.base import SearchProvider


class BingSearchProvider(SearchProvider):
    def search(self, query: str, criteria_id: str) -> list[SearchResult]:
        if not BING_API_KEY:
            raise ValueError(
                "BING_API_KEY is required when SEARCH_PROVIDER=bing. "
                "Note: Bing Search APIs were retired for new usage, so prefer google or serpapi."
            )

        headers = {
            "Ocp-Apim-Subscription-Key": BING_API_KEY,
        }

        params = {
            "q": query,
            "count": MAX_RESULTS_PER_QUERY,
            "mkt": "es-MX",
            "responseFilter": "Webpages",
        }

        response = requests.get(
            BING_ENDPOINT,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        data = response.json()
        web_pages = data.get("webPages", {})
        values = web_pages.get("value", [])

        output: list[SearchResult] = []

        for item in values:
            link = item.get("url")

            if not link:
                continue

            url = normalize_url(link)

            output.append(
                SearchResult(
                    criteria_id=criteria_id,
                    query=query,
                    title=item.get("name", ""),
                    snippet=item.get("snippet", ""),
                    url=url,
                    source_domain=domain_from_url(url),
                )
            )

        return output