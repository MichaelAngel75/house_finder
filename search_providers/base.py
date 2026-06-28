from __future__ import annotations

from abc import ABC, abstractmethod
from models import SearchResult


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, criteria_id: str) -> list[SearchResult]:
        pass