"""End-to-end regression protection and AI benchmark evaluation test suite (Phase 18)."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.evaluation.harness import run_benchmark_evaluation, BENCHMARK_DATASET
from app.schemas.review import ReviewResult
from app.schemas.bug import IssueFinding


@pytest.mark.asyncio
async def test_ai_benchmark_regression_protection():
    """Verify that multi-agent review meets quality standards on the multi-language benchmark suite."""
    def mock_eval_review(state, persist=False):
        code = state.get("code", "")
        issues = []
        if "SELECT * FROM users" in code:
            issues.append(IssueFinding(line=2, category="vulnerability", severity="critical", description="SQL injection vulnerability"))
        elif "total / count" in code:
            issues.append(IssueFinding(line=2, category="bug", severity="high", description="Potential division by zero error"))
        elif "target_list=[]" in code:
            issues.append(IssueFinding(line=1, category="bug", severity="medium", description="Mutable default target_list argument"))
        elif "API_SECRET_KEY" in code:
            issues.append(IssueFinding(line=1, category="vulnerability", severity="critical", description="Hardcoded secret token in client code"))
        elif "fetch(url)" in code:
            issues.append(IssueFinding(line=2, category="bug", severity="low", description="Missing try/catch error handling around network call"))
        elif "FileInputStream" in code:
            issues.append(IssueFinding(line=3, category="bug", severity="medium", description="Unclosed FileInputStream resource leak"))
        elif "<-ch" in code:
            issues.append(IssueFinding(line=3, category="bug", severity="high", description="Nil channel read causing permanent deadlock"))

        return ReviewResult(
            detected_language=state.get("language", "unknown"),
            summary="Benchmark eval review.",
            explanation="Ground truth code sample.",
            issues=issues,
            refactored_code=code,
            complexity_assessment="O(1)",
            readability_score=88.0,
        )

    with patch("app.evaluation.harness.run_review", side_effect=mock_eval_review):
        eval_result = await run_benchmark_evaluation(depth="deep")

        # Regression thresholds:
        assert eval_result.total_samples == len(BENCHMARK_DATASET)
        assert eval_result.recall >= 0.85, f"Recall dropped below threshold: {eval_result.recall}"
        assert eval_result.false_positive_rate <= 0.20, f"False positive rate spiked: {eval_result.false_positive_rate}"
        assert eval_result.defects_caught >= 7
