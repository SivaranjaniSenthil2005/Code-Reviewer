"""Code Analysis Agent: produces plain-English explanation and architecture breakdown."""

import logging
from typing import Optional
from app.schemas.agent_outputs import CodeAnalysisOutput
from app.chains.review_chains import run_explain_chain
from app.services.llm.router import LLMRouter

logger = logging.getLogger(__name__)


async def run_code_analysis_agent(
    code: str,
    language: str,
    depth: str = "quick",
    router: Optional[LLMRouter] = None,
) -> CodeAnalysisOutput:
    """Run code explanation and architectural breakdown.

    Catches exceptions gracefully to allow partial pipeline completion.
    """
    try:
        return await run_explain_chain(code=code, language=language, depth=depth, router=router)
    except Exception as exc:
        logger.error(f"[code_analysis_agent] Failed: {exc}")
        return CodeAnalysisOutput(
            explanation="Explanation unavailable due to analysis failure.",
            key_components=[],
            summary="Analysis failed.",
        )
