"""API request and response schemas for the review endpoints."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from app.schemas.bug import IssueFinding
from app.schemas.review import ReviewResult


class ReviewRequest(BaseModel):
    """Payload for submitting a code review request."""
    code: str = Field(..., description="Raw source code snippet to review")
    language_hint: Optional[str] = Field(None, description="Optional explicit language hint (e.g. 'python', 'javascript')")
    depth: Literal["quick", "deep"] = Field("quick", description="Review depth: 'quick' or 'deep'")
    user_id: Optional[str] = Field(None, description="Optional user or session identifier")
    repo_name: Optional[str] = Field(None, description="Optional repository name")
    file_path: Optional[str] = Field(None, description="Optional source file path/name")


class ReviewResponse(BaseModel):
    """API response model containing full review results and metadata."""
    review_id: Optional[str] = Field(None, description="Persisted review UUID/ObjectId")
    detected_language: str = Field(..., description="Canonical detected programming language")
    summary: str = Field(..., description="Executive summary of the review")
    explanation: str = Field(..., description="Plain-English explanation of the code")
    issues: List[IssueFinding] = Field(default_factory=list, description="List of detected defects and suggestions")
    refactored_code: str = Field(..., description="Refactored and optimized source code")
    refactoring_notes: Optional[str] = Field(None, description="Summary of refactoring changes")
    refactoring_validated: bool = Field(True, description="Whether refactored code passed automated validation")
    complexity_assessment: str = Field(..., description="Big-O and cyclomatic complexity assessment")
    readability_score: float = Field(..., ge=0.0, le=100.0, description="Readability score between 0.0 and 100.0")
    review_mode: str = Field("quick", description="Review depth: 'quick' or 'deep'")
    processing_time_ms: float = Field(..., description="Total server processing time in milliseconds")
    status: str = Field("completed", description="Status of the review execution")


class APIErrorResponse(BaseModel):
    """Standardized user-facing error response payload."""
    error: str = Field(..., description="High-level error code or type")
    message: str = Field(..., description="User-friendly explanation of why the request failed")
    detail: Optional[str] = Field(None, description="Additional context if available")
