import json
import asyncio
from typing import Any, Dict, Optional, Type
from openai import AsyncOpenAI, APIConnectionError, RateLimitError, APITimeoutError
from pydantic import BaseModel
from app.core.logging import logger
from app.services.llm.base import LLMProvider, LLMError, LLMTimeoutError, LLMInvalidJSONError

class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def _retry_request(self, fn, max_retries: int = 3):
        delay = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                return await fn()
            except (APITimeoutError, TimeoutError) as e:
                if attempt == max_retries:
                    raise LLMTimeoutError(f"OpenAI request timed out after {attempt} attempts: {e}")
                await asyncio.sleep(delay)
                delay *= 2
            except (RateLimitError, APIConnectionError) as e:
                if attempt == max_retries:
                    raise LLMError(f"OpenAI request failed after {attempt} retries: {e}")
                logger.warning(f"OpenAI retry {attempt}/{max_retries} after error: {e}")
                await asyncio.sleep(delay)
                delay *= 2
            except Exception as e:
                raise LLMError(f"OpenAI execution error: {e}")

    async def complete_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        timeout: float = 60.0
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async def _call():
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature
                ),
                timeout=timeout
            )
            return response.choices[0].message.content or ""

        return await self._retry_request(_call)

    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.1,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        messages = []
        sys = (system_prompt or "") + "\nYou MUST return valid RFC8259 JSON only without markdown formatting."
        messages.append({"role": "system", "content": sys})
        messages.append({"role": "user", "content": prompt})

        async def _call():
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"}
                ),
                timeout=timeout
            )
            raw = response.choices[0].message.content or "{}"
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as err:
                raise LLMInvalidJSONError(f"Invalid JSON returned by LLM: {err}. Raw: {raw[:200]}")

            if schema:
                try:
                    validated = schema.model_validate(data)
                    return validated.model_dump()
                except Exception as ve:
                    raise LLMInvalidJSONError(f"JSON validation against schema failed: {ve}")
            return data

        return await self._retry_request(_call)
