"""Edge definitions and conditional transitions for the review graph."""

from langgraph.graph import StateGraph, END
from app.graph.router import route_by_depth, route_refactoring_validation


def attach_graph_edges(builder: StateGraph) -> None:
    """Connect nodes with appropriate sequential and conditional edges."""
    # Entrypoint routing based on review depth
    builder.add_conditional_edges(
        "entry_router",
        route_by_depth,
        {
            "quick_flow": "code_analysis",
            "deep_flow": "code_analysis",
        },
    )

    # After code analysis:
    # In quick scan: goes code_analysis -> bug -> complexity -> refactoring
    # In deep review: branches to bug, security, quality, complexity concurrently
    builder.add_edge("code_analysis", "bug")
    builder.add_edge("code_analysis", "security")
    builder.add_edge("code_analysis", "quality")
    builder.add_edge("code_analysis", "complexity")

    # Convergence into refactoring
    builder.add_edge("bug", "refactoring")
    builder.add_edge("security", "refactoring")
    builder.add_edge("quality", "refactoring")
    builder.add_edge("complexity", "refactoring")

    # Refactoring -> Validation
    builder.add_edge("refactoring", "validation")

    # Validation -> Synthesis
    builder.add_edge("validation", "synthesis")
    builder.add_edge("synthesis", END)
