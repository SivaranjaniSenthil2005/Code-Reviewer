# API Reference Specification

Base URL: `http://localhost:8000` (or production configured domain).

---

## 1. Endpoints

### `POST /api/review`
Submit source code for automated multi-agent review and refactoring.

#### Request Body (`application/json`)
```json
{
  "code": "def divide(a, b):\n    return a / b\n",
  "language_hint": "python",
  "depth": "quick",
  "user_id": "optional-user-id",
  "repo_name": "optional-repo",
  "file_path": "math_utils.py"
}
```

#### Response (`application/json` - HTTP 200)
```json
{
  "review_id": "65f2a1b9c3e4d50012a4b876",
  "detected_language": "python",
  "summary": "Review completed in QUICK mode. Identified 1 total issue(s).",
  "explanation": "Defines a division helper function.",
  "issues": [
    {
      "line": 2,
      "category": "bug",
      "severity": "high",
      "description": "Potential division by zero when b is 0.",
      "suggestion": "Check that b != 0 before dividing."
    }
  ],
  "refactored_code": "def divide(a: float, b: float) -> float:\n    if b == 0:\n        raise ValueError('Divisor cannot be zero')\n    return a / b\n",
  "refactoring_notes": "Added divisor validation guard check.",
  "refactoring_validated": true,
  "complexity_assessment": "O(1) time complexity, O(1) space complexity.",
  "readability_score": 92.5,
  "review_mode": "quick",
  "processing_time_ms": 1240.5,
  "status": "completed"
}
```

#### Error Responses
- **400 Bad Request**: Empty code or plain prose text rejected.
- **413 Payload Too Large**: Code exceeds character or line limit.
- **429 Too Many Requests**: Client IP exceeded rate limit threshold.
- **502 Bad Gateway**: AI providers (Gemini & Mistral) temporarily unreachable.
- **500 Internal Server Error**: Unexpected unhandled exception.

---

### `GET /api/review/{review_id}`
Fetch a previously saved review and its attached findings.

---

### `GET /health`
System health probe verifying service status and database connectivity.
