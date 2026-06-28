from __future__ import annotations

from urllib.parse import urlparse

from .generic_resolver import GenericResolver


class PropiedadesResolver(GenericResolver):
    def can_handle(self, url: str) -> bool:
        return "propiedades.com" in urlparse(url).netloc.lower()

    def looks_like_detail_url(self, url: str) -> bool:
        path = urlparse(url).path.lower().rstrip("/")

        return (
            path.startswith("/inmuebles/")
            and path.split("-")[-1].isdigit()
        )