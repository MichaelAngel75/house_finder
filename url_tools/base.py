from __future__ import annotations

from abc import ABC, abstractmethod


class PropertyUrlResolver(ABC):
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        pass

    @abstractmethod
    def resolve(self, url: str, html: str | None = None) -> list[str]:
        pass