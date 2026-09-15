# API Reference & Specification

This document details the RESTful and SSE (Server-Sent Events) API endpoints provided by the FastAPI backend service for the **AI Code Review & Refactoring Platform**.

---

## 1. Endpoints Overview

| Endpoint | Method | Description | Content-Type |
| :--- | :--- | :--- | :--- |
| `/api/v1/health` | GET | System health check & dependency status | `application/json` |
| `/api/v1/review` | POST | Submit code snippet for Quick Scan or Deep Review | `application/json` |
| `/api/v1/review/stream` | POST | Stream intermediate agent progress & final result | `text/event-stream` |
| `/api/v1/reviews/{id}` | GET | Retrieve past code review by ID | `application/json` |

---

## 2. Request & Response Payloads

### 2.1 Health Check (`GET /api/v1/health`)
**Response (200 OK)**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "llm_providers": {
    "gemini": "available",
    "mistral": "available"
  },
  "database": "connected"
}
```

### 2.2 Submit Code Review (`POST /api/v1/review`)
**Request**:
```json
{
  "code": "def divide(a, b):\n    return a / b",
  "language": "python",
  "mode": "quick"
}
```

**Response (200 OK)**: Canonical `CodeReviewResult` JSON format.

---

## 3. Server-Sent Events (SSE) Progress Stream (`POST /api/v1/review/stream`)

Streams real-time execution steps as agents execute.

**Events Emitted**:
- `event: status` -> Payload: `{"step": "language_detection", "message": "Detected Python"}`
- `event: status` -> Payload: `{"step": "bug_agent", "message": "Analyzing edge cases..."}`
- `event: complete` -> Payload: `<Full Canonical CodeReviewResult JSON>`
