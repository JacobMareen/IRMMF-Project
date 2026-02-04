"""Lightweight in-memory rate limiting for dev environments."""
from __future__ import annotations

from dataclasses import dataclass
import os
import time
from threading import Lock
from typing import Tuple

from fastapi import Request


@dataclass
class RateLimitConfig:
    enabled: bool
    limit_per_minute: int
    window_seconds: int
    max_body_bytes: int | None


def load_rate_limit_config() -> RateLimitConfig:
    enabled = os.getenv("IRMMF_RATE_LIMIT_ENABLED", "1").lower() in ("1", "true", "yes")
    limit = int(os.getenv("IRMMF_RATE_LIMIT_PER_MINUTE", "240"))
    window = int(os.getenv("IRMMF_RATE_LIMIT_WINDOW_SECONDS", "60"))
    max_body_mb = os.getenv("IRMMF_MAX_BODY_MB")
    max_body_bytes = int(max_body_mb) * 1024 * 1024 if max_body_mb else None
    return RateLimitConfig(
        enabled=enabled,
        limit_per_minute=limit,
        window_seconds=window,
        max_body_bytes=max_body_bytes,
    )


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, Tuple[float, int]] = {}
        self._lock = Lock()

    def allow(self, key: str) -> tuple[bool, int]:
        now = time.monotonic()
        with self._lock:
            window_start, count = self._hits.get(key, (now, 0))
            if now - window_start >= self.window_seconds:
                window_start = now
                count = 0
            if count >= self.limit:
                retry_after = max(0, int(self.window_seconds - (now - window_start)))
                return False, retry_after
            self._hits[key] = (window_start, count + 1)
            return True, 0


def resolve_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for") or request.headers.get("x-real-ip")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
