"""Structured output chain execution with automatic schema correction and retry."""

import json
import logging
from typing import Any, Type, TypeVar, Optional
from pydantic import BaseModel, ValidationError

from app.services.llm.router import LLMRouter, get_llm_router
from app.prompts.templates import JSON_CORRECTION_PROMPT

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


async def execute_structured_chain(
    prompt_template: Any,
    prompt_inputs: dict[str, Any],
    schema_cls: Type[T],
    router: Optional[LLMRouter] = None,
) -> T:
    """Execute a prompt template against the LLM router and parse into a Pydantic schema.

    If output validation fails, retries ONCE using a schema correction prompt.
    If still failing, raises or returns a safe default.
    """
    if router is None:
        router = get_llm_router()

    # 1. Format the prompt
    formatted_messages = prompt_template.format_messages(**prompt_inputs)
    # Convert LangChain messages to standard prompt or run structured output
    full_prompt = "\n\n".join(f"{m.type.upper()}: {m.content}" for m in formatted_messages)

    try:
        # Attempt direct structured generation
        result = await router.generate_structured(full_prompt, schema=schema_cls)
        return result[0] if isinstance(result, tuple) else result
    except (ValidationError, json.JSONDecodeError, ValueError) as exc:
        logger.warning(
            f"[chains] Initial structured generation failed for schema {schema_cls.__name__}: {exc}. Retrying with correction..."
        )

    # 2. Retry path with explicit JSON correction
    try:
        raw_res = await router.generate(full_prompt)
        raw_fallback_text = raw_res[0] if isinstance(raw_res, tuple) else raw_res
        correction_messages = JSON_CORRECTION_PROMPT.format_messages(
            schema_json=json.dumps(schema_cls.model_json_schema(), indent=2),
            raw_output=raw_fallback_text,
            error_message="Output did not match schema or was invalid JSON.",
        )
        correction_prompt = "\n\n".join(f"{m.type.upper()}: {m.content}" for m in correction_messages)
        corrected_res = await router.generate_structured(correction_prompt, schema=schema_cls)
        return corrected_res[0] if isinstance(corrected_res, tuple) else corrected_res
    except Exception as retry_exc:
        logger.error(f"[chains] Retry correction failed for schema {schema_cls.__name__}: {retry_exc}")
        raise retry_exc
