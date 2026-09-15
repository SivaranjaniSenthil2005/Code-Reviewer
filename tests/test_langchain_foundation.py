"""Tests for LangChain schemas, prompts, and structured output chains."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.schemas.bug import IssueFinding, BugAnalysisResult
from app.schemas.security import SecurityFinding, SecurityAnalysisResult
from app.schemas.review import ReviewResult, ComplexityAssessment
from app.schemas.agent_outputs import (
    CodeAnalysisOutput,
    QualityAnalysisOutput,
    ComplexityAnalysisOutput,
    RefactoringOutput,
)
from app.chains.structured_runner import execute_structured_chain
from app.chains.review_chains import (
    run_explain_chain,
    run_bug_chain,
    run_security_chain,
    run_quality_chain,
    run_complexity_chain,
    run_refactoring_chain,
)
from app.prompts.templates import EXPLAIN_PROMPT, BUG_PROMPT


# ─── Schema Validation Tests ───────────────────────────────────────────────

def test_issue_finding_schema():
    finding = IssueFinding(
        line=12,
        category="bug",
        severity="high",
        description="Index out of range when list is empty",
        suggestion="Add guard check len(items) > 0",
    )
    assert finding.line == 12
    assert finding.severity == "high"
    assert finding.category == "bug"


def test_security_finding_schema():
    sec_finding = SecurityFinding(
        line=45,
        severity="critical",
        description="SQL injection vulnerability in user lookup query",
        cwe_id="CWE-89",
        owasp_category="A03:2021-Injection",
        remediation="Use parameterized queries instead of string concatenation",
    )
    assert sec_finding.cwe_id == "CWE-89"
    assert sec_finding.owasp_category == "A03:2021-Injection"
    assert sec_finding.category == "vulnerability"


def test_review_result_schema():
    result = ReviewResult(
        detected_language="python",
        summary="Code review detected 1 bug and 1 security issue.",
        explanation="This module handles user authentication.",
        issues=[
            IssueFinding(line=5, category="bug", severity="medium", description="Missing return statement"),
        ],
        refactored_code="def auth(user):\n    return True\n",
        complexity_assessment="O(1) time complexity, minimal memory overhead.",
        readability_score=85.5,
        review_mode="quick",
    )
    assert result.detected_language == "python"
    assert len(result.issues) == 1
    assert result.readability_score == 85.5
    assert result.refactoring_validated is True


# ─── Prompt Template Tests ──────────────────────────────────────────────────

def test_explain_prompt_formatting():
    messages = EXPLAIN_PROMPT.format_messages(code="x = 1", language="python", depth="quick")
    assert len(messages) == 2
    assert "x = 1" in messages[1].content
    assert "python" in messages[1].content


def test_bug_prompt_formatting():
    messages = BUG_PROMPT.format_messages(
        numbered_code="1: def foo():\n2:     pass",
        language="python",
        depth="deep",
        context_section="\nOWASP Best Practices\n",
    )
    assert len(messages) == 2
    assert "1: def foo():" in messages[1].content
    assert "OWASP Best Practices" in messages[1].content


# ─── Chain Execution & Structured Parsing Tests ─────────────────────────────

@pytest.mark.asyncio
async def test_structured_chain_valid_output():
    mock_router = AsyncMock()
    mock_output = CodeAnalysisOutput(
        explanation="Calculates Fibonacci numbers iteratively.",
        key_components=["fibonacci()"],
        summary="Fibonacci function",
    )
    mock_router.generate_structured.return_value = mock_output

    res = await run_explain_chain(code="def fib(n): pass", language="python", depth="quick", router=mock_router)
    assert res.explanation == "Calculates Fibonacci numbers iteratively."
    assert "fibonacci()" in res.key_components


@pytest.mark.asyncio
async def test_bug_chain_structured_output():
    mock_router = AsyncMock()
    mock_output = BugAnalysisResult(
        issues=[
            IssueFinding(line=3, category="bug", severity="high", description="Division by zero if denom is 0"),
        ],
        summary="Found 1 critical divide-by-zero bug.",
    )
    mock_router.generate_structured.return_value = mock_output

    res = await run_bug_chain("1: def div(a, b):\n2:   return a / b", language="python", router=mock_router)
    assert len(res.issues) == 1
    assert res.issues[0].line == 3
    assert res.issues[0].severity == "high"


@pytest.mark.asyncio
async def test_malformed_output_retry_then_succeeds():
    mock_router = AsyncMock()
    # First attempt fails with ValueError (malformed json), retry succeed with structured output
    mock_corrected_output = QualityAnalysisOutput(
        readability_score=90.0,
        style_issues=[],
        maintainability_notes="Clean and concise code.",
    )
    mock_router.generate_structured.side_effect = [
        ValueError("Malformed JSON response"),
        mock_corrected_output,
    ]
    mock_router.generate.return_value = "{ invalid json text }"

    res = await run_quality_chain("1: def bar(): return 42", language="python", router=mock_router)
    assert res.readability_score == 90.0
    assert mock_router.generate_structured.call_count == 2
    assert mock_router.generate.call_count == 1


@pytest.mark.asyncio
async def test_malformed_output_retry_then_fails_cleanly():
    mock_router = AsyncMock()
    # Both initial and retry fail
    mock_router.generate_structured.side_effect = [
        ValueError("Malformed JSON 1"),
        ValueError("Malformed JSON 2"),
    ]
    mock_router.generate.return_value = "{ still broken json }"

    with pytest.raises(ValueError):
        await run_complexity_chain("def foo(): pass", language="python", router=mock_router)
