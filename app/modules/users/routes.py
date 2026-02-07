"""User management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.modules.users.schemas import (
    LoginResponse,
    UserInviteIn,
    UserLoginIn,
    UserOut,
    UserRolesUpdate,
    TenantLookupRequest,
    TenantLookupResponse,
    TermsStatus,
    TermsAccept,
)
from app.modules.users.service import UserService
from app.core.settings import settings
from app.security.access import ensure_tenant_match
from app.security.slowapi import limit
from app.security.rbac import require_roles
from auth import get_principal, Principal, Request


router = APIRouter()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/api/v1/users", response_model=list[UserOut])
def list_users(
    tenant_key: str | None = Query(default=None),
    principal=Depends(require_roles("ADMIN", "HR", "LEGAL", "DPO_AUDITOR")),
    service: UserService = Depends(get_user_service),
):
    try:
        resolved_tenant = tenant_key or principal.tenant_key or "default"
        ensure_tenant_match(principal, resolved_tenant, not_found_detail="Tenant not found.")
        return service.list_users(resolved_tenant)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/users/invite", response_model=UserOut)
@limit(f"{settings.IRMMF_RATE_LIMIT_INVITE_PER_MINUTE}/minute")
def invite_user(
    request: Request,
    payload: UserInviteIn,
    tenant_key: str | None = Query(default=None),
    principal=Depends(require_roles("ADMIN")),
    service: UserService = Depends(get_user_service),
):
    try:
        resolved_tenant = tenant_key or principal.tenant_key or "default"
        ensure_tenant_match(principal, resolved_tenant, not_found_detail="Tenant not found.")
        return service.invite_user(resolved_tenant, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/auth/login", response_model=LoginResponse)
@limit(f"{settings.IRMMF_RATE_LIMIT_LOGIN_PER_MINUTE}/minute")
def login_user(
    request: Request,
    payload: UserLoginIn,
    tenant_key: str = Query(default="default"),
    service: UserService = Depends(get_user_service),
):
    try:
        return service.login(tenant_key, payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/api/v1/auth/lookup-tenant", response_model=TenantLookupResponse)
def lookup_tenant(
    payload: TenantLookupRequest,
    service: UserService = Depends(get_user_service),
):
    """Find all tenants associated with an email address."""
    tenants = service.lookup_tenants(payload.email)
    return {"tenants": tenants}


@router.get("/api/v1/auth/terms/status", response_model=TermsStatus)
def get_terms_status(
    principal: Principal = Depends(get_principal),
    service: UserService = Depends(get_user_service),
):
    """Check if the current user has accepted the latest T&C."""
    return service.get_terms_status(principal.subject)


@router.post("/api/v1/auth/terms/accept")
def accept_terms(
    payload: TermsAccept,
    request: Request,
    principal: Principal = Depends(get_principal),
    service: UserService = Depends(get_user_service),
):
    """Accept the T&C."""
    service.accept_terms(
        user_id=principal.subject,
        version=payload.version,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return {"status": "ok"}


@router.put("/api/v1/users/{user_id}/roles", response_model=UserOut)
def update_user_roles(
    user_id: str,
    payload: UserRolesUpdate,
    tenant_key: str | None = Query(default=None),
    principal=Depends(require_roles("ADMIN")),
    service: UserService = Depends(get_user_service),
):
    try:
        resolved_tenant = tenant_key or principal.tenant_key or "default"
        ensure_tenant_match(principal, resolved_tenant, not_found_detail="Tenant not found.")
        return service.update_roles(resolved_tenant, user_id, payload.roles)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
