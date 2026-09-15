"""Abstract LLM provider interface and base class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""

    def __init__(self, provider_name: str, message: str, original_error: Optional[Exception] = None):
        self.provider_name = provider_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{provider_name}] {message}")


class MissingAPIKeyError(LLMProviderError):
    """Raised when an API key is missing or empty."""
    pass


class BaseLLMProvider(ABC):
    """Abstract base class defining the contract for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name identifier of the LLM provider (e.g., 'gemini', 'mistral')."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        """Generate a raw text response asynchronously from the LLM provider."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> T:
        """Generate a validated structured Pydantic object asynchronously from the LLM provider."""
        pass
