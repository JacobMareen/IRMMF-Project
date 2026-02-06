"""Tenant settings API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.settings import settings
from app.security.access import ensure_tenant_match
from app.security.slowapi import limit
from app.security.rbac import require_roles
from app.modules.tenant.schemas import (
    TenantHolidayCreate,
    TenantHolidayOut,
    TenantSettingsIn,
    TenantSettingsOut,
    RegistrationRequest,
    RegistrationResponse,
)
from app.modules.tenant.service import TenantService


router = APIRouter()


def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    return TenantService(db)


@router.get("/api/v1/tenant/settings", response_model=TenantSettingsOut)
def get_tenant_settings(
    tenant_key: str | None = Query(default=None),
    principal=Depends(require_roles("ADMIN")),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        resolved_tenant = tenant_key or principal.tenant_key or "default"
        ensure_tenant_match(principal, resolved_tenant, not_found_detail="Tenant not found.")
        return service.get_settings(resolved_tenant)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/api/v1/tenant/settings", response_model=TenantSettingsOut)
def update_tenant_settings(
    payload: TenantSettingsIn,
    tenant_key: str | None = Query(default=None),
    principal=Depends(require_roles("ADMIN")),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        resolved_tenant = tenant_key or principal.tenant_key or "default"
        ensure_tenant_match(principal, resolved_tenant, not_found_detail="Tenant not found.")
        return service.update_settings(resolved_tenant, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/tenant/holidays", response_model=list[TenantHolidayOut])
def list_tenant_holidays(
    tenant_key: str | None = Query(default=None),
    principal=Depends(require_roles("ADMIN")),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        resolved_tenant = tenant_key or principal.tenant_key or "default"
        ensure_tenant_match(principal, resolved_tenant, not_found_detail="Tenant not found.")
        return service.list_holidays(resolved_tenant)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/tenant/holidays", response_model=TenantHolidayOut)
def add_tenant_holiday(
    payload: TenantHolidayCreate,
    tenant_key: str | None = Query(default=None),
    principal=Depends(require_roles("ADMIN")),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        resolved_tenant = tenant_key or principal.tenant_key or "default"
        ensure_tenant_match(principal, resolved_tenant, not_found_detail="Tenant not found.")
        return service.add_holiday(resolved_tenant, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/api/v1/tenant/holidays/{holiday_id}")
def delete_tenant_holiday(
    holiday_id: int,
    tenant_key: str | None = Query(default=None),
    principal=Depends(require_roles("ADMIN")),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        resolved_tenant = tenant_key or principal.tenant_key or "default"
        ensure_tenant_match(principal, resolved_tenant, not_found_detail="Tenant not found.")
        service.delete_holiday(resolved_tenant, holiday_id)
        return {"status": "deleted"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/api/v1/register", response_model=RegistrationResponse)
@limit(f"{settings.IRMMF_RATE_LIMIT_INVITE_PER_MINUTE}/minute")
def register_tenant_endpoint(
    request: Request,
    payload: RegistrationRequest,
    service: TenantService = Depends(get_tenant_service),
):
    try:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip() or None
        else:
            ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        return service.register_tenant(payload, ip_address=ip_address, user_agent=user_agent)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal Server Error during registration")
