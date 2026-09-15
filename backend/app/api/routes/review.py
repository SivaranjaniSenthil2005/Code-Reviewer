"""FastAPI code review API routes."""

import time
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.schemas.api import ReviewRequest, ReviewResponse, APIErrorResponse
from app.services.code import process_code_input
from app.services.code.validator import validate_code_input, MAX_INPUT_CHARS, MAX_INPUT_LINES
from app.graph.review_graph import run_review, persist_review_state
from app.graph.review_synthesis import synthesize_and_persist_review
from app.services.llm.provider import LLMProviderError
from app.database.client import get_database
from app.repositories.review_repository import ReviewRepository
from app.repositories.finding_repository import FindingRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/review", tags=["Code Review"])


@router.post(
    "",
    response_model=ReviewResponse,
    responses={
        400: {"model": APIErrorResponse, "description": "Invalid or non-code input"},
        413: {"model": APIErrorResponse, "description": "Input code too large"},
        502: {"model": APIErrorResponse, "description": "AI provider service unavailable"},
        503: {"model": APIErrorResponse, "description": "AI provider service overloaded"},
    },
)
async def submit_code_review(payload: ReviewRequest) -> ReviewResponse:
    """Submit code for automated multi-agent analysis, bug detection, and refactoring."""
    start_time = time.perf_counter()

    # 1. Input Screening: empty, non-code prose, oversized
    is_valid_input, error_msg = validate_code_input(payload.code)
    if not is_valid_input:
        if "exceeds maximum allowed size" in (error_msg or "") or "exceeds maximum allowed line count" in (error_msg or ""):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=error_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg or "Invalid input code snippet.",
        )

    # 2. Preprocessing pipeline (normalization, language detection, line mapping)
    try:
        proc = await process_code_input(
            code=payload.code,
            language_hint=payload.language_hint,
            filename=payload.file_path,
        )
    except Exception as exc:
        logger.error(f"[API: review] Preprocessing error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to parse and normalize the submitted code.",
        )

    # 3. LangGraph Multi-Agent Orchestration
    state = {
        "raw_code": payload.code,
        "code": proc["normalized_code"],
        "language": proc["language_id"],
        "depth": payload.depth,
        "line_map": proc["line_map"],
        "user_id": payload.user_id,
        "repo_name": payload.repo_name,
        "file_path": payload.file_path,
    }

    try:
        review_result = await run_review(state, persist=False)
    except LLMProviderError as llm_exc:
        logger.error(f"[API: review] LLM provider failure: {llm_exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI review providers are temporarily unavailable. Please retry in a moment.",
        )
    except Exception as exc:
        logger.error(f"[API: review] Unexpected review execution failure: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during code analysis. Please try again.",
        )

    # 4. Persistence to MongoDB (if available)
    review_id = None
    try:
        db = get_database()
        if db is not None:
            _, review_id = await synthesize_and_persist_review(
                db=db,
                state=state,
                user_id=payload.user_id,
                repo_name=payload.repo_name,
                file_path=payload.file_path,
            )
    except Exception as exc:
        logger.warning(f"[API: review] Persistence failed gracefully: {exc}")

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return ReviewResponse(
        review_id=review_id,
        detected_language=review_result.detected_language,
        summary=review_result.summary,
        explanation=review_result.explanation,
        issues=review_result.issues,
        refactored_code=review_result.refactored_code,
        refactoring_notes=review_result.refactoring_notes,
        refactoring_validated=review_result.refactoring_validated,
        complexity_assessment=review_result.complexity_assessment,
        readability_score=review_result.readability_score,
        review_mode=review_result.review_mode,
        processing_time_ms=round(elapsed_ms, 2),
        status="completed",
    )


@router.get("/{review_id}", response_model=Dict[str, Any])
async def get_review_by_id(review_id: str) -> Dict[str, Any]:
    """Retrieve a previously persisted review by ID with its attached findings."""
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database storage is not currently available.",
        )

    review_repo = ReviewRepository(db)
    finding_repo = FindingRepository(db)

    review = await review_repo.get_by_id(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID '{review_id}' not found.",
        )

    findings = await finding_repo.list_by_review_id(review_id)
    review["issues"] = findings
    return review
