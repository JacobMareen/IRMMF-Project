"""Insider risk program API routes (policy + controls)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import Principal, get_principal
from app.db import get_db
from app.modules.insider_program.schemas import (
    InsiderRiskPolicyIn,
    InsiderRiskPolicyOut,
    InsiderRiskControlIn,
    InsiderRiskControlOut,
    InsiderRiskControlUpdate,
    InsiderRiskRoadmapIn,
    InsiderRiskRoadmapOut,
    InsiderRiskRoadmapUpdate,
)
from app.modules.insider_program.service import InsiderRiskProgramService, DEFAULT_POLICY
from app.security.access import tenant_principal_required


router = APIRouter(dependencies=[Depends(tenant_principal_required)])


def get_program_service(db: Session = Depends(get_db)) -> InsiderRiskProgramService:
    return InsiderRiskProgramService(db)


@router.get("/api/v1/insider-program/policy", response_model=InsiderRiskPolicyOut)
def get_policy(
    principal: Principal = Depends(get_principal),
    service: InsiderRiskProgramService = Depends(get_program_service),
):
    tenant_key = principal.tenant_key or "default"
    policy = service.get_policy(tenant_key)
    if policy is None:
        return InsiderRiskPolicyOut(**DEFAULT_POLICY.model_dump(), is_template=True)
    return InsiderRiskPolicyOut.model_validate(policy, from_attributes=True)


@router.put("/api/v1/insider-program/policy", response_model=InsiderRiskPolicyOut)
def upsert_policy(
    payload: InsiderRiskPolicyIn,
    principal: Principal = Depends(get_principal),
    service: InsiderRiskProgramService = Depends(get_program_service),
):
    tenant_key = principal.tenant_key or "default"
    policy = service.upsert_policy(tenant_key, payload)
    return InsiderRiskPolicyOut.model_validate(policy, from_attributes=True)


@router.get("/api/v1/insider-program/controls", response_model=list[InsiderRiskControlOut])
def list_controls(
    principal: Principal = Depends(get_principal),
    service: InsiderRiskProgramService = Depends(get_program_service),
):
    tenant_key = principal.tenant_key or "default"
    return service.list_controls(tenant_key)


@router.post("/api/v1/insider-program/controls", response_model=InsiderRiskControlOut, status_code=201)
def create_control(
    payload: InsiderRiskControlIn,
    principal: Principal = Depends(get_principal),
    service: InsiderRiskProgramService = Depends(get_program_service),
):
    tenant_key = principal.tenant_key or "default"
    try:
        return service.create_control(tenant_key, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.put("/api/v1/insider-program/controls/{control_id}", response_model=InsiderRiskControlOut)
def update_control(
    control_id: str,
    payload: InsiderRiskControlUpdate,
    principal: Principal = Depends(get_principal),
    service: InsiderRiskProgramService = Depends(get_program_service),
):
    tenant_key = principal.tenant_key or "default"
    try:
        return service.update_control(tenant_key, control_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/insider-program/roadmap", response_model=list[InsiderRiskRoadmapOut])
def list_roadmap(
    principal: Principal = Depends(get_principal),
    service: InsiderRiskProgramService = Depends(get_program_service),
):
    tenant_key = principal.tenant_key or "default"
    return service.list_roadmap(tenant_key)


@router.post("/api/v1/insider-program/roadmap", response_model=InsiderRiskRoadmapOut, status_code=201)
def create_roadmap_item(
    payload: InsiderRiskRoadmapIn,
    principal: Principal = Depends(get_principal),
    service: InsiderRiskProgramService = Depends(get_program_service),
):
    tenant_key = principal.tenant_key or "default"
    return service.create_roadmap_item(tenant_key, payload)


@router.put("/api/v1/insider-program/roadmap/{item_id}", response_model=InsiderRiskRoadmapOut)
def update_roadmap_item(
    item_id: str,
    payload: InsiderRiskRoadmapUpdate,
    principal: Principal = Depends(get_principal),
    service: InsiderRiskProgramService = Depends(get_program_service),
):
    tenant_key = principal.tenant_key or "default"
    try:
        return service.update_roadmap_item(tenant_key, item_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/api/v1/insider-program/roadmap/{item_id}", status_code=204)
def delete_roadmap_item(
    item_id: str,
    principal: Principal = Depends(get_principal),
    service: InsiderRiskProgramService = Depends(get_program_service),
):
    tenant_key = principal.tenant_key or "default"
    try:
        service.delete_roadmap_item(tenant_key, item_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
