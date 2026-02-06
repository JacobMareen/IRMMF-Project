"""SlowAPI rate limiting integration."""
from __future__ import annotations

from app.core.settings import settings

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address

    _SLOWAPI_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    Limiter = None  # type: ignore[assignment]
    _rate_limit_exceeded_handler = None  # type: ignore[assignment]
    RateLimitExceeded = None  # type: ignore[assignment]
    SlowAPIMiddleware = None  # type: ignore[assignment]
    get_remote_address = None  # type: ignore[assignment]
    _SLOWAPI_AVAILABLE = False


limiter = None
if _SLOWAPI_AVAILABLE:
    default_limit = f"{settings.IRMMF_RATE_LIMIT_PER_MINUTE}/minute"
    limiter = Limiter(key_func=get_remote_address, default_limits=[default_limit])


def slowapi_enabled() -> bool:
    return bool(settings.IRMMF_RATE_LIMIT_ENABLED) and _SLOWAPI_AVAILABLE


def limit(rule: str):
    if limiter and slowapi_enabled():
        return limiter.limit(rule)

    def decorator(func):
        return func

    return decorator
