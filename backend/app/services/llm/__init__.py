from app.core.config import settings
from app.services.llm.base import LLMProvider, LLMError, LLMTimeoutError, LLMInvalidJSONError
from app.services.llm.openai_provider import OpenAILLMProvider
from app.services.llm.mock_provider import MockLLMProvider

def get_llm_provider(mock: bool = None) -> LLMProvider:
    use_mock = settings.MOCK_MODE if mock is None else mock
    if use_mock:
        return MockLLMProvider()
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured and MOCK_MODE is False")
    return OpenAILLMProvider(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
