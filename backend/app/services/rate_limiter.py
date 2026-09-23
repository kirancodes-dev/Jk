import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import HTTPException, status, Request


class RateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        # {key: [timestamp1, timestamp2, ...]}
        self._hits: Dict[str, List[float]] = defaultdict(list)
        # {key: {"count": int, "locked_until": float}}
        self._failures: Dict[str, Dict] = {}

    def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Sliding-window rate limiter.
        Returns (is_allowed: bool, retry_after_seconds: int).
        """
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = [t for t in self._hits[key] if t > window_start]
            self._hits[key] = timestamps

            if len(timestamps) >= max_requests:
                oldest_hit = timestamps[0]
                retry_after = max(1, int(oldest_hit + window_seconds - now))
                return False, retry_after

            self._hits[key].append(now)
            return True, 0

    def enforce(self, key: str, max_requests: int, window_seconds: int, action_name: str = "requests"):
        """Enforces rate limit and raises HTTP 429 if exceeded."""
        allowed, retry_after = self.check_rate_limit(key, max_requests, window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many {action_name}. Rate limit exceeded. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

    def is_locked_out(self, key: str) -> Tuple[bool, int]:
        """Checks if key is currently locked out without incrementing failure counter."""
        now = time.time()
        with self._lock:
            record = self._failures.get(key)
            if record and record.get("locked_until", 0) > now:
                return True, int(record["locked_until"] - now)
            return False, 0

    def record_failure(self, key: str, max_failures: int = 5, lockout_seconds: int = 600) -> Tuple[bool, int]:
        """
        Records a failed attempt. Locks out when failure count hits threshold.
        Returns (is_locked: bool, remaining_seconds: int).
        """
        now = time.time()
        with self._lock:
            record = self._failures.get(key, {"count": 0, "locked_until": 0})
            if record["locked_until"] > now:
                return True, int(record["locked_until"] - now)

            record["count"] += 1
            if record["count"] >= max_failures:
                record["locked_until"] = now + lockout_seconds
                self._failures[key] = record
                return True, lockout_seconds

            self._failures[key] = record
            return False, 0

    def clear_failure(self, key: str):
        """Clears failure counter upon a successful authentication."""
        with self._lock:
            self._failures.pop(key, None)

    def reset(self):
        """Resets all hits and failures (useful in test fixtures)."""
        with self._lock:
            self._hits.clear()
            self._failures.clear()

    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extracts client IP considering standard forwarding headers."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "127.0.0.1"


rate_limiter = RateLimiter()
