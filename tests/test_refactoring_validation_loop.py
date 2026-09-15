"""Tests for Refactoring and Validation Loop (Phase 10)."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.graph.state import ReviewState
from app.graph.nodes import validation_node
from app.schemas.agent_outputs import RefactoringOutput
from app.agents.validation_agent import run_validation_agent


@pytest.mark.asyncio
async def test_validation_agent_syntax_and_structure_checks():
    orig_python = "def compute_tax(amount):\n    return amount * 0.1\n"

    # Valid refactor
    valid_refactor = "def compute_tax(amount: float) -> float:\n    \"\"\"Calculates tax amount.\"\"\"\n    return round(amount * 0.1, 2)\n"
    ok, err = await run_validation_agent(orig_python, valid_refactor, "python")
    assert ok is True
    assert err is None

    # Syntax broken refactor
    broken_syntax = "def compute_tax(amount: float) -> float\n    return amount * 0.1"
    ok, err = await run_validation_agent(orig_python, broken_syntax, "python")
    assert ok is False
    assert "syntax" in err.lower()

    # Function signature deleted refactor
    missing_func = "def some_completely_unrelated_function(): pass\n"
    ok, err = await run_validation_agent(orig_python, missing_func, "python")
    assert ok is False
    assert "function definitions" in err.lower()


@pytest.mark.asyncio
async def test_validation_node_valid_refactor_passes_without_retry():
    state: ReviewState = {
        "raw_code": "def hello(): pass",
        "language": "python",
        "refactoring_output": RefactoringOutput(
            refactored_code="def hello() -> None:\n    print('hello')\n",
            changes_summary="Added print",
            reasoning=[],
        ),
    }

    result = await validation_node(state)
    assert result.get("refactoring_validated") is True
    assert "refactor_retry_count" not in result  # No retry was needed


@pytest.mark.asyncio
async def test_validation_node_broken_refactor_triggers_retry_and_succeeds():
    state: ReviewState = {
        "raw_code": "def process(): return 1\n",
        "language": "python",
        "refactoring_output": RefactoringOutput(
            refactored_code="def process( return 1",  # Syntax error
            changes_summary="Broken refactor",
            reasoning=[],
        ),
    }

    corrected_output = RefactoringOutput(
        refactored_code="def process() -> int:\n    return 1\n",
        changes_summary="Fixed syntax",
        reasoning=[],
    )

    with patch("app.agents.refactoring_agent.run_refactoring_retry", new_callable=AsyncMock) as mock_retry:
        mock_retry.return_value = corrected_output

        result = await validation_node(state)
        assert result.get("refactoring_validated") is True
        assert result.get("refactor_retry_count") == 1
        assert "process() -> int" in result["refactoring_output"].refactored_code


@pytest.mark.asyncio
async def test_validation_node_double_failure_falls_back_safely():
    original_code = "def important_logic(): return 42\n"
    state: ReviewState = {
        "raw_code": original_code,
        "language": "python",
        "refactoring_output": RefactoringOutput(
            refactored_code="def important_logic( invalid syntax 1",
            changes_summary="Bad 1",
            reasoning=[],
        ),
    }

    still_broken_output = RefactoringOutput(
        refactored_code="def important_logic( invalid syntax 2",
        changes_summary="Bad 2",
        reasoning=[],
    )

    with patch("app.agents.refactoring_agent.run_refactoring_retry", new_callable=AsyncMock) as mock_retry:
        mock_retry.return_value = still_broken_output

        result = await validation_node(state)
        # Must fall back to original code with refactoring_validated = False
        assert result.get("refactoring_validated") is False
        assert result.get("refactor_retry_count") == 1
        assert result["refactoring_output"].refactored_code == original_code
        assert "confidently validated" in result["refactoring_output"].changes_summary
