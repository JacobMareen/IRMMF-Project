"""Request-scoped audit context for enriched logging."""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional


@dataclass
class AuditContext:
    actor: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


_audit_context: ContextVar[AuditContext | None] = ContextVar("audit_context", default=None)


def set_audit_context(context: AuditContext | None):
    return _audit_context.set(context)


def reset_audit_context(token) -> None:
    _audit_context.reset(token)


def get_audit_context() -> AuditContext | None:
    return _audit_context.get()
