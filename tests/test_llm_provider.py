import sys
import os
import pytest
from unittest.mock import MagicMock
from pydantic import BaseModel, Field

# Ensure backend package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.llm.provider import BaseLLMProvider, LLMProviderError, MissingAPIKeyError
from app.services.llm.gemini import GeminiProvider
from app.services.llm.mistral import MistralProvider
from app.services.llm.router import LLMRouter

pytestmark = pytest.mark.asyncio


class DummySchema(BaseModel):
    summary: str = Field(description="Summary text")
    score: int = Field(description="Numerical score")


class MockProvider(BaseLLMProvider):
    def __init__(self, provider_name: str, should_fail: bool = False, error_msg: str = "Provider error"):
        self._name = provider_name
        self.should_fail = should_fail
        self.error_msg = error_msg
        self.generate_mock = MagicMock()
        self.generate_structured_mock = MagicMock()

    @property
    def name(self) -> str:
        return self._name

    async def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        self.generate_mock(prompt=prompt, system_prompt=system_prompt, **kwargs)
        if self.should_fail:
            raise LLMProviderError(self._name, self.error_msg)
        return f"Response from {self._name}"

    async def generate_structured(self, prompt: str, schema: type, system_prompt: str = None, **kwargs):
        self.generate_structured_mock(prompt=prompt, schema=schema, system_prompt=system_prompt, **kwargs)
        if self.should_fail:
            raise LLMProviderError(self._name, self.error_msg)
        return schema(summary=f"Structured from {self._name}", score=100)


async def test_primary_success_short_circuits_fallback():
    """Verify successful Gemini call short-circuits without touching Mistral fallback."""
    primary = MockProvider("gemini", should_fail=False)
    fallback = MockProvider("mistral", should_fail=False)
    router = LLMRouter(primary_provider=primary, fallback_provider=fallback)

    result, meta = await router.generate("Test prompt")
    assert result == "Response from gemini"
    assert meta["provider_used"] == "gemini"
    assert meta["fallback_triggered"] is False
    assert meta["primary_error"] is None

    primary.generate_mock.assert_called_once()
    fallback.generate_mock.assert_not_called()


async def test_primary_failure_triggers_mistral_fallback():
    """Verify primary Gemini failure automatically triggers Mistral fallback."""
    primary = MockProvider("gemini", should_fail=True, error_msg="Gemini rate limit 429")
    fallback = MockProvider("mistral", should_fail=False)
    router = LLMRouter(primary_provider=primary, fallback_provider=fallback)

    result, meta = await router.generate("Test prompt")
    assert result == "Response from mistral"
    assert meta["provider_used"] == "mistral"
    assert meta["fallback_triggered"] is True
    assert "Gemini rate limit 429" in meta["primary_error"]

    primary.generate_mock.assert_called_once()
    fallback.generate_mock.assert_called_once()


async def test_structured_output_primary_to_fallback():
    """Verify structured output generation falls back seamlessly when primary fails."""
    primary = MockProvider("gemini", should_fail=True, error_msg="Gemini quota exceeded")
    fallback = MockProvider("mistral", should_fail=False)
    router = LLMRouter(primary_provider=primary, fallback_provider=fallback)

    obj, meta = await router.generate_structured("Extract code issues", schema=DummySchema)
    assert isinstance(obj, DummySchema)
    assert obj.summary == "Structured from mistral"
    assert obj.score == 100
    assert meta["provider_used"] == "mistral"
    assert meta["fallback_triggered"] is True


async def test_missing_api_key_fails_gracefully():
    """Verify missing/empty API key raises MissingAPIKeyError gracefully without unhandled crashes."""
    gemini = GeminiProvider(api_key="")
    with pytest.raises(MissingAPIKeyError) as exc_info:
        await gemini.generate("Hello")

    err_str = str(exc_info.value)
    assert "[gemini]" in err_str
    assert "not configured" in err_str

    mistral = MistralProvider(api_key="   ")
    with pytest.raises(MissingAPIKeyError) as exc_info_mistral:
        await mistral.generate("Hello")

    assert "[mistral]" in str(exc_info_mistral.value)


async def test_all_providers_failed_raises_router_error():
    """Verify exception when both primary and fallback providers fail."""
    primary = MockProvider("gemini", should_fail=True, error_msg="Gemini down")
    fallback = MockProvider("mistral", should_fail=True, error_msg="Mistral down")
    router = LLMRouter(primary_provider=primary, fallback_provider=fallback)

    with pytest.raises(LLMProviderError) as exc_info:
        await router.generate("Test prompt")

    err_msg = str(exc_info.value)
    assert "[router]" in err_msg
    assert "All configured LLM providers failed" in err_msg
