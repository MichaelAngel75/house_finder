from __future__ import annotations

import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from .base import PropertyUrlResolver
from .normalizer import normalize_url


DETAIL_PATTERNS = [
    r"/propiedades/clasificado/.+\.html$",
    r"/detalle/[a-zA-Z0-9-]+$",
    r"/inmuebles/.+-\d+$",
    r"/a-[^/]+/.+/\d+$",
    r"/MLM-\d+-.+_JM$",
    r"/property/.+",
    r"/propiedad/.+",
]


SEARCH_PATH_MARKERS = [
    "/s-",
    "/search",
    "/listado",
    "/casas-remates",
    "/foreclosures/for-sale",
    "/for-sale",
    "/casas-en-venta",
    "/departamentos-en-venta",
]


class GenericResolver(PropertyUrlResolver):
    def can_handle(self, url: str) -> bool:
        return True

    def resolve(self, url: str, html: str | None = None) -> list[str]:
        normalized = normalize_url(url)

        if self.looks_like_detail_url(normalized):
            return [normalized]

        if not html:
            return []

        links = self.extract_links(html, normalized)

        return links

    def looks_like_detail_url(self, url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")

        return any(
            re.search(pattern, path, re.IGNORECASE)
            for pattern in DETAIL_PATTERNS
        )

    def looks_like_search_url(self, url: str) -> bool:
        path = urlparse(url).path.lower()

        return any(marker in path for marker in SEARCH_PATH_MARKERS)

    def extract_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links: set[str] = set()

        for a in soup.find_all("a", href=True):
            full_url = normalize_url(urljoin(base_url, a["href"]))

            if self.looks_like_detail_url(full_url):
                links.add(full_url)

        return sorted(links)