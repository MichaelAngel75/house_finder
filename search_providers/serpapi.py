from __future__ import annotations

import requests

from config import SERPAPI_API_KEY, MAX_RESULTS_PER_QUERY, REQUEST_TIMEOUT_SECONDS
from dedupe import normalize_url, domain_from_url
from models import SearchResult
from search_providers.base import SearchProvider


class SerpApiSearchProvider(SearchProvider):
    endpoint = "https://serpapi.com/search.json"

    def search(self, query: str, criteria_id: str) -> list[SearchResult]:
        if not SERPAPI_API_KEY:
            raise ValueError(
                "SERPAPI_API_KEY is required when SEARCH_PROVIDER=serpapi"
            )

        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "hl": "es",
            "gl": "mx",
            "num": MAX_RESULTS_PER_QUERY,
        }

        response = requests.get(
            self.endpoint,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        data = response.json()
        organic_results = data.get("organic_results", [])

        output: list[SearchResult] = []

        for item in organic_results[:MAX_RESULTS_PER_QUERY]:
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

        return output