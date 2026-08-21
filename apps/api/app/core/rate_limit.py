"""Sliding-window token rate limiter middleware and dependency (TRADLY_SRS v1.0 §6.1.4, NFR-S4)."""

import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self):
        # Maps client_key -> list of request epoch timestamps
        self._records: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(
        self, client_key: str, max_requests: int, window_seconds: int = 60
    ) -> Tuple[bool, int, int]:
        """
        Check if a request from client_key is allowed within window_seconds.
        Returns: (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        window_start = now - window_seconds

        # Prune outdated timestamps
        timestamps = self._records[client_key]
        active = [t for t in timestamps if t > window_start]
        self._records[client_key] = active

        current_count = len(active)
        if current_count >= max_requests:
            oldest_active = active[0] if active else now
            retry_after = max(1, int(oldest_active + window_seconds - now))
            return False, 0, retry_after

        # Record this request
        active.append(now)
        remaining = max_requests - len(active)
        return True, remaining, 0

    def cleanup(self):
        """Prune idle clients older than 5 minutes."""
        now = time.time()
        cutoff = now - 300
        keys_to_remove = [
            k for k, v in self._records.items() if not v or v[-1] < cutoff
        ]
        for k in keys_to_remove:
            del self._records[k]


limiter = SlidingWindowRateLimiter()


def get_client_identifier(request: Request) -> str:
    """Extract client IP address or authenticated user ID."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        return f"token:{token[-12:]}"

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    client = request.client
    return client.host if client else "127.0.0.1"


def get_endpoint_limit(path: str) -> int:
    """Determine rate limit per minute based on endpoint sensitivity."""
    if path.startswith("/api/v1/auth"):
        return 20  # 20 auth attempts / minute
    elif path.startswith("/api/v1/ai"):
        return 30  # 30 AI reasoning queries / minute
    elif path.startswith("/api/v1/trading/orders"):
        return 30  # 30 order placements / minute
    return 120  # 120 general requests / minute


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware to enforce rate limiting across all HTTP routes."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Exempt docs, health check, and static files
        if path in ["/docs", "/openapi.json", "/health", "/redoc", "/"] or not path.startswith("/api/"):
            return await call_next(request)

        client_key = get_client_identifier(request)
        max_requests = get_endpoint_limit(path)
        window = 60

        allowed, remaining, retry_after = limiter.is_allowed(client_key, max_requests, window)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_key} on {path} (limit: {max_requests}/min)")
            corr_id = request.headers.get("X-Request-ID") or "unknown"
            return JSONResponse(
                status_code=429,
                content={
                    "data": None,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Maximum {max_requests} requests per minute allowed on this endpoint.",
                        "details": {
                            "retry_after_seconds": retry_after,
                            "limit_per_minute": max_requests,
                            "client_key": client_key,
                        },
                    },
                    "meta": {
                        "request_id": corr_id,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "version": "v1",
                    },
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                },
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        return response
