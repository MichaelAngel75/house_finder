from __future__ import annotations

import time
import requests

from config import SERPAPI_API_KEY, MAX_RESULTS_PER_QUERY, REQUEST_TIMEOUT_SECONDS
from dedupe import normalize_url, domain_from_url
from models import SearchResult
from search_providers.base import SearchProvider


class SerpApiSearchProvider(SearchProvider):
    endpoint = "https://serpapi.com/search.json"

    def search(self, query: str, criteria_id: str) -> list[SearchResult]:
        if not SERPAPI_API_KEY or SERPAPI_API_KEY == "your_serpapi_key_here":
            raise ValueError("SERPAPI_API_KEY is required when SEARCH_PROVIDER=serpapi")

        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "location": "Mexico City, Mexico",
            "google_domain": "google.com.mx",
            "hl": "es",
            "gl": "mx",
            "device": "desktop",
            "num": MAX_RESULTS_PER_QUERY,
        }

        last_error = None

        for attempt in range(1, 4):
            try:
                response = requests.get(
                    self.endpoint,
                    params=params,
                    timeout=(5, max(REQUEST_TIMEOUT_SECONDS, 30)),
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

            except requests.exceptions.Timeout as exc:
                last_error = exc
                print(f"  [yellow]SerpAPI timeout attempt {attempt}/3. Retrying...[/yellow]")
                time.sleep(attempt * 2)

            except requests.exceptions.RequestException as exc:
                last_error = exc
                print(f"  [red]SerpAPI request failed:[/red] {exc}")
                return []

        print(f"  [red]SerpAPI failed after retries:[/red] {last_error}")
        return []