"""Validation Agent: performs syntax verification and structural intent preservation checks."""

import ast
import logging
import re
from typing import Optional, Set
from app.services.code.validator import validate_syntax

logger = logging.getLogger(__name__)


def extract_python_function_and_class_names(code: str) -> tuple[Set[str], Set[str]]:
    """Extract top-level and method function and class names using AST."""
    funcs = set()
    classes = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs.add(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.add(node.name)
    except Exception:
        pass
    return funcs, classes


def extract_generic_identifiers(code: str) -> Set[str]:
    """Regex-based fallback extraction of function / declaration names."""
    # Matches 'def foo', 'function foo', 'class Foo', 'const foo =', 'fn foo'
    patterns = [
        r"\b(?:def|function|fn|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\b(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=",
    ]
    ids = set()
    for pat in patterns:
        for match in re.finditer(pat, code):
            ids.add(match.group(1))
    return ids


async def run_validation_agent(
    original_code: str,
    refactored_code: str,
    language: str,
) -> tuple[bool, Optional[str]]:
    """Validate that refactored code is syntactically valid and preserves essential structural interfaces.

    Checks:
    1. Refactored code is non-empty.
    2. Syntax validity check via language AST / structural validator.
    3. Interface / signature intent check: Ensure key functions and classes defined in original are present in refactor.

    Returns: (is_valid: bool, error_message: Optional[str])
    """
    if not refactored_code or not refactored_code.strip():
        return False, "Refactored code is empty."

    # 1. Syntax Check
    syntax_res = validate_syntax(refactored_code, language_id=language)
    if not syntax_res.is_valid:
        err_msg = syntax_res.first_error_message() or "Syntax error in refactored code."
        logger.warning(f"[validation_agent] Syntax check failed: {err_msg}")
        return False, f"Syntax validation failed: {err_msg}"

    # 2. Structural Intent & Interface Check
    lang_lower = language.lower()
    if lang_lower == "python":
        orig_funcs, orig_classes = extract_python_function_and_class_names(original_code)
        ref_funcs, ref_classes = extract_python_function_and_class_names(refactored_code)

        missing_funcs = orig_funcs - ref_funcs
        missing_classes = orig_classes - ref_classes

        if missing_classes:
            return False, f"Refactored code removed class definition(s): {', '.join(missing_classes)}"

        # If original functions were defined and none of them exist in refactored code, reject
        if orig_funcs and not (orig_funcs & ref_funcs):
            return False, f"Refactored code removed all original function definitions: {', '.join(orig_funcs)}"
    else:
        # Generic identifier check
        orig_ids = extract_generic_identifiers(original_code)
        ref_ids = extract_generic_identifiers(refactored_code)
        if orig_ids and not (orig_ids & ref_ids):
            return False, f"Refactored code altered all core function/symbol signatures."

    return True, None
