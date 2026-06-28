from search_providers.base import SearchProvider
from search_providers.mock import MockSearchProvider
from search_providers.serpapi import SerpApiSearchProvider
from search_providers.google_custom_search import GoogleCustomSearchProvider
from search_providers.bing import BingSearchProvider


def get_search_provider(name: str) -> SearchProvider:
    normalized = name.lower().strip()

    if normalized == "mock":
        return MockSearchProvider()

    if normalized == "serpapi":
        return SerpApiSearchProvider()

    if normalized in {"google", "google_custom_search", "google-cse"}:
        return GoogleCustomSearchProvider()

    if normalized == "bing":
        return BingSearchProvider()

    raise ValueError(
        f"Unknown SEARCH_PROVIDER: {name}. "
        "Use one of: mock, serpapi, google, bing."
    )

# from search_providers.base import SearchProvider
# from search_providers.mock import MockSearchProvider
# from search_providers.serpapi import SerpApiSearchProvider


# def get_search_provider(name: str) -> SearchProvider:
#     normalized = name.lower().strip()

#     if normalized == "mock":
#         return MockSearchProvider()

#     if normalized == "serpapi":
#         return SerpApiSearchProvider()

#     raise ValueError(f"Unknown SEARCH_PROVIDER: {name}")