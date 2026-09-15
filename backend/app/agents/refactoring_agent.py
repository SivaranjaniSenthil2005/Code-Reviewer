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
