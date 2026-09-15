"""Programming language detection and file extension parsing service."""

import re
from typing import Optional


# Supported language definitions: name, canonical ID, file extensions, shebang patterns, keywords
LANGUAGE_DEFINITIONS = [
    {
        "id": "python",
        "name": "Python",
        "extensions": [".py", ".pyw", ".pyx", ".pxd"],
        "shebangs": [r"python", r"python3"],
        "keywords": ["def ", "import ", "from ", "class ", "elif ", "lambda ", "print(", "self.", "__init__"],
    },
    {
        "id": "javascript",
        "name": "JavaScript",
        "extensions": [".js", ".mjs", ".cjs"],
        "shebangs": [r"node"],
        "keywords": ["const ", "let ", "var ", "function ", "=>", "require(", "module.exports", "console.log"],
    },
    {
        "id": "typescript",
        "name": "TypeScript",
        "extensions": [".ts", ".tsx"],
        "shebangs": [],
        "keywords": ["interface ", "type ", ": string", ": number", ": boolean", "readonly ", "enum ", "implements "],
    },
    {
        "id": "java",
        "name": "Java",
        "extensions": [".java"],
        "shebangs": [],
        "keywords": ["public class ", "private ", "protected ", "System.out", "import java.", "void ", "throws "],
    },
    {
        "id": "go",
        "name": "Go",
        "extensions": [".go"],
        "shebangs": [],
        "keywords": ["package ", "func ", "import (", ":= ", "fmt.", "go ", "chan ", "goroutine "],
    },
    {
        "id": "cpp",
        "name": "C++",
        "extensions": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
        "shebangs": [],
        "keywords": ["#include", "std::", "cout <<", "cin >>", "nullptr", "template<", "class ", "namespace "],
    },
    {
        "id": "rust",
        "name": "Rust",
        "extensions": [".rs"],
        "shebangs": [],
        "keywords": ["fn ", "let mut ", "impl ", "use ", "pub ", "mod ", "match ", "Some(", "Result<"],
    },
    {
        "id": "csharp",
        "name": "C#",
        "extensions": [".cs"],
        "shebangs": [],
        "keywords": ["using ", "namespace ", "public class ", "Console.Write", "static void Main", "async Task"],
    },
    {
        "id": "ruby",
        "name": "Ruby",
        "extensions": [".rb"],
        "shebangs": [r"ruby"],
        "keywords": ["def ", "end", "puts ", "require ", "attr_", "class ", "do |", "yield"],
    },
    {
        "id": "php",
        "name": "PHP",
        "extensions": [".php"],
        "shebangs": [r"php"],
        "keywords": ["<?php", "echo ", "$_", "->", "function ", "namespace "],
    },
    {
        "id": "sql",
        "name": "SQL",
        "extensions": [".sql"],
        "shebangs": [],
        "keywords": ["SELECT ", "FROM ", "WHERE ", "INSERT ", "UPDATE ", "DELETE ", "CREATE TABLE"],
    },
    {
        "id": "bash",
        "name": "Bash/Shell",
        "extensions": [".sh", ".bash"],
        "shebangs": [r"bash", r"sh"],
        "keywords": ["#!/", "echo ", "if [", "fi", "for ", "done", "export "],
    },
]

# Canonical user-facing language name → internal ID map
LANGUAGE_ALIAS_MAP: dict[str, str] = {
    "python": "python", "py": "python",
    "javascript": "javascript", "js": "javascript",
    "typescript": "typescript", "ts": "typescript",
    "java": "java",
    "go": "go", "golang": "go",
    "c++": "cpp", "cpp": "cpp",
    "rust": "rust", "rs": "rust",
    "c#": "csharp", "csharp": "csharp", "cs": "csharp",
    "ruby": "ruby", "rb": "ruby",
    "php": "php",
    "sql": "sql",
    "bash": "bash", "shell": "bash", "sh": "bash",
}


def detect_language(code: str, filename: Optional[str] = None, hint: Optional[str] = None) -> dict:
    """Detect the programming language of a code snippet.

    Detection priority:
    1. User-provided `hint` (explicit override)
    2. `filename` extension match
    3. Shebang line (`#!/usr/bin/env python3`)
    4. Keyword heuristic scoring

    Returns a dict with keys:
        - "language_id": str  (e.g. "python")
        - "language_name": str (e.g. "Python")
        - "confidence": float  (0.0–1.0)
        - "method": str  (e.g. "hint", "extension", "shebang", "heuristic", "unknown")
    """
    # 1. User hint
    if hint:
        normalized_hint = hint.strip().lower()
        if normalized_hint in LANGUAGE_ALIAS_MAP:
            lang_id = LANGUAGE_ALIAS_MAP[normalized_hint]
            lang_def = _get_lang_def(lang_id)
            return {
                "language_id": lang_id,
                "language_name": lang_def["name"] if lang_def else lang_id,
                "confidence": 1.0,
                "method": "hint",
            }

    # 2. Filename extension
    if filename:
        ext = _extract_extension(filename)
        for lang_def in LANGUAGE_DEFINITIONS:
            if ext in lang_def["extensions"]:
                return {
                    "language_id": lang_def["id"],
                    "language_name": lang_def["name"],
                    "confidence": 0.95,
                    "method": "extension",
                }

    # 3. Shebang detection
    first_line = code.lstrip().split("\n")[0] if code.strip() else ""
    if first_line.startswith("#!"):
        for lang_def in LANGUAGE_DEFINITIONS:
            for shebang in lang_def["shebangs"]:
                if re.search(shebang, first_line, re.IGNORECASE):
                    return {
                        "language_id": lang_def["id"],
                        "language_name": lang_def["name"],
                        "confidence": 0.9,
                        "method": "shebang",
                    }

    # 4. Keyword heuristic scoring
    scores = _score_by_keywords(code)
    if scores:
        best_id, best_score = scores[0]
        total = sum(s for _, s in scores)
        confidence = round(best_score / total, 3) if total > 0 else 0.0
        lang_def = _get_lang_def(best_id)
        return {
            "language_id": best_id,
            "language_name": lang_def["name"] if lang_def else best_id,
            "confidence": min(confidence, 0.85),
            "method": "heuristic",
        }

    return {
        "language_id": "unknown",
        "language_name": "Unknown",
        "confidence": 0.0,
        "method": "unknown",
    }


def normalize_language_id(raw: str) -> str:
    """Normalize a user-supplied language string to its canonical internal ID."""
    normalized = raw.strip().lower()
    return LANGUAGE_ALIAS_MAP.get(normalized, normalized)


# ─── Internal helpers ────────────────────────────────────────────────────────

def _extract_extension(filename: str) -> str:
    """Extract lowercased file extension including the dot."""
    parts = filename.rsplit(".", 1)
    return f".{parts[-1].lower()}" if len(parts) > 1 else ""


def _score_by_keywords(code: str) -> list[tuple[str, int]]:
    """Score each language definition by keyword hit count."""
    scores: dict[str, int] = {}
    for lang_def in LANGUAGE_DEFINITIONS:
        count = sum(code.count(kw) for kw in lang_def["keywords"])
        if count > 0:
            scores[lang_def["id"]] = count
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _get_lang_def(lang_id: str) -> Optional[dict]:
    """Fetch language definition by ID."""
    for lang_def in LANGUAGE_DEFINITIONS:
        if lang_def["id"] == lang_id:
            return lang_def
    return None
