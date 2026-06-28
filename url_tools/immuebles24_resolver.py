from __future__ import annotations

from urllib.parse import urlparse

from .generic_resolver import GenericResolver


class Immuebles24Resolver(GenericResolver):
    def can_handle(self, url: str) -> bool:
        return "inmuebles24.com" in urlparse(url).netloc.lower()

    def looks_like_detail_url(self, url: str) -> bool:
        path = urlparse(url).path.lower().rstrip("/")

        return (
            path.startswith("/propiedades/clasificado/")
            and path.endswith(".html")
        )