from app.core.config import settings
from app.services.search.base import SearchProvider, SearchError
from app.services.search.tavily import TavilySearchProvider
from app.services.search.mock import MockSearchProvider

def get_search_provider(mock: bool = None) -> SearchProvider:
    use_mock = settings.MOCK_MODE if mock is None else mock
    if use_mock:
        return MockSearchProvider()
    if not settings.SEARCH_API_KEY:
        raise ValueError("SEARCH_API_KEY is not configured and MOCK_MODE is False")
    return TavilySearchProvider(api_key=settings.SEARCH_API_KEY)
