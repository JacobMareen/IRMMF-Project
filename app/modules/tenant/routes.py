"""Tenant settings API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.security.rbac import require_roles
from app.modules.tenant.schemas import (
    TenantHolidayCreate,
    TenantHolidayOut,
    TenantSettingsIn,
    TenantSettingsOut,
)
from app.modules.tenant.service import TenantService


router = APIRouter()


def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    return TenantService(db)


@router.get("/api/v1/tenant/settings", response_model=TenantSettingsOut)
def get_tenant_settings(
    tenant_key: str = Query(default="default"),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return service.get_settings(tenant_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/api/v1/tenant/settings", response_model=TenantSettingsOut)
def update_tenant_settings(
    payload: TenantSettingsIn,
    tenant_key: str = Query(default="default"),
    principal=Depends(require_roles("ADMIN")),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return service.update_settings(tenant_key, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/tenant/holidays", response_model=list[TenantHolidayOut])
def list_tenant_holidays(
    tenant_key: str = Query(default="default"),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return service.list_holidays(tenant_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/tenant/holidays", response_model=TenantHolidayOut)
def add_tenant_holiday(
    payload: TenantHolidayCreate,
    tenant_key: str = Query(default="default"),
    principal=Depends(require_roles("ADMIN")),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return service.add_holiday(tenant_key, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/api/v1/tenant/holidays/{holiday_id}")
def delete_tenant_holiday(
    holiday_id: int,
    tenant_key: str = Query(default="default"),
    principal=Depends(require_roles("ADMIN")),
    service: TenantService = Depends(get_tenant_service),
):
    try:
        service.delete_holiday(tenant_key, holiday_id)
        return {"status": "deleted"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
