"""Source code syntax validation and parsing service."""

import ast
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a syntax validation check."""
    is_valid: bool
    language_id: str
    errors: list[dict] = field(default_factory=list)
    warning: Optional[str] = None

    def first_error_message(self) -> Optional[str]:
        """Return the first error message if any."""
        if self.errors:
            return self.errors[0].get("message")
        return None


def validate_syntax(code: str, language_id: str) -> ValidationResult:
    """Validate the syntax of a code snippet for a given language.

    Returns a ValidationResult describing whether the code parses cleanly.
    Currently supports: python (AST), javascript/typescript, and all others as pass-through.
    """
    language_id = language_id.lower().strip()

    if language_id == "python":
        return _validate_python(code)

    if language_id in ("javascript", "typescript"):
        return _validate_js_ts(code, language_id)

    # For unsupported languages, do basic non-empty check only
    return _validate_generic(code, language_id)


def _validate_python(code: str) -> ValidationResult:
    """Validate Python source code using the built-in ast module."""
    if not code.strip():
        return ValidationResult(
            is_valid=False,
            language_id="python",
            errors=[{"line": None, "message": "Code is empty."}],
        )
    try:
        ast.parse(code)
        return ValidationResult(is_valid=True, language_id="python")
    except SyntaxError as exc:
        return ValidationResult(
            is_valid=False,
            language_id="python",
            errors=[{
                "line": exc.lineno,
                "col": exc.offset,
                "message": exc.msg,
                "text": exc.text.strip() if exc.text else None,
            }],
        )
    except Exception as exc:
        logger.warning(f"[validator] Unexpected Python parse error: {exc}")
        return ValidationResult(
            is_valid=False,
            language_id="python",
            errors=[{"line": None, "message": str(exc)}],
        )


def _validate_js_ts(code: str, language_id: str) -> ValidationResult:
    """Basic JavaScript/TypeScript validation via structural bracket balance checks.

    Deep JS/TS parsing requires a JS runtime (e.g. tree-sitter); this does a
    lightweight bracket-balance and common syntax check as a fast proxy.
    """
    if not code.strip():
        return ValidationResult(
            is_valid=False,
            language_id=language_id,
            errors=[{"line": None, "message": "Code is empty."}],
        )

    errors = _check_bracket_balance(code, language_id)
    if errors:
        return ValidationResult(is_valid=False, language_id=language_id, errors=errors)

    return ValidationResult(
        is_valid=True,
        language_id=language_id,
        warning="Deep AST validation for JS/TS requires tree-sitter (Phase 5+).",
    )


def _validate_generic(code: str, language_id: str) -> ValidationResult:
    """Generic pass-through validator for unsupported languages."""
    if not code.strip():
        return ValidationResult(
            is_valid=False,
            language_id=language_id,
            errors=[{"line": None, "message": "Code is empty."}],
        )
    return ValidationResult(
        is_valid=True,
        language_id=language_id,
        warning=f"Full AST validation for '{language_id}' is not yet implemented.",
    )


def _check_bracket_balance(code: str, language_id: str) -> list[dict]:
    """Check for unbalanced braces, brackets, and parentheses."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack: list[tuple[str, int]] = []
    in_string: Optional[str] = None
    errors = []

    lines = code.split("\n")
    for lineno, line in enumerate(lines, start=1):
        i = 0
        while i < len(line):
            ch = line[i]

            # Handle string context
            if in_string:
                if ch == "\\" and i + 1 < len(line):
                    i += 2
                    continue
                if ch == in_string:
                    in_string = None
                i += 1
                continue

            # Detect string start
            if ch in ('"', "'"):
                # Check for triple-quote
                if line[i:i+3] in ('"""', "'''"):
                    in_string = line[i:i+3]
                    i += 3
                    continue
                in_string = ch
                i += 1
                continue

            if ch in pairs:
                stack.append((pairs[ch], lineno))
            elif ch in pairs.values():
                if stack and stack[-1][0] == ch:
                    stack.pop()
                else:
                    errors.append({
                        "line": lineno,
                        "message": f"Unexpected closing bracket '{ch}' at line {lineno}.",
                    })
            i += 1

    for _, lineno in stack:
        errors.append({
            "line": lineno,
            "message": f"Unclosed opening bracket opened at line {lineno}.",
        })

    return errors
