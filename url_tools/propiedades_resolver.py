from __future__ import annotations

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from .generic_resolver import GenericResolver
from .normalizer import normalize_url


class PropiedadesResolver(GenericResolver):
    def can_handle(self, url: str) -> bool:
        return "propiedades.com" in urlparse(url).netloc.lower()

    def looks_like_detail_url(self, url: str) -> bool:
        path = urlparse(url).path.lower().rstrip("/")

        return (
            path.startswith("/inmuebles/")
            and path.split("-")[-1].isdigit()
        )

    def resolve(self, url: str, html: str | None = None) -> list[str]:
        normalized = normalize_url(url)

        if self.looks_like_detail_url(normalized):
            return [normalized]

        if not html:
            return []

        return self.extract_property_links(html, normalized)

    def extract_property_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = normalize_url(urljoin(base_url, href))

            if self.looks_like_detail_url(full_url):
                links.add(full_url)

        return sorted(links)

# from __future__ import annotations

# from urllib.parse import urlparse

# from .generic_resolver import GenericResolver


# class PropiedadesResolver(GenericResolver):
#     def can_handle(self, url: str) -> bool:
#         return "propiedades.com" in urlparse(url).netloc.lower()

#     def looks_like_detail_url(self, url: str) -> bool:
#         path = urlparse(url).path.lower().rstrip("/")

#         return (
#             path.startswith("/inmuebles/")
#             and path.split("-")[-1].isdigit()
#         )