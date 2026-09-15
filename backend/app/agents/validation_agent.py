"""Validation Agent: sanity-checks refactored code syntax and behavioral intent."""

import logging
from typing import Optional
from app.services.code.validator import validate_syntax

logger = logging.getLogger(__name__)


async def run_validation_agent(
    original_code: str,
    refactored_code: str,
    language: str,
) -> tuple[bool, Optional[str]]:
    """Validate that refactored code is syntactically valid and non-empty.

    (Will be extended with LLM intent check and retry loop in Phase 10).
    Returns (is_valid: bool, error_message: Optional[str]).
    """
    if not refactored_code or not refactored_code.strip():
        return False, "Refactored code is empty."

    # 1. Syntax check
    syntax_res = validate_syntax(refactored_code, language_id=language)
    if not syntax_res.is_valid:
        err_msg = syntax_res.first_error_message() or "Syntax validation failed on refactored code."
        logger.warning(f"[validation_agent] Refactor failed syntax check: {err_msg}")
        return False, err_msg

    return True, None
