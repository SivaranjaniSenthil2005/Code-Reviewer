"""Deep Review comprehensive graph configuration."""

import logging
from typing import Any, Dict
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
from app.rag.pipeline import get_rag_pipeline

logger = logging.getLogger(__name__)


async def rag_enrichment_node(state: ReviewState) -> Dict[str, Any]:
    """Node: Enrich review state with domain knowledge from RAG knowledge store."""
    code = state.get("code", "")
    language = state.get("language", "unknown")
    logger.info(f"[Node: rag_enrichment] Fetching RAG context for {language}")

    try:
        pipeline = get_rag_pipeline()
        context = await pipeline.get_context_for_review(
            language=language,
            code_snippet=code,
            category="security",
            top_k=2,
        )
        return {"rag_context": context}
    except Exception as exc:
        logger.warning(f"[Node: rag_enrichment] RAG context enrichment failed: {exc}")
        return {"rag_context": ""}


def build_deep_review_graph() -> StateGraph:
    """Build the comprehensive Deep Review workflow.

    Workflow:
    START -> code_analysis -> rag_enrichment -> [bug, security, quality, complexity] in parallel
          -> refactoring -> validation -> synthesis -> END
    """
    builder = StateGraph(ReviewState)

    builder.add_node("code_analysis", code_analysis_node)
    builder.add_node("rag_enrichment", rag_enrichment_node)
    builder.add_node("bug", bug_node)
    builder.add_node("security", security_node)
    builder.add_node("quality", quality_node)
    builder.add_node("complexity", complexity_node)
    builder.add_node("refactoring", refactoring_node)
    builder.add_node("validation", validation_node)
    builder.add_node("synthesis", synthesis_node)

    # Wire Edges
    builder.add_edge(START, "code_analysis")
    builder.add_edge("code_analysis", "rag_enrichment")

    # Parallel branch from RAG enrichment to all specialized analyzers
    builder.add_edge("rag_enrichment", "bug")
    builder.add_edge("rag_enrichment", "security")
    builder.add_edge("rag_enrichment", "quality")
    builder.add_edge("rag_enrichment", "complexity")

    # Converge analyzers into refactoring
    builder.add_edge(["bug", "security", "quality", "complexity"], "refactoring")
    builder.add_edge("refactoring", "validation")
    builder.add_edge("validation", "synthesis")
    builder.add_edge("synthesis", END)

    return builder.compile()


_deep_graph = None


def get_deep_review_graph():
    """Get compiled singleton Deep Review graph."""
    global _deep_graph
    if _deep_graph is None:
        _deep_graph = build_deep_review_graph()
    return _deep_graph
