"""Quick Scan review graph configuration."""

import logging
from langgraph.graph import StateGraph, START, END

from app.graph.state import ReviewState
from app.graph.nodes import (
    code_analysis_node,
    bug_node,
    complexity_node,
    refactoring_node,
    validation_node,
    synthesis_node,
)

logger = logging.getLogger(__name__)


def build_quick_review_graph() -> StateGraph:
    """Build the lightweight, fast Quick Scan review workflow.

    Workflow: START -> code_analysis -> bug -> complexity -> refactoring -> validation -> synthesis -> END
    Omits RAG retrieval, security audits, and style linters for sub-second / minimal latency.
    """
    builder = StateGraph(ReviewState)

    builder.add_node("code_analysis", code_analysis_node)
    builder.add_node("bug", bug_node)
    builder.add_node("complexity", complexity_node)
    builder.add_node("refactoring", refactoring_node)
    builder.add_node("validation", validation_node)
    builder.add_node("synthesis", synthesis_node)

    builder.add_edge(START, "code_analysis")
    builder.add_edge("code_analysis", "bug")
    builder.add_edge("bug", "complexity")
    builder.add_edge("complexity", "refactoring")
    builder.add_edge("refactoring", "validation")
    builder.add_edge("validation", "synthesis")
    builder.add_edge("synthesis", END)

    return builder.compile()


_quick_graph = None


def get_quick_review_graph():
    """Get compiled singleton Quick Scan graph."""
    global _quick_graph
    if _quick_graph is None:
        _quick_graph = build_quick_review_graph()
    return _quick_graph
