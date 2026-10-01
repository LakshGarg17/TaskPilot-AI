from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

class LLMError(Exception):
    """Base error for LLM calls"""
    pass

class LLMTimeoutError(LLMError):
    """Raised when an LLM call exceeds timeout"""
    pass

class LLMInvalidJSONError(LLMError):
    """Raised when LLM fails to return valid schema JSON"""
    pass

class LLMProvider(ABC):
    @abstractmethod
    async def complete_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        timeout: float = 60.0
    ) -> str:
        """Async text completion"""
        pass

    @abstractmethod
    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.1,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """Async structured JSON completion conforming to schema or valid JSON dict"""
        pass
