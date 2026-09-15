"""LLM router for dynamic provider selection and automatic fallback management."""

import logging
from typing import Any, Dict, Optional, Type, TypeVar, Tuple
from pydantic import BaseModel

from app.services.llm.provider import BaseLLMProvider, LLMProviderError
from app.services.llm.gemini import GeminiProvider
from app.services.llm.mistral import MistralProvider

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMRouter:
    """Multi-provider LLM router handling automatic failover between primary and secondary providers."""

    def __init__(
        self,
        primary_provider: Optional[BaseLLMProvider] = None,
        fallback_provider: Optional[BaseLLMProvider] = None,
    ):
        self.primary_provider = primary_provider or GeminiProvider()
        self.fallback_provider = fallback_provider or MistralProvider()

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate text using primary provider, falling back to secondary provider on error.
        
        Returns a tuple: (response_text, metadata_dict).
        metadata_dict contains: {"provider_used": str, "fallback_triggered": bool, "primary_error": Optional[str]}
        """
        # Attempt Primary Provider
        try:
            logger.info(f"[LLMRouter] Attempting generation via primary provider '{self.primary_provider.name}'...")
            result = await self.primary_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                **kwargs,
            )
            return result, {
                "provider_used": self.primary_provider.name,
                "fallback_triggered": False,
                "primary_error": None,
            }
        except Exception as primary_exc:
            primary_msg = str(primary_exc)
            logger.warning(
                f"[LLMRouter] Primary provider '{self.primary_provider.name}' failed: {primary_msg}. "
                f"Failing over to fallback provider '{self.fallback_provider.name}'..."
            )

        # Attempt Fallback Provider
        try:
            result = await self.fallback_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                **kwargs,
            )
            return result, {
                "provider_used": self.fallback_provider.name,
                "fallback_triggered": True,
                "primary_error": primary_msg,
            }
        except Exception as fallback_exc:
            fallback_msg = str(fallback_exc)
            logger.error(
                f"[LLMRouter] Both primary ('{self.primary_provider.name}') and fallback "
                f"('{self.fallback_provider.name}') LLM providers failed. Fallback error: {fallback_msg}"
            )
            raise LLMProviderError(
                "router",
                f"All configured LLM providers failed. Primary error: {primary_msg}. Fallback error: {fallback_msg}",
                original_error=fallback_exc,
            )

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> Tuple[T, Dict[str, Any]]:
        """Generate structured Pydantic object with primary to fallback failover.
        
        Returns a tuple: (pydantic_object, metadata_dict).
        """
        # Attempt Primary Provider
        try:
            logger.info(
                f"[LLMRouter] Attempting structured generation via primary provider '{self.primary_provider.name}'..."
            )
            result = await self.primary_provider.generate_structured(
                prompt=prompt,
                schema=schema,
                system_prompt=system_prompt,
                temperature=temperature,
                **kwargs,
            )
            return result, {
                "provider_used": self.primary_provider.name,
                "fallback_triggered": False,
                "primary_error": None,
            }
        except Exception as primary_exc:
            primary_msg = str(primary_exc)
            logger.warning(
                f"[LLMRouter] Primary structured provider '{self.primary_provider.name}' failed: {primary_msg}. "
                f"Failing over to fallback provider '{self.fallback_provider.name}'..."
            )

        # Attempt Fallback Provider
        try:
            result = await self.fallback_provider.generate_structured(
                prompt=prompt,
                schema=schema,
                system_prompt=system_prompt,
                temperature=temperature,
                **kwargs,
            )
            return result, {
                "provider_used": self.fallback_provider.name,
                "fallback_triggered": True,
                "primary_error": primary_msg,
            }
        except Exception as fallback_exc:
            fallback_msg = str(fallback_exc)
            logger.error(
                f"[LLMRouter] Both primary and fallback structured generation failed. Fallback error: {fallback_msg}"
            )
            raise LLMProviderError(
                "router",
                f"All configured LLM providers failed structured generation. Primary error: {primary_msg}. Fallback error: {fallback_msg}",
                original_error=fallback_exc,
            )
