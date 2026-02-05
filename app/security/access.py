"""Shared access-control helpers for tenant/role checks."""
from __future__ import annotations

import os
from typing import Iterable

from fastapi import Depends, HTTPException

from auth import Principal, get_principal


from app.core.settings import settings

def rbac_disabled() -> bool:
    return settings.DEV_RBAC_DISABLED


def role_set(roles: Iterable[str] | None) -> set[str]:
    normalized = {role.upper() for role in (roles or []) if role}
    if "LEGAL_COUNSEL" in normalized:
        normalized.add("LEGAL")
    if "AUDITOR" in normalized:
        normalized.add("DPO_AUDITOR")
    return normalized


def is_admin(principal: Principal) -> bool:
    return "ADMIN" in role_set(principal.roles)


def require_tenant(principal: Principal) -> str:
    """Ensure tenant context is present when RBAC is enabled."""
    if rbac_disabled() or is_admin(principal):
        return principal.tenant_key or "default"
    if not principal.tenant_key:
        raise HTTPException(status_code=403, detail="Tenant access required.")
    return principal.tenant_key


def ensure_tenant_match(
    principal: Principal,
    tenant_key: str | None,
    *,
    not_found_detail: str = "Resource not found.",
) -> None:
    """Hide cross-tenant resources by returning 404 when mismatched."""
    if rbac_disabled() or is_admin(principal):
        return
    if not principal.tenant_key:
        raise HTTPException(status_code=403, detail="Tenant access required.")
    if tenant_key and tenant_key != principal.tenant_key:
        raise HTTPException(status_code=404, detail=not_found_detail)


def principal_required(principal: Principal = Depends(get_principal)) -> Principal:
    return principal


def tenant_principal_required(principal: Principal = Depends(get_principal)) -> Principal:
    require_tenant(principal)
    return principal
