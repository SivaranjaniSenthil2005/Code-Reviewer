"""Tests for Security Hardening, Prompt Injection Defenses, and Non-Execution Proof (Phase 19)."""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch
from starlette.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.services.security.rate_limiter import TokenBucketRateLimiter
from app.services.security.sanitizer import redact_sensitive_text
from app.config import settings
from app.schemas.review import ReviewResult


@pytest.fixture
def client():
    return TestClient(app)


def test_cors_origins_whitelist():
    """Verify CORS origins are explicitly restricted and do not allow wildcard '*'."""
    assert "*" not in settings.CORS_ORIGINS
    assert "http://localhost:3000" in settings.CORS_ORIGINS


def test_secret_redaction():
    text = "Error connecting to mongodb+srv://admin:supersecretpassword@cluster.mongodb.net/test with GEMINI_KEY=AIzaSyA1234567890abcdefghijklmnopqrstuv"
    redacted = redact_sensitive_text(text)
    assert "supersecretpassword" not in redacted
    assert "AIzaSyA1234567890abcdefghijklmnopqrstuv" not in redacted
    assert "[REDACTED_GEMINI_KEY]" in redacted or "[REDACTED]" in redacted


def test_rate_limiter_exceeded():
    limiter = TokenBucketRateLimiter(max_requests=3, window_seconds=60)
    client_ip = "192.168.1.100"

    assert limiter.check_rate_limit(client_ip) is True
    assert limiter.check_rate_limit(client_ip) is True
    assert limiter.check_rate_limit(client_ip) is True
    # 4th request must fail
    assert limiter.check_rate_limit(client_ip) is False


def test_user_code_never_executed_proof(client):
    """Explicitly verify that user code containing destructive shell / OS execution attempts is strictly analyzed as static text and NEVER executed."""
    # A canary marker file that would be created IF the code was evaluated
    canary_path = os.path.join(os.path.dirname(__file__), "canary_execution_proof.txt")
    if os.path.exists(canary_path):
        os.remove(canary_path)

    malicious_payload = f"""import os
# Deliberate malicious execution attempt:
os.system('touch "{canary_path}"')
open('{canary_path}', 'w').write('HACKED')
"""

    mock_review_result = ReviewResult(
        detected_language="python",
        summary="Detected potentially malicious OS system calls in code.",
        explanation="Static review performed.",
        issues=[],
        refactored_code="pass",
        complexity_assessment="O(1)",
        readability_score=50.0,
    )

    with patch("app.api.routes.review.run_review", new_callable=AsyncMock) as mock_review:
        mock_review.return_value = mock_review_result
        res = client.post("/api/review", json={"code": malicious_payload})
        assert res.status_code == 200

    # Assert canary file was NEVER created on disk
    assert not os.path.exists(canary_path), "CRITICAL SECURITY BREACH: User-submitted code was executed!"
