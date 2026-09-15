"""Rate limiter implementing in-memory token bucket per client IP."""

import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """In-memory rate limiter tracking request counts in sliding windows."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check_rate_limit(self, client_ip: str) -> bool:
        """Check if request from client_ip is allowed under current rate limits."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old timestamps
        timestamps = [t for t in self._requests[client_ip] if t > window_start]
        self._requests[client_ip] = timestamps

        if len(timestamps) >= self.max_requests:
            logger.warning(f"[RateLimiter] Rate limit exceeded for IP: {client_ip}")
            return False

        self._requests[client_ip].append(now)
        return True

    def reset(self):
        """Reset all rate limiter tracking."""
        self._requests.clear()


# Default limiter: 30 requests per minute per IP
_global_rate_limiter = TokenBucketRateLimiter(max_requests=30, window_seconds=60)


async def check_review_rate_limit(request: Request):
    """FastAPI dependency enforcing rate limits per client IP."""
    client_ip = request.client.host if request.client else "unknown"
    if not _global_rate_limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait a moment before submitting more code reviews.",
        )
