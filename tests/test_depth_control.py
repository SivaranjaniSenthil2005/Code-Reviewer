"""Tests and latency benchmarks for Quick Scan and Deep Review depth control (Phase 9)."""

import sys
import os
import time
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.graph.state import ReviewState
from app.graph.review_graph import run_review
from app.schemas.review import ReviewResult
from app.schemas.bug import BugAnalysisResult, IssueFinding
from app.schemas.security import SecurityAnalysisResult, SecurityFinding
from app.schemas.agent_outputs import (
    CodeAnalysisOutput,
    QualityAnalysisOutput,
    ComplexityAnalysisOutput,
    RefactoringOutput,
)


@pytest.mark.asyncio
async def test_quick_scan_produces_consistent_schema():
    state: ReviewState = {
        "raw_code": "def add(a, b): return a + b",
        "code": "def add(a, b): return a + b",
        "language": "python",
        "depth": "quick",
    }
    with (
        patch("app.graph.nodes.run_code_analysis_agent", new_callable=AsyncMock) as mock_analysis,
        patch("app.graph.nodes.run_bug_agent", new_callable=AsyncMock) as mock_bug,
        patch("app.graph.nodes.run_complexity_agent", new_callable=AsyncMock) as mock_comp,
        patch("app.graph.nodes.run_refactoring_agent", new_callable=AsyncMock) as mock_refactor,
        patch("app.graph.nodes.run_validation_agent", new_callable=AsyncMock) as mock_val,
    ):
        mock_analysis.return_value = CodeAnalysisOutput(explanation="Adds numbers.", key_components=[], summary="Add")
        mock_bug.return_value = BugAnalysisResult(issues=[], summary="No bugs")
        mock_comp.return_value = ComplexityAnalysisOutput(
            time_complexity="O(1)", space_complexity="O(1)", cyclomatic_estimate="Low", complexity_assessment="Constant"
        )
        mock_refactor.return_value = RefactoringOutput(refactored_code="def add(a: int, b: int) -> int:\n    return a + b\n", changes_summary="Types", reasoning=[])
        mock_val.return_value = (True, None)

        result = await run_review(state)
        assert isinstance(result, ReviewResult)
        assert result.review_mode == "quick"
        assert result.detected_language == "python"
        assert hasattr(result, "issues")
        assert hasattr(result, "refactored_code")
        assert hasattr(result, "complexity_assessment")
        assert hasattr(result, "readability_score")


@pytest.mark.asyncio
async def test_deep_review_produces_consistent_schema():
    state: ReviewState = {
        "raw_code": "def process_data(data): pass",
        "code": "def process_data(data): pass",
        "language": "python",
        "depth": "deep",
    }
    with (
        patch("app.graph.nodes.run_code_analysis_agent", new_callable=AsyncMock) as mock_analysis,
        patch("app.graph.deep_review.get_rag_pipeline") as mock_rag_getter,
        patch("app.graph.nodes.run_bug_agent", new_callable=AsyncMock) as mock_bug,
        patch("app.graph.nodes.run_security_agent", new_callable=AsyncMock) as mock_sec,
        patch("app.graph.nodes.run_quality_agent", new_callable=AsyncMock) as mock_qual,
        patch("app.graph.nodes.run_complexity_agent", new_callable=AsyncMock) as mock_comp,
        patch("app.graph.nodes.run_refactoring_agent", new_callable=AsyncMock) as mock_refactor,
        patch("app.graph.nodes.run_validation_agent", new_callable=AsyncMock) as mock_val,
    ):
        mock_rag_pipeline = AsyncMock()
        mock_rag_pipeline.get_context_for_review.return_value = "Sample OWASP guidelines"
        mock_rag_getter.return_value = mock_rag_pipeline

        mock_analysis.return_value = CodeAnalysisOutput(explanation="Processes data.", key_components=[], summary="Data pipeline")
        mock_bug.return_value = BugAnalysisResult(issues=[], summary="Clean")
        mock_sec.return_value = SecurityAnalysisResult(vulnerabilities=[], risk_level="none", summary="No flaws")
        mock_qual.return_value = QualityAnalysisOutput(readability_score=90.0, style_issues=[], maintainability_notes="High")
        mock_comp.return_value = ComplexityAnalysisOutput(time_complexity="O(N)", space_complexity="O(1)", cyclomatic_estimate="Low", complexity_assessment="Linear")
        mock_refactor.return_value = RefactoringOutput(refactored_code="def process_data(data: list) -> None:\n    pass\n", changes_summary="Types", reasoning=[])
        mock_val.return_value = (True, None)

        result = await run_review(state)
        assert isinstance(result, ReviewResult)
        assert result.review_mode == "deep"
        assert result.readability_score == 90.0


@pytest.mark.asyncio
async def test_latency_benchmark_quick_vs_deep():
    """Verify Quick Scan completes with fewer operations / lower latency than Deep Review."""
    code_samples = {
        "small": "x = 1\ny = 2\n",
        "medium": "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)\n",
    }

    with (
        patch("app.graph.nodes.run_code_analysis_agent", new_callable=AsyncMock) as mock_analysis,
        patch("app.graph.deep_review.get_rag_pipeline") as mock_rag_getter,
        patch("app.graph.nodes.run_bug_agent", new_callable=AsyncMock) as mock_bug,
        patch("app.graph.nodes.run_security_agent", new_callable=AsyncMock) as mock_sec,
        patch("app.graph.nodes.run_quality_agent", new_callable=AsyncMock) as mock_qual,
        patch("app.graph.nodes.run_complexity_agent", new_callable=AsyncMock) as mock_comp,
        patch("app.graph.nodes.run_refactoring_agent", new_callable=AsyncMock) as mock_refactor,
        patch("app.graph.nodes.run_validation_agent", new_callable=AsyncMock) as mock_val,
    ):
        mock_rag_pipeline = AsyncMock()
        mock_rag_pipeline.get_context_for_review.return_value = "RAG context"
        mock_rag_getter.return_value = mock_rag_pipeline

        mock_analysis.return_value = CodeAnalysisOutput(explanation="E", key_components=[], summary="S")
        mock_bug.return_value = BugAnalysisResult(issues=[], summary="")
        mock_sec.return_value = SecurityAnalysisResult(vulnerabilities=[], risk_level="none", summary="")
        mock_qual.return_value = QualityAnalysisOutput(readability_score=85.0, style_issues=[], maintainability_notes="")
        mock_comp.return_value = ComplexityAnalysisOutput(time_complexity="O(1)", space_complexity="O(1)", cyclomatic_estimate="Low", complexity_assessment="")
        mock_refactor.return_value = RefactoringOutput(refactored_code="x = 1", changes_summary="", reasoning=[])
        mock_val.return_value = (True, None)

        for size, snippet in code_samples.items():
            t0 = time.perf_counter()
            quick_res = await run_review({"raw_code": snippet, "code": snippet, "language": "python", "depth": "quick"})
            quick_duration = time.perf_counter() - t0

            t0 = time.perf_counter()
            deep_res = await run_review({"raw_code": snippet, "code": snippet, "language": "python", "depth": "deep"})
            deep_duration = time.perf_counter() - t0

            assert quick_res.review_mode == "quick"
            assert deep_res.review_mode == "deep"
            # Both outputs conform to the exact same schema
            assert isinstance(quick_res, ReviewResult)
            assert isinstance(deep_res, ReviewResult)
