"""Routing logic and conditional edge predictors for LangGraph review graph."""

from typing import Literal
from app.graph.state import ReviewState


def route_by_depth(state: ReviewState) -> Literal["quick_flow", "deep_flow"]:
    """Determine whether to route into quick scan or deep comprehensive flow."""
    depth = state.get("depth", "quick").lower()
    if depth == "deep":
        return "deep_flow"
    return "quick_flow"


def route_refactoring_validation(state: ReviewState) -> Literal["synthesize", "retry_refactor"]:
    """Check if refactored code needs a retry or proceeds directly to synthesis."""
    validated = state.get("refactoring_validated", True)
    retry_count = state.get("refactor_retry_count", 0)

    if not validated and retry_count < 1:
        return "retry_refactor"
    return "synthesize"
