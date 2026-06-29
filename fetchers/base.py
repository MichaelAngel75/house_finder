from __future__ import annotations

from abc import ABC, abstractmethod

from models import PageContent


class PageFetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> PageContent:
        pass