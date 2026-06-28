from __future__ import annotations

from dedupe import normalize_url, domain_from_url
from models import SearchResult
from search_providers.base import SearchProvider


class MockSearchProvider(SearchProvider):
    def search(self, query: str, criteria_id: str) -> list[SearchResult]:
        examples = [
            {
                "title": "Casa en remate bancario adjudicado en Portales",
                "snippet": (
                    "Casa en remate bancario, adjudicado, posible escrituración. "
                    "Revisar documentación."
                ),
                "url": "https://example.com/remate-portales-adjudicado",
            },
            {
                "title": "Casa en remate con cesión de derechos litigiosos",
                "snippet": (
                    "Oportunidad con cesión de derechos litigiosos, "
                    "juicio en proceso y sin posesión."
                ),
                "url": "https://example.com/remate-alto-riesgo",
            },
            {
                "title": "Casa venta normal en Narvarte",
                "snippet": "Casa en venta tradicional, no remate, crédito aceptado.",
                "url": "https://example.com/casa-venta-normal",
            },
        ]

        output: list[SearchResult] = []

        for item in examples:
            url = normalize_url(item["url"])
            output.append(
                SearchResult(
                    criteria_id=criteria_id,
                    query=query,
                    title=item["title"],
                    snippet=item["snippet"],
                    url=url,
                    source_domain=domain_from_url(url),
                )
            )

        return output