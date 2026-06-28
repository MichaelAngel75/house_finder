from __future__ import annotations

import requests

from config import (
    GOOGLE_API_KEY,
    GOOGLE_SEARCH_ENGINE_ID,
    MAX_RESULTS_PER_QUERY,
    REQUEST_TIMEOUT_SECONDS,
)
from dedupe import normalize_url, domain_from_url
from models import SearchResult
from search_providers.base import SearchProvider


class GoogleCustomSearchProvider(SearchProvider):
    endpoint = "https://www.googleapis.com/customsearch/v1"

    def search(self, query: str, criteria_id: str) -> list[SearchResult]:
        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is required when SEARCH_PROVIDER=google"
            )

        if not GOOGLE_SEARCH_ENGINE_ID:
            raise ValueError(
                "GOOGLE_SEARCH_ENGINE_ID is required when SEARCH_PROVIDER=google"
            )

        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_SEARCH_ENGINE_ID,
            "q": query,
            "num": min(MAX_RESULTS_PER_QUERY, 10),
            "hl": "es",
            "gl": "mx",
        }

        response = requests.get(
            self.endpoint,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        output: list[SearchResult] = []

        for item in items:
            link = item.get("link")

            if not link:
                continue

            url = normalize_url(link)

            output.append(
                SearchResult(
                    criteria_id=criteria_id,
                    query=query,
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    url=url,
                    source_domain=domain_from_url(url),
                )
            )

        return outputghtyfjk