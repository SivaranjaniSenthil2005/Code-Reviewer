"""Refactoring Agent: generates clean, robust refactored code fixing detected issues."""

import logging
from typing import Optional
from app.schemas.agent_outputs import RefactoringOutput
from app.schemas.bug import IssueFinding
from app.chains.review_chains import run_refactoring_chain
from app.services.llm.router import LLMRouter

logger = logging.getLogger(__name__)


def format_issues_summary(issues: list[IssueFinding]) -> str:
    """Format a bulleted list of issues for the refactoring prompt."""
    if not issues:
        return "No specific defects flagged; optimize for clarity and idiomatic style."
    lines = []
    for issue in issues:
        line_ref = f"Line {issue.line}: " if issue.line else ""
        lines.append(f"- [{issue.severity.upper()}] {line_ref}{issue.description}")
        if issue.suggestion:
            lines.append(f"  Fix hint: {issue.suggestion}")
    return "\n".join(lines)


async def run_refactoring_agent(
    code: str,
    language: str,
    issues: list[IssueFinding],
    router: Optional[LLMRouter] = None,
) -> RefactoringOutput:
    """Produce refactored code addressing identified issues."""
    try:
        issues_summary = format_issues_summary(issues)
        return await run_refactoring_chain(
            code=code,
            language=language,
            issues_summary=issues_summary,
            router=router,
        )
    except Exception as exc:
        logger.error(f"[refactoring_agent] Failed: {exc}")
        return RefactoringOutput(
            refactored_code=code,
            changes_summary="Refactoring generation failed; returning original code.",
            reasoning=["Original code preserved."],
        )


async def run_refactoring_retry(
    original_code: str,
    language: str,
    failed_refactor: str,
    error_reason: str,
    router: Optional[LLMRouter] = None,
) -> RefactoringOutput:
    """Retry refactoring with explicit error feedback describing what failed in validation."""
    logger.info(f"[refactoring_agent] Retrying refactoring due to: {error_reason}")
    correction_instruction = (
        f"The previous refactoring attempt failed validation with error: {error_reason}.\n"
        f"Fix the syntax and preserve all original signatures and behaviors while optimizing."
    )
    try:
        return await run_refactoring_chain(
            code=original_code,
            language=language,
            issues_summary=correction_instruction,
            router=router,
        )
    except Exception as exc:
        logger.error(f"[refactoring_agent] Retry failed: {exc}")
        return RefactoringOutput(
            refactored_code=original_code,
            changes_summary="Refactoring retry failed; returning original code.",
            reasoning=["Original code preserved."],
        )
