"""Synthesis and persistence workflow: unifies agent outputs and saves full audit history."""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.schemas.review import ReviewResult
from app.schemas.bug import IssueFinding
from app.agents.synthesizer_agent import synthesize_review_result, deduplicate_findings
from app.repositories.review_repository import ReviewRepository
from app.repositories.finding_repository import FindingRepository
from app.repositories.agent_run_repository import AgentRunRepository

logger = logging.getLogger(__name__)


async def synthesize_and_persist_review(
    db: Any,
    state: Dict[str, Any],
    user_id: Optional[str] = None,
    repo_name: Optional[str] = None,
    file_path: Optional[str] = None,
) -> tuple[ReviewResult, Optional[str]]:
    """Synthesize ReviewResult from state and persist review, findings, and agent runs to database.

    Returns: (ReviewResult, review_id)
    """
    language = state.get("language", "unknown")
    original_code = state.get("raw_code") or state.get("code", "")
    review_mode = state.get("depth", "quick")

    # 1. Synthesize final ReviewResult
    result = synthesize_review_result(
        language=language,
        original_code=original_code,
        analysis_output=state.get("analysis_output"),
        bug_output=state.get("bug_output"),
        security_output=state.get("security_output"),
        quality_output=state.get("quality_output"),
        complexity_output=state.get("complexity_output"),
        refactoring_output=state.get("refactoring_output"),
        refactoring_validated=state.get("refactoring_validated", True),
        review_mode=review_mode,
    )

    if db is None:
        return result, None

    # 2. Persist to MongoDB collections
    review_id = None
    try:
        review_repo = ReviewRepository(db)
        finding_repo = FindingRepository(db)
        agent_run_repo = AgentRunRepository(db)

        # 2a. Insert Review Document
        review_doc = {
            "raw_code": original_code,
            "language": language,
            "depth": review_mode,
            "summary": result.summary,
            "explanation": result.explanation,
            "refactored_code": result.refactored_code,
            "refactoring_notes": result.refactoring_notes,
            "refactoring_validated": result.refactoring_validated,
            "complexity_assessment": result.complexity_assessment,
            "readability_score": result.readability_score,
            "user_id": user_id or state.get("user_id"),
            "repo_name": repo_name or state.get("repo_name"),
            "file_path": file_path or state.get("file_path"),
            "issues_count": len(result.issues),
        }
        created_review = await review_repo.create(review_doc)
        review_id = created_review.get("id") if created_review else None

        # 2b. Insert Findings
        if result.issues and review_id:
            finding_docs = [
                {
                    "review_id": review_id,
                    "line": issue.line,
                    "category": issue.category,
                    "severity": issue.severity,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                }
                for issue in result.issues
            ]
            await finding_repo.create_many(finding_docs)

        # 2c. Insert Agent Run Audit Logs
        agent_names = [
            ("code_analysis_agent", state.get("analysis_output")),
            ("bug_agent", state.get("bug_output")),
            ("security_agent", state.get("security_output")),
            ("quality_agent", state.get("quality_output")),
            ("complexity_agent", state.get("complexity_output")),
            ("refactoring_agent", state.get("refactoring_output")),
        ]

        if review_id:
            for name, output in agent_names:
                if output is not None:
                    await agent_run_repo.create({
                        "review_id": review_id,
                        "agent_name": name,
                        "status": "success",
                        "output_summary": getattr(output, "summary", name),
                        "created_at": datetime.now(timezone.utc),
                    })

        logger.info(f"[review_synthesis] Successfully persisted review {review_id} with {len(result.issues)} findings.")
    except Exception as exc:
        logger.warning(f"[review_synthesis] Persistence encountered error (non-blocking): {exc}")

    return result, review_id
