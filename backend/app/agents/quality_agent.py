"""Quality Agent: evaluates clean code standards, style issues, and readability score."""

import logging
from typing import Optional
from app.schemas.agent_outputs import QualityAnalysisOutput
from app.schemas.bug import IssueFinding
from app.chains.review_chains import run_quality_chain
from app.agents.bug_agent import format_numbered_code
from app.services.code.line_mapper import LineMap, remap_finding_line
from app.services.llm.router import LLMRouter

logger = logging.getLogger(__name__)


async def run_quality_agent(
    code: str,
    language: str,
    line_map: Optional[LineMap] = None,
    context: str = "",
    router: Optional[LLMRouter] = None,
) -> QualityAnalysisOutput:
    """Evaluate code cleanliness, standards compliance, and readability scoring."""
    try:
        numbered_code = format_numbered_code(code)
        raw_result = await run_quality_chain(
            numbered_code=numbered_code,
            language=language,
            context=context,
            router=router,
        )

        if line_map:
            remapped_issues = []
            for issue in raw_result.style_issues:
                if issue.line is not None:
                    orig_line = remap_finding_line(issue.line, line_map, direction="norm_to_orig")
                    remapped_issues.append(issue.model_copy(update={"line": orig_line}))
                else:
                    remapped_issues.append(issue)
            return QualityAnalysisOutput(
                readability_score=raw_result.readability_score,
                style_issues=remapped_issues,
                maintainability_notes=raw_result.maintainability_notes,
            )

        return raw_result
    except Exception as exc:
        logger.error(f"[quality_agent] Failed: {exc}")
        return QualityAnalysisOutput(
            readability_score=70.0,
            style_issues=[],
            maintainability_notes="Quality analysis was unavailable.",
        )
