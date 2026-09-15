"""Google Gemini LLM provider implementation."""

import logging
from typing import Any, Optional, Type, TypeVar
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.services.llm.provider import BaseLLMProvider, LLMProviderError, MissingAPIKeyError

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider integration using LangChain."""

    def __init__(self, api_key: Optional[str] = None, default_model: str = "gemini-2.0-flash"):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self.default_model = default_model

    @property
    def name(self) -> str:
        return "gemini"

    def _verify_api_key(self) -> None:
        if not self._api_key or self._api_key.strip() in ("", "mock_gemini_api_key", "your_gemini_api_key_here"):
            raise MissingAPIKeyError(self.name, "Gemini API key is not configured or is empty.")

    def _get_client(self, model: Optional[str] = None, temperature: float = 0.2) -> ChatGoogleGenerativeAI:
        self._verify_api_key()
        model_name = model or self.default_model
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self._api_key,
            temperature=temperature,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate raw text using Gemini model."""
        try:
            client = self._get_client(model=model, temperature=temperature)
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))

            response = await client.ainvoke(messages)
            return str(response.content)
        except MissingAPIKeyError:
            raise
        except Exception as exc:
            logger.error(f"[Gemini] Text generation failed: {exc}")
            raise LLMProviderError(self.name, f"Gemini API request failed: {exc}", original_error=exc)

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> T:
        """Generate structured Pydantic object using Gemini with_structured_output."""
        try:
            client = self._get_client(model=model, temperature=temperature)
            structured_client = client.with_structured_output(schema)

            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))

            result = await structured_client.ainvoke(messages)
            if isinstance(result, schema):
                return result
            return schema.model_validate(result)
        except MissingAPIKeyError:
            raise
        except Exception as exc:
            logger.error(f"[Gemini] Structured output generation failed: {exc}")
            raise LLMProviderError(self.name, f"Gemini structured generation failed: {exc}", original_error=exc)
