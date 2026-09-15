"""Complexity Agent: estimates Big-O time/space complexity and cyclomatic metrics."""

import logging
from typing import Optional
from app.schemas.agent_outputs import ComplexityAnalysisOutput
from app.chains.review_chains import run_complexity_chain
from app.services.llm.router import LLMRouter

logger = logging.getLogger(__name__)


async def run_complexity_agent(
    code: str,
    language: str,
    router: Optional[LLMRouter] = None,
) -> ComplexityAnalysisOutput:
    """Analyze algorithmic complexity and structural branching."""
    try:
        return await run_complexity_chain(code=code, language=language, router=router)
    except Exception as exc:
        logger.error(f"[complexity_agent] Failed: {exc}")
        return ComplexityAnalysisOutput(
            time_complexity="O(N)",
            space_complexity="O(1)",
            cyclomatic_estimate="Low",
            complexity_assessment="Complexity assessment was unavailable.",
        )
