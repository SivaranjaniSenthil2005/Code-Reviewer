"""LangGraph execution nodes for multi-agent code review."""

import logging
import time
from typing import Any, Dict, Optional

from app.graph.state import ReviewState
from app.agents.code_analysis_agent import run_code_analysis_agent
from app.agents.bug_agent import run_bug_agent
from app.agents.security_agent import run_security_agent
from app.agents.quality_agent import run_quality_agent
from app.agents.complexity_agent import run_complexity_agent
from app.agents.refactoring_agent import run_refactoring_agent
from app.agents.validation_agent import run_validation_agent
from app.agents.synthesizer_agent import synthesize_review_result
from app.schemas.bug import IssueFinding

logger = logging.getLogger(__name__)


async def code_analysis_node(state: ReviewState) -> Dict[str, Any]:
    """Node: Explain code functionality and architecture."""
    code = state.get("code", "")
    language = state.get("language", "unknown")
    depth = state.get("depth", "quick")
    logger.info(f"[Node: code_analysis] Running explanation for {language} ({depth})")

    try:
        output = await run_code_analysis_agent(code=code, language=language, depth=depth)
        return {"analysis_output": output}
    except Exception as exc:
        logger.error(f"[Node: code_analysis] Error: {exc}")
        errors = state.get("errors", []) + [f"code_analysis_failed: {exc}"]
        return {"analysis_output": None, "errors": errors}


async def bug_node(state: ReviewState) -> Dict[str, Any]:
    """Node: Detect functional bugs and logic errors."""
    code = state.get("code", "")
    language = state.get("language", "unknown")
    depth = state.get("depth", "quick")
    line_map = state.get("line_map")
    context = state.get("rag_context", "") or ""
    logger.info(f"[Node: bug] Running bug analysis for {language}")

    try:
        output = await run_bug_agent(
            code=code,
            language=language,
            line_map=line_map,
            depth=depth,
            context=context,
        )
        return {"bug_output": output}
    except Exception as exc:
        logger.error(f"[Node: bug] Error: {exc}")
        errors = state.get("errors", []) + [f"bug_agent_failed: {exc}"]
        return {"bug_output": None, "errors": errors}


async def security_node(state: ReviewState) -> Dict[str, Any]:
    """Node: Audit code for security vulnerabilities."""
    code = state.get("code", "")
    language = state.get("language", "unknown")
    line_map = state.get("line_map")
    context = state.get("rag_context", "") or ""
    logger.info(f"[Node: security] Running security analysis for {language}")

    try:
        output = await run_security_agent(
            code=code,
            language=language,
            line_map=line_map,
            context=context,
        )
        return {"security_output": output}
    except Exception as exc:
        logger.error(f"[Node: security] Error: {exc}")
        errors = state.get("errors", []) + [f"security_agent_failed: {exc}"]
        return {"security_output": None, "errors": errors}


async def quality_node(state: ReviewState) -> Dict[str, Any]:
    """Node: Assess readability, naming, and style standards."""
    code = state.get("code", "")
    language = state.get("language", "unknown")
    line_map = state.get("line_map")
    context = state.get("rag_context", "") or ""
    logger.info(f"[Node: quality] Running quality assessment for {language}")

    try:
        output = await run_quality_agent(
            code=code,
            language=language,
            line_map=line_map,
            context=context,
        )
        return {"quality_output": output}
    except Exception as exc:
        logger.error(f"[Node: quality] Error: {exc}")
        errors = state.get("errors", []) + [f"quality_agent_failed: {exc}"]
        return {"quality_output": None, "errors": errors}


async def complexity_node(state: ReviewState) -> Dict[str, Any]:
    """Node: Evaluate Big-O and structural complexity."""
    code = state.get("code", "")
    language = state.get("language", "unknown")
    logger.info(f"[Node: complexity] Running complexity assessment for {language}")

    try:
        output = await run_complexity_agent(code=code, language=language)
        return {"complexity_output": output}
    except Exception as exc:
        logger.error(f"[Node: complexity] Error: {exc}")
        errors = state.get("errors", []) + [f"complexity_agent_failed: {exc}"]
        return {"complexity_output": None, "errors": errors}


async def refactoring_node(state: ReviewState) -> Dict[str, Any]:
    """Node: Produce optimized refactored source code."""
    code = state.get("code", "")
    language = state.get("language", "unknown")

    # Aggregate collected issues
    collected_issues: list[IssueFinding] = []
    bug_out = state.get("bug_output")
    if bug_out and bug_out.issues:
        collected_issues.extend(bug_out.issues)
    sec_out = state.get("security_output")
    if sec_out and sec_out.vulnerabilities:
        collected_issues.extend(sec_out.vulnerabilities)
    qual_out = state.get("quality_output")
    if qual_out and qual_out.style_issues:
        collected_issues.extend(qual_out.style_issues)

    logger.info(f"[Node: refactoring] Generating refactored code for {len(collected_issues)} issue(s)")

    try:
        output = await run_refactoring_agent(code=code, language=language, issues=collected_issues)
        return {"refactoring_output": output}
    except Exception as exc:
        logger.error(f"[Node: refactoring] Error: {exc}")
        errors = state.get("errors", []) + [f"refactoring_agent_failed: {exc}"]
        return {"refactoring_output": None, "errors": errors}


async def validation_node(state: ReviewState) -> Dict[str, Any]:
    """Node: Sanity check refactored code."""
    original = state.get("code", "")
    refactor_out = state.get("refactoring_output")
    language = state.get("language", "unknown")

    if not refactor_out:
        return {"refactoring_validated": True}

    is_valid, err = await run_validation_agent(
        original_code=original,
        refactored_code=refactor_out.refactored_code,
        language=language,
    )
    return {"refactoring_validated": is_valid}


async def synthesis_node(state: ReviewState) -> Dict[str, Any]:
    """Node: Unify all agent outputs into final ReviewResult."""
    language = state.get("language", "unknown")
    original_code = state.get("raw_code") or state.get("code", "")
    review_mode = state.get("depth", "quick")

    result = synthesize_review_result(
        language=language,
        original_code=original_code,
        analysis_output=state.get("analysis_output"),
        bug_output=state.get("bug_output"),
        security_output=state.get("security_output"),
        quality_output=state.get("quality_output"),
        complexity_output=state.get("complexity_output"),
        refactoring_output=state.get("refactoring_output"),
        refactoring_validated=state.get("refactoring_validated", True),
        review_mode=review_mode,
    )
    return {"final_result": result}
