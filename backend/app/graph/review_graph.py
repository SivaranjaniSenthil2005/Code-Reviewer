"""Review graph compilation and execution entrypoint."""

import logging
from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, START, END

from app.graph.state import ReviewState
from app.graph.nodes import (
    code_analysis_node,
    bug_node,
    security_node,
    quality_node,
    complexity_node,
    refactoring_node,
    validation_node,
    synthesis_node,
)
from app.schemas.review import ReviewResult
from app.repositories.review_repository import ReviewRepository
from app.repositories.finding_repository import FindingRepository
from app.repositories.agent_run_repository import AgentRunRepository
from app.database.client import get_database

logger = logging.getLogger(__name__)


def build_review_graph() -> StateGraph:
    """Build and compile the LangGraph workflow."""
    builder = StateGraph(ReviewState)

    # Register all nodes
    builder.add_node("code_analysis", code_analysis_node)
    builder.add_node("bug", bug_node)
    builder.add_node("security", security_node)
    builder.add_node("quality", quality_node)
    builder.add_node("complexity", complexity_node)
    builder.add_node("refactoring", refactoring_node)
    builder.add_node("validation", validation_node)
    builder.add_node("synthesis", synthesis_node)

    # Define Graph flow
    builder.add_edge(START, "code_analysis")
    builder.add_edge("code_analysis", "bug")
    builder.add_edge("code_analysis", "security")
    builder.add_edge("code_analysis", "quality")
    builder.add_edge("code_analysis", "complexity")

    builder.add_edge(["bug", "security", "quality", "complexity"], "refactoring")
    builder.add_edge("refactoring", "validation")
    builder.add_edge("validation", "synthesis")
    builder.add_edge("synthesis", END)

    return builder.compile()


from app.graph.quick_review import get_quick_review_graph
from app.graph.deep_review import get_deep_review_graph


def get_review_graph(depth: str = "quick"):
    """Get the appropriate compiled graph based on review depth."""
    if depth.lower() == "deep":
        return get_deep_review_graph()
    return get_quick_review_graph()


async def run_review(state: ReviewState, persist: bool = False) -> ReviewResult:
    """Execute the appropriate LangGraph review workflow for the provided state."""
    depth = state.get("depth", "quick")
    graph = get_review_graph(depth=depth)
    final_state = await graph.ainvoke(state)
    result: ReviewResult = final_state.get("final_result")

    if persist:
        await persist_review_state(final_state, result)

    return result


async def persist_review_state(state: Dict[str, Any], result: ReviewResult) -> Optional[str]:
    """Persist the review results and individual findings into MongoDB."""
    try:
        db = get_database()
        if db is None:
            return None

        review_repo = ReviewRepository(db)
        finding_repo = FindingRepository(db)

        # 1. Create review record
        review_doc = {
            "raw_code": state.get("raw_code", ""),
            "language": state.get("language", "unknown"),
            "depth": state.get("depth", "quick"),
            "summary": result.summary,
            "explanation": result.explanation,
            "refactored_code": result.refactored_code,
            "refactoring_notes": result.refactoring_notes,
            "refactoring_validated": result.refactoring_validated,
            "complexity_assessment": result.complexity_assessment,
            "readability_score": result.readability_score,
            "user_id": state.get("user_id"),
            "repo_name": state.get("repo_name"),
            "file_path": state.get("file_path"),
            "issues_count": len(result.issues),
        }
        review_id = await review_repo.create_review(review_doc)

        # 2. Bulk insert findings
        if result.issues:
            finding_docs = [
                {
                    "review_id": review_id,
                    "line": issue.line,
                    "category": issue.category,
                    "severity": issue.severity,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                }
                for issue in result.issues
            ]
            await finding_repo.create_findings(finding_docs)

        return review_id
    except Exception as exc:
        logger.warning(f"[review_graph] Failed to persist review to MongoDB (non-fatal): {exc}")
        return None
