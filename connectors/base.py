from abc import ABC, abstractmethod
from models import SearchCriteria, Listing


class BaseConnector(ABC):
    portal_name: str

    @abstractmethod
    def search(self, criteria: SearchCriteria) -> list[Listing]:
        pass