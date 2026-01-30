"""User management API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.modules.users.schemas import LoginResponse, UserInviteIn, UserLoginIn, UserOut, UserRolesUpdate
from app.modules.users.service import UserService
from app.security.rbac import require_roles


router = APIRouter()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/api/v1/users", response_model=list[UserOut])
def list_users(
    tenant_key: str = Query(default="default"),
    principal=Depends(require_roles("ADMIN", "HR", "LEGAL", "DPO_AUDITOR")),
    service: UserService = Depends(get_user_service),
):
    try:
        return service.list_users(tenant_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/users/invite", response_model=UserOut)
def invite_user(
    payload: UserInviteIn,
    tenant_key: str = Query(default="default"),
    principal=Depends(require_roles("ADMIN")),
    service: UserService = Depends(get_user_service),
):
    try:
        return service.invite_user(tenant_key, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/auth/login", response_model=LoginResponse)
def login_user(
    payload: UserLoginIn,
    tenant_key: str = Query(default="default"),
    service: UserService = Depends(get_user_service),
):
    try:
        return service.login(tenant_key, payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.put("/api/v1/users/{user_id}/roles", response_model=UserOut)
def update_user_roles(
    user_id: str,
    payload: UserRolesUpdate,
    tenant_key: str = Query(default="default"),
    principal=Depends(require_roles("ADMIN")),
    service: UserService = Depends(get_user_service),
):
    try:
        return service.update_roles(tenant_key, user_id, payload.roles)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
