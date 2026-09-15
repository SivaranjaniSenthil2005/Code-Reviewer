"""Tests for code services: language detection, syntax validation, normalizer, and line mapper."""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.code.language_detector import detect_language, normalize_language_id
from app.services.code.validator import validate_syntax, validate_code_input
from app.services.code.normalizer import normalize_code, truncate_to_limit, estimate_line_count
from app.services.code.line_mapper import build_line_map, remap_finding_line, remap_findings


# ─── Language Detector Tests ────────────────────────────────────────────────

class TestLanguageDetector:

    def test_detect_python_by_hint(self):
        result = detect_language("print('hello')", hint="python")
        assert result["language_id"] == "python"
        assert result["confidence"] == 1.0
        assert result["method"] == "hint"

    def test_detect_python_by_extension(self):
        result = detect_language("x = 1", filename="main.py")
        assert result["language_id"] == "python"
        assert result["method"] == "extension"

    def test_detect_javascript_by_extension(self):
        result = detect_language("const x = 1;", filename="app.js")
        assert result["language_id"] == "javascript"
        assert result["method"] == "extension"

    def test_detect_typescript_by_extension(self):
        result = detect_language("const x: number = 1;", filename="app.ts")
        assert result["language_id"] == "typescript"

    def test_detect_python_by_shebang(self):
        code = "#!/usr/bin/env python3\nprint('hello')"
        result = detect_language(code)
        assert result["language_id"] == "python"
        assert result["method"] == "shebang"

    def test_detect_python_by_heuristic(self):
        code = "def foo():\n    return self.value\nimport os\nfrom pathlib import Path"
        result = detect_language(code)
        assert result["language_id"] == "python"
        assert result["method"] == "heuristic"

    def test_detect_unknown_for_empty_code(self):
        result = detect_language("", hint=None)
        assert result["language_id"] == "unknown"

    def test_hint_overrides_extension(self):
        # Even if file says .js, explicit hint wins
        result = detect_language("def foo(): pass", filename="foo.js", hint="python")
        assert result["language_id"] == "python"
        assert result["method"] == "hint"

    def test_normalize_alias(self):
        assert normalize_language_id("py") == "python"
        assert normalize_language_id("JS") == "javascript"
        assert normalize_language_id("golang") == "go"
        assert normalize_language_id("csharp") == "csharp"


# ─── Validator Tests ────────────────────────────────────────────────────────

class TestValidator:

    def test_valid_python_code(self):
        code = "def add(a, b):\n    return a + b\n"
        result = validate_syntax(code, "python")
        assert result.is_valid is True
        assert result.errors == []

    def test_invalid_python_syntax(self):
        code = "def foo(\n    return 1\n"
        result = validate_syntax(code, "python")
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert result.errors[0]["line"] is not None

    def test_empty_code_fails(self):
        result = validate_syntax("", "python")
        assert result.is_valid is False
        assert "empty" in result.errors[0]["message"].lower()

    def test_balanced_js_brackets(self):
        code = "function foo() { const x = [1, 2]; return x; }"
        result = validate_syntax(code, "javascript")
        assert result.is_valid is True

    def test_unbalanced_js_brackets(self):
        code = "function foo() { const x = [1, 2; return x; }"
        result = validate_syntax(code, "javascript")
        assert result.is_valid is False

    def test_generic_language_passes(self):
        result = validate_syntax("SELECT * FROM users;", "sql")
        assert result.is_valid is True
        assert result.warning is not None

    def test_empty_js_fails(self):
        result = validate_syntax("   ", "javascript")
        assert result.is_valid is False

    def test_validate_code_input_normal_python(self):
        ok, err = validate_code_input("def greet(name):\n    return f'Hello {name}'")
        assert ok is True
        assert err is None

    def test_validate_code_input_normal_javascript(self):
        ok, err = validate_code_input("const sum = (a, b) => a + b;")
        assert ok is True
        assert err is None

    def test_validate_code_input_normal_java(self):
        ok, err = validate_code_input("public class Main { public static void main(String[] args) { System.out.println(1); } }")
        assert ok is True
        assert err is None

    def test_validate_code_input_empty_rejected(self):
        ok, err = validate_code_input("   \n\t  ")
        assert ok is False
        assert "empty" in err.lower()

    def test_validate_code_input_plain_prose_rejected(self):
        prose = "Yesterday I went to the park and saw many birds singing in the trees and people walking around enjoying the sunny weather."
        ok, err = validate_code_input(prose)
        assert ok is False
        assert "prose" in err.lower()

    def test_validate_code_input_oversized_rejected(self):
        huge_code = "x = 1\n" * 3000
        ok, err = validate_code_input(huge_code, max_lines=2000)
        assert ok is False
        assert "line count" in err.lower()


# ─── Normalizer Tests ────────────────────────────────────────────────────────

class TestNormalizer:

    def test_crlf_normalized_to_lf(self):
        code = "line1\r\nline2\r\nline3"
        result = normalize_code(code, "python")
        assert "\r" not in result.normalized_code
        assert "normalized_line_endings_to_LF" in result.changes_made

    def test_trailing_whitespace_stripped(self):
        code = "x = 1   \ny = 2  \n"
        result = normalize_code(code, "python")
        for line in result.normalized_code.split("\n"):
            assert line == line.rstrip()
        assert "stripped_trailing_whitespace" in result.changes_made

    def test_python_tabs_to_spaces(self):
        code = "def foo():\n\treturn 1\n"
        result = normalize_code(code, "python")
        assert "\t" not in result.normalized_code
        assert "    " in result.normalized_code
        assert "python_tabs_converted_to_4_spaces" in result.changes_made

    def test_no_tab_conversion_for_js(self):
        code = "function foo() {\n\treturn 1;\n}"
        result = normalize_code(code, "javascript")
        # JS tabs are kept as-is
        assert "python_tabs_converted_to_4_spaces" not in result.changes_made

    def test_trailing_newline_ensured(self):
        result = normalize_code("x = 1", "python")
        assert result.normalized_code.endswith("\n")

    def test_excessive_blank_lines_collapsed(self):
        code = "x = 1\n\n\n\n\ny = 2\n"
        result = normalize_code(code, "python")
        assert "\n\n\n" not in result.normalized_code
        assert "collapsed_excessive_blank_lines" in result.changes_made

    def test_no_changes_on_clean_code(self):
        code = "def foo():\n    return 1\n"
        result = normalize_code(code, "python")
        assert result.changes_made == []

    def test_estimate_line_count(self):
        code = "x = 1\n\ny = 2\n   \nz = 3\n"
        count = estimate_line_count(code)
        assert count == 3

    def test_truncate_to_limit_by_lines(self):
        code = "\n".join(f"line_{i}" for i in range(3000))
        truncated, was_truncated = truncate_to_limit(code, max_lines=100)
        assert was_truncated is True
        assert "TRUNCATED" in truncated

    def test_no_truncation_on_short_code(self):
        code = "x = 1\ny = 2\n"
        result, was_truncated = truncate_to_limit(code)
        assert was_truncated is False
        assert result == code


# ─── Line Mapper Tests ────────────────────────────────────────────────────────

class TestLineMapper:

    def test_identity_map_identical_code(self):
        code = "x = 1\ny = 2\nz = 3\n"
        line_map = build_line_map(code, code)
        assert line_map.original_to_normalized(1) == 1
        assert line_map.original_to_normalized(2) == 2
        assert line_map.normalized_to_original(3) == 3

    def test_remap_finding_line_norm_to_orig(self):
        original = "x = 1\n\n\ny = 2\n"
        normalized = "x = 1\n\ny = 2\n"
        line_map = build_line_map(original, normalized)
        # y = 2 is on line 4 of original, line 3 of normalized
        norm_line_y = line_map.original_to_normalized(4)
        assert norm_line_y is not None
        remapped_back = remap_finding_line(norm_line_y, line_map, direction="norm_to_orig")
        assert remapped_back == 4

    def test_remap_findings_bulk(self):
        code = "a = 1\nb = 2\nc = 3\n"
        line_map = build_line_map(code, code)
        findings = [
            {"line": 1, "severity": "HIGH", "description": "Issue on a"},
            {"line": 3, "severity": "LOW", "description": "Issue on c"},
        ]
        remapped = remap_findings(findings, line_map, direction="norm_to_orig")
        assert remapped[0]["line"] == 1
        assert remapped[1]["line"] == 3

    def test_context_window(self):
        code = "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\n"
        line_map = build_line_map(code, code)
        context = line_map.get_context_window(3, window=1)
        orig_lines = [e.original_line for e in context]
        assert 2 in orig_lines
        assert 3 in orig_lines
        assert 4 in orig_lines

    def test_line_index_dict(self):
        code = "first_line\nsecond_line\nthird_line"
        line_map = build_line_map(code, code)
        idx = line_map.to_line_index()
        assert idx[1] == "first_line"
        assert idx[2] == "second_line"
        assert idx[3] == "third_line"
        assert line_map.get_line_text(2) == "second_line"
