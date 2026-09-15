"""Bug Agent: detects functional, logical, and edge-case defects with exact line mapping."""

import logging
from typing import Optional
from app.schemas.bug import BugAnalysisResult, IssueFinding
from app.chains.review_chains import run_bug_chain
from app.services.code.line_mapper import LineMap, remap_finding_line
from app.services.llm.router import LLMRouter

logger = logging.getLogger(__name__)


def format_numbered_code(code: str) -> str:
    """Format code with 1-based line numbers for LLM prompts."""
    lines = code.splitlines()
    return "\n".join(f"{idx}: {line}" for idx, line in enumerate(lines, start=1))


async def run_bug_agent(
    code: str,
    language: str,
    line_map: Optional[LineMap] = None,
    depth: str = "quick",
    context: str = "",
    router: Optional[LLMRouter] = None,
) -> BugAnalysisResult:
    """Identify functional bugs and remap finding line numbers to original source coordinates."""
    try:
        numbered_code = format_numbered_code(code)
        raw_result = await run_bug_chain(
            numbered_code=numbered_code,
            language=language,
            depth=depth,
            context=context,
            router=router,
        )

        # Remap lines if line_map is provided
        if line_map:
            remapped_issues = []
            for issue in raw_result.issues:
                if issue.line is not None:
                    orig_line = remap_finding_line(issue.line, line_map, direction="norm_to_orig")
                    remapped_issues.append(issue.model_copy(update={"line": orig_line}))
                else:
                    remapped_issues.append(issue)
            return BugAnalysisResult(issues=remapped_issues, summary=raw_result.summary)

        return raw_result
    except Exception as exc:
        logger.error(f"[bug_agent] Failed: {exc}")
        return BugAnalysisResult(issues=[], summary="Bug analysis was unavailable.")
