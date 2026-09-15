"""Code formatting, indentation normalization, and sanitization service."""

import re
from dataclasses import dataclass


@dataclass
class NormalizationResult:
    """Result of a code normalization operation."""
    original_code: str
    normalized_code: str
    language_id: str
    changes_made: list[str]


def normalize_code(code: str, language_id: str) -> NormalizationResult:
    """Normalize code formatting and sanitize for safe LLM processing.

    Applies the following transformations in order:
    1. Strip trailing whitespace on each line
    2. Normalize mixed CRLF/CR line endings to LF
    3. Collapse >2 consecutive blank lines into 2
    4. Ensure exactly one trailing newline
    5. Language-specific: Python tabs→spaces (4-space indent)
    6. Truncate excessively long single lines (>5000 chars) with a marker
    7. Strip null bytes and other control characters
    """
    language_id = language_id.lower().strip()
    original = code
    changes: list[str] = []
    result = code

    # 1. Normalize line endings → LF
    before = result
    result = result.replace("\r\n", "\n").replace("\r", "\n")
    if result != before:
        changes.append("normalized_line_endings_to_LF")

    # 2. Strip trailing whitespace per line
    lines = result.split("\n")
    stripped_lines = [line.rstrip() for line in lines]
    if stripped_lines != lines:
        changes.append("stripped_trailing_whitespace")
    result = "\n".join(stripped_lines)

    # 3. Strip null bytes and control characters (keep \n, \t)
    before = result
    result = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", result)
    if result != before:
        changes.append("stripped_control_characters")

    # 4. Python-specific: convert tabs to 4-space indentation
    if language_id == "python":
        before = result
        result_lines = []
        for line in result.split("\n"):
            # Count leading tabs and replace
            stripped = line.lstrip("\t")
            tab_count = len(line) - len(stripped)
            if tab_count > 0:
                result_lines.append("    " * tab_count + stripped)
            else:
                result_lines.append(line)
        result = "\n".join(result_lines)
        if result != before:
            changes.append("python_tabs_converted_to_4_spaces")

    # 5. Collapse more than 2 consecutive blank lines → 2
    before = result
    result = re.sub(r"\n{3,}", "\n\n", result)
    if result != before:
        changes.append("collapsed_excessive_blank_lines")

    # 6. Truncate excessively long lines (>5000 chars) with marker
    lines = result.split("\n")
    truncated_lines = []
    line_truncated = False
    for line in lines:
        if len(line) > 5000:
            truncated_lines.append(line[:5000] + "  # [TRUNCATED: line exceeds 5000 chars]")
            line_truncated = True
        else:
            truncated_lines.append(line)
    if line_truncated:
        changes.append("truncated_oversized_lines")
    result = "\n".join(truncated_lines)

    # 7. Ensure exactly one trailing newline
    result = result.rstrip("\n") + "\n"

    return NormalizationResult(
        original_code=original,
        normalized_code=result,
        language_id=language_id,
        changes_made=changes,
    )


def estimate_line_count(code: str) -> int:
    """Count the number of non-empty lines in a code snippet."""
    return sum(1 for line in code.splitlines() if line.strip())


def truncate_to_limit(code: str, max_lines: int = 2000, max_chars: int = 100_000) -> tuple[str, bool]:
    """Truncate code to the configured line and character limits.

    Returns: (truncated_code, was_truncated)
    """
    lines = code.splitlines(keepends=True)

    truncated = False
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append(f"\n# [TRUNCATED: exceeded {max_lines} line limit]\n")
        truncated = True

    result = "".join(lines)

    if len(result) > max_chars:
        result = result[:max_chars] + f"\n# [TRUNCATED: exceeded {max_chars} character limit]\n"
        truncated = True

    return result, truncated
