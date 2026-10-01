import urllib.parse
from typing import List, Dict, Any
import httpx
from app.core.logging import logger
from app.services.search.base import SearchProvider, SearchError

class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://api.tavily.com/search"

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_domains": [],
            "exclude_domains": []
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(self.endpoint, json=payload, headers=headers)
                if res.status_code != 200:
                    raise SearchError(f"Tavily search API error ({res.status_code}): {res.text}")
                data = res.json()
                results = []
                for item in data.get("results", []):
                    raw_url = item.get("url", "")
                    parsed = urllib.parse.urlparse(raw_url)
                    results.append({
                        "title": item.get("title", ""),
                        "url": raw_url,
                        "domain": parsed.netloc or "web",
                        "snippet": item.get("content", "")
                    })
                return results
        except httpx.TimeoutException:
            raise SearchError("Tavily search request timed out")
        except Exception as e:
            if isinstance(e, SearchError):
                raise
            raise SearchError(f"Failed to query Tavily search: {e}")
