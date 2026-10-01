from abc import ABC, abstractmethod
from typing import List, Dict, Any

class SearchError(Exception):
    pass

class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Execute search query.
        Returns a list of dicts:
        [{"title": str, "url": str, "domain": str, "snippet": str}]
        """
        pass
