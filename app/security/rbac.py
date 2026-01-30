"""Lightweight RBAC guardrails (disabled by default in dev)."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from auth import Principal, get_principal
from app.security.access import rbac_disabled, role_set


def require_roles(*roles: str):
    required = {role.upper() for role in roles if role}

    def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if rbac_disabled() or not required:
            return principal
        principal_roles = role_set(principal.roles)
        if not principal_roles.intersection(required):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return principal

    return dependency
