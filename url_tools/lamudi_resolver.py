from __future__ import annotations

from urllib.parse import urlparse

from .generic_resolver import GenericResolver


class LamudiResolver(GenericResolver):
    def can_handle(self, url: str) -> bool:
        return "lamudi.com.mx" in urlparse(url).netloc.lower()

    def looks_like_detail_url(self, url: str) -> bool:
        path = urlparse(url).path.lower().rstrip("/")

        return path.startswith("/detalle/") and len(path.split("/")[-1]) >= 20