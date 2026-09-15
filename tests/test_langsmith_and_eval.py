"""Tests for LangSmith Tracing and Evaluation Harness (Phase 12)."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.config import setup_langsmith_tracing, settings
from app.evaluation.harness import run_benchmark_evaluation, BENCHMARK_DATASET
from app.schemas.review import ReviewResult
from app.schemas.bug import IssueFinding


def test_setup_langsmith_tracing():
    with patch.object(settings, "LANGSMITH_API_KEY", "test-langsmith-key-123"):
        enabled = setup_langsmith_tracing()
        assert enabled is True
        assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
        assert os.environ.get("LANGCHAIN_API_KEY") == "test-langsmith-key-123"


@pytest.mark.asyncio
async def test_run_benchmark_evaluation_metrics():
    # Mock review graph to return ground-truth findings
    def mock_review_side_effect(state, persist=False):
        code = state.get("code", "")
        issues = []
        if "SELECT * FROM users" in code:
            issues.append(IssueFinding(line=2, category="vulnerability", severity="critical", description="SQL injection vulnerability"))
        elif "total / count" in code:
            issues.append(IssueFinding(line=2, category="bug", severity="high", description="Potential division by zero"))
        elif "target_list=[]" in code:
            issues.append(IssueFinding(line=1, category="bug", severity="medium", description="Mutable default argument in target_list"))
        elif "API_SECRET_KEY" in code:
            issues.append(IssueFinding(line=1, category="vulnerability", severity="critical", description="Hardcoded API secret token"))

        return ReviewResult(
            detected_language="python",
            summary="Benchmark evaluation review.",
            explanation="Test code.",
            issues=issues,
            refactored_code=code,
            complexity_assessment="O(1)",
            readability_score=85.0,
        )

    with patch("app.evaluation.harness.run_review", side_effect=mock_review_side_effect):
        result = await run_benchmark_evaluation(depth="quick")
        assert result.total_samples == len(BENCHMARK_DATASET)
        assert result.recall > 0.8  # High recall on ground truth
        assert result.avg_latency_ms >= 0.0
        assert len(result.sample_details) == len(BENCHMARK_DATASET)
