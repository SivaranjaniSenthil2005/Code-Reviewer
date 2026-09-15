"""Tests for LangGraph Orchestration (Phase 7)."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.graph.state import ReviewState
from app.graph.review_graph import build_review_graph, run_review
from app.schemas.review import ReviewResult
from app.schemas.bug import BugAnalysisResult, IssueFinding
from app.schemas.security import SecurityAnalysisResult, SecurityFinding
from app.schemas.agent_outputs import (
    CodeAnalysisOutput,
    QualityAnalysisOutput,
    ComplexityAnalysisOutput,
    RefactoringOutput,
)


@pytest.fixture
def sample_state() -> ReviewState:
    return {
        "raw_code": "def divide(a, b):\n    return a / b\n",
        "code": "def divide(a, b):\n    return a / b\n",
        "language": "python",
        "depth": "quick",
        "errors": [],
    }


@pytest.mark.asyncio
async def test_full_graph_execution_success(sample_state):
    # Mock individual agent calls
    with (
        patch("app.graph.nodes.run_code_analysis_agent", new_callable=AsyncMock) as mock_analysis,
        patch("app.graph.nodes.run_bug_agent", new_callable=AsyncMock) as mock_bug,
        patch("app.graph.nodes.run_security_agent", new_callable=AsyncMock) as mock_sec,
        patch("app.graph.nodes.run_quality_agent", new_callable=AsyncMock) as mock_qual,
        patch("app.graph.nodes.run_complexity_agent", new_callable=AsyncMock) as mock_comp,
        patch("app.graph.nodes.run_refactoring_agent", new_callable=AsyncMock) as mock_refactor,
        patch("app.graph.nodes.run_validation_agent", new_callable=AsyncMock) as mock_val,
    ):
        mock_analysis.return_value = CodeAnalysisOutput(explanation="Divides two numbers.", key_components=[], summary="Divide function")
        mock_bug.return_value = BugAnalysisResult(
            issues=[IssueFinding(line=2, category="bug", severity="high", description="Division by zero if b == 0")],
            summary="Found 1 bug",
        )
        mock_sec.return_value = SecurityAnalysisResult(vulnerabilities=[], risk_level="none", summary="No vulns")
        mock_qual.return_value = QualityAnalysisOutput(readability_score=85.0, style_issues=[], maintainability_notes="Clean")
        mock_comp.return_value = ComplexityAnalysisOutput(
            time_complexity="O(1)", space_complexity="O(1)", cyclomatic_estimate="Low", complexity_assessment="Constant time"
        )
        mock_refactor.return_value = RefactoringOutput(
            refactored_code="def divide(a, b):\n    if b == 0:\n        raise ValueError('b cannot be 0')\n    return a / b\n",
            changes_summary="Added zero divisor check",
            reasoning=["Prevents ZeroDivisionError"],
        )
        mock_val.return_value = (True, None)

        result = await run_review(sample_state, persist=False)

        assert isinstance(result, ReviewResult)
        assert result.detected_language == "python"
        assert len(result.issues) == 1
        assert result.issues[0].line == 2
        assert "zero" in result.issues[0].description.lower()
        assert "ValueError" in result.refactored_code


@pytest.mark.asyncio
async def test_graph_execution_with_node_failure_recovery(sample_state):
    # Simulate bug_agent raising an unexpected Exception, while others succeed
    with (
        patch("app.graph.nodes.run_code_analysis_agent", new_callable=AsyncMock) as mock_analysis,
        patch("app.graph.nodes.run_bug_agent", side_effect=RuntimeError("LLM API Timeout")),
        patch("app.graph.nodes.run_security_agent", new_callable=AsyncMock) as mock_sec,
        patch("app.graph.nodes.run_quality_agent", new_callable=AsyncMock) as mock_qual,
        patch("app.graph.nodes.run_complexity_agent", new_callable=AsyncMock) as mock_comp,
        patch("app.graph.nodes.run_refactoring_agent", new_callable=AsyncMock) as mock_refactor,
        patch("app.graph.nodes.run_validation_agent", new_callable=AsyncMock) as mock_val,
    ):
        mock_analysis.return_value = CodeAnalysisOutput(explanation="Divides numbers.", key_components=[], summary="Divide")
        mock_sec.return_value = SecurityAnalysisResult(vulnerabilities=[], risk_level="none", summary="None")
        mock_qual.return_value = QualityAnalysisOutput(readability_score=80.0, style_issues=[], maintainability_notes="Ok")
        mock_comp.return_value = ComplexityAnalysisOutput(
            time_complexity="O(1)", space_complexity="O(1)", cyclomatic_estimate="Low", complexity_assessment="Constant time"
        )
        mock_refactor.return_value = RefactoringOutput(
            refactored_code=sample_state["raw_code"],
            changes_summary="No refactoring",
            reasoning=[],
        )
        mock_val.return_value = (True, None)

        # Graph should NOT crash, but return a degraded-yet-complete ReviewResult
        result = await run_review(sample_state, persist=False)
        assert isinstance(result, ReviewResult)
        assert result.detected_language == "python"
        assert isinstance(result.readability_score, float)
        assert result.readability_score > 0.0
