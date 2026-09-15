"""Code service integration module: normalizes, detects language, validates, and maps lines."""

from typing import Optional

from app.services.code.language_detector import detect_language, normalize_language_id
from app.services.code.normalizer import normalize_code, truncate_to_limit, estimate_line_count
from app.services.code.validator import validate_syntax
from app.services.code.line_mapper import build_line_map, remap_findings


async def process_code_input(
    code: str,
    language_hint: Optional[str] = None,
    filename: Optional[str] = None,
) -> dict:
    """Full pre-processing pipeline for a submitted code snippet.

    Steps:
    1. Truncate to safe limits
    2. Detect language
    3. Normalize (whitespace, line endings, tabs, etc.)
    4. Validate syntax
    5. Build line map (original ↔ normalized)

    Returns a dict with all processed artifacts needed by agents.
    """
    from typing import Optional

    # 1. Truncate
    code_input, was_truncated = truncate_to_limit(code)

    # 2. Detect language
    lang_result = detect_language(code_input, filename=filename, hint=language_hint)
    language_id = lang_result["language_id"]

    # 3. Normalize
    norm_result = normalize_code(code_input, language_id=language_id)
    normalized_code = norm_result.normalized_code

    # 4. Validate
    validation = validate_syntax(normalized_code, language_id=language_id)

    # 5. Build line map
    line_map = build_line_map(code_input, normalized_code)

    return {
        "original_code": code_input,
        "normalized_code": normalized_code,
        "language_id": language_id,
        "language_name": lang_result["language_name"],
        "detection_confidence": lang_result["confidence"],
        "detection_method": lang_result["method"],
        "normalization_changes": norm_result.changes_made,
        "was_truncated": was_truncated,
        "line_count": estimate_line_count(normalized_code),
        "syntax_valid": validation.is_valid,
        "syntax_errors": validation.errors,
        "syntax_warning": validation.warning,
        "line_map": line_map,
    }
