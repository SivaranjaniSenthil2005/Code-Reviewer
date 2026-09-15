"""Synthesizer Agent: deduplicates findings and merges all agent outputs into a canonical ReviewResult."""

import logging
from typing import Optional
from app.schemas.review import ReviewResult
from app.schemas.bug import IssueFinding, BugAnalysisResult
from app.schemas.security import SecurityAnalysisResult, SecurityFinding
from app.schemas.agent_outputs import (
    CodeAnalysisOutput,
    QualityAnalysisOutput,
    ComplexityAnalysisOutput,
    RefactoringOutput,
)

logger = logging.getLogger(__name__)

SEVERITY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


def deduplicate_findings(findings: list[IssueFinding]) -> list[IssueFinding]:
    """Deduplicate findings from different agents occurring on the same line.

    If two findings occur on the same line and have similar keywords or descriptions,
    the finding with the higher severity is preserved.
    """
    if not findings:
        return []

    # Separate findings with line numbers and file-wide findings
    line_grouped: dict[int, list[IssueFinding]] = {}
    file_wide: list[IssueFinding] = []

    for f in findings:
        if f.line is not None:
            line_grouped.setdefault(f.line, []).append(f)
        else:
            file_wide.append(f)

    deduped: list[IssueFinding] = []

    for line_no, group in line_grouped.items():
        if len(group) == 1:
            deduped.append(group[0])
            continue

        # Sort by severity descending
        sorted_group = sorted(
            group,
            key=lambda x: SEVERITY_RANK.get(x.severity.lower(), 1),
            reverse=True,
        )

        seen_words: list[set[str]] = []
        for candidate in sorted_group:
            candidate_words = set(candidate.description.lower().split())
            is_dup = False
            for prev_words in seen_words:
                overlap = len(candidate_words.intersection(prev_words))
                if overlap >= 3 or (len(candidate_words) > 0 and overlap / len(candidate_words) > 0.5):
                    is_dup = True
                    break
            if not is_dup:
                deduped.append(candidate)
                seen_words.append(candidate_words)

    deduped.extend(file_wide)
    # Return sorted by line number (None at end)
    return sorted(deduped, key=lambda x: (x.line is None, x.line or 0))


def synthesize_review_result(
    language: str,
    original_code: str,
    analysis_output: Optional[CodeAnalysisOutput] = None,
    bug_output: Optional[BugAnalysisResult] = None,
    security_output: Optional[SecurityAnalysisResult] = None,
    quality_output: Optional[QualityAnalysisOutput] = None,
    complexity_output: Optional[ComplexityAnalysisOutput] = None,
    refactoring_output: Optional[RefactoringOutput] = None,
    refactoring_validated: bool = True,
    review_mode: str = "quick",
) -> ReviewResult:
    """Merge and unify all agent outputs into a canonical ReviewResult."""
    # 1. Collect all raw findings
    all_findings: list[IssueFinding] = []

    if bug_output and bug_output.issues:
        all_findings.extend(bug_output.issues)

    if security_output and security_output.vulnerabilities:
        all_findings.extend(security_output.vulnerabilities)

    if quality_output and quality_output.style_issues:
        all_findings.extend(quality_output.style_issues)

    # 2. Deduplicate findings
    unified_issues = deduplicate_findings(all_findings)

    # 3. Formulate executive summary
    issue_count = len(unified_issues)
    critical_count = sum(1 for i in unified_issues if i.severity == "critical")
    high_count = sum(1 for i in unified_issues if i.severity == "high")

    analysis_sum = analysis_output.summary if analysis_output and analysis_output.summary else ""
    summary_parts = [
        f"Review completed in {review_mode.upper()} mode.",
        analysis_sum,
        f"Identified {issue_count} total issue(s) ({critical_count} critical, {high_count} high).",
    ]
    summary = " ".join(p for p in summary_parts if p)

    explanation = analysis_output.explanation if analysis_output else "Explanation not available."
    refactored_code = refactoring_output.refactored_code if refactoring_output else original_code
    refactoring_notes = refactoring_output.changes_summary if refactoring_output else None
    complexity_text = (
        complexity_output.complexity_assessment
        if complexity_output
        else "Complexity assessment unavailable."
    )
    readability_score = quality_output.readability_score if quality_output else 75.0

    return ReviewResult(
        detected_language=language,
        summary=summary,
        explanation=explanation,
        issues=unified_issues,
        refactored_code=refactored_code,
        refactoring_notes=refactoring_notes,
        refactoring_validated=refactoring_validated,
        complexity_assessment=complexity_text,
        readability_score=readability_score,
        review_mode=review_mode,
    )
