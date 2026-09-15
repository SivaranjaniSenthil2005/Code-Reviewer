"""Sanitization and log masking service to prevent secret and PII leakage."""

import re

# Patterns matching sensitive keys and tokens
SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|secret|password|token|bearer|auth)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?", r"\1: [REDACTED]"),
    (r"AIza[0-9A-Za-z\-_]{35}", "[REDACTED_GEMINI_KEY]"),
    (r"sk-[a-zA-Z0-9]{32,}", "[REDACTED_API_KEY]"),
    (r"mongodb(\+srv)?:\/\/[^\s]+", "[REDACTED_MONGO_URI]"),
]


def redact_sensitive_text(text: str) -> str:
    """Mask known secret patterns, tokens, and database URIs from log strings."""
    if not text:
        return ""
    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)
    return sanitized
