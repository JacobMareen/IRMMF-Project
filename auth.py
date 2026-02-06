"""Very lightweight auth for alpha development.

Goals:
- Keep local testing frictionless.
- Provide a clear seam to swap in real JWT/tenant auth later.

Current behavior:
- By default, auth is *disabled* (DEV_AUTH_DISABLED=1).
- If you enable auth (DEV_AUTH_DISABLED=0), requests must include:
    Authorization: Bearer <DEV_TOKEN>

You can also pass a tenant key via X-IRMMF-KEY for early multi-tenant testing.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from typing import Optional, List, Mapping

from fastapi import Depends, Header, HTTPException, Request
from app.security.jwt import verify_token


@dataclass
class Principal:
    subject: str
    tenant_key: Optional[str] = None
    roles: List[str] | None = None


def get_principal(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_irmmf_key: Optional[str] = Header(default=None),
    x_irmmf_roles: Optional[str] = Header(default=None),
) -> Principal:
    cached = getattr(request.state, "principal", None)
    if cached:
        return cached
    principal = _build_principal(
        authorization=authorization,
        x_irmmf_key=x_irmmf_key,
        x_irmmf_roles=x_irmmf_roles,
        allow_anonymous=False,
    )
    if principal is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    request.state.principal = principal
    return principal


def resolve_principal_from_headers(
    headers: Mapping[str, str],
    *,
    allow_anonymous: bool = True,
) -> Principal | None:
    return _build_principal(
        authorization=headers.get("authorization"),
        x_irmmf_key=headers.get("x-irmmf-key"),
        x_irmmf_roles=headers.get("x-irmmf-roles"),
        allow_anonymous=allow_anonymous,
    )


def _default_roles() -> List[str]:
    env_roles = os.getenv("DEV_ROLES")
    if env_roles:
        return [role.strip().upper() for role in env_roles.split(",") if role.strip()]
    return ["SUPER_ADMIN", "ADMIN"]


def _resolve_roles(raw_roles: Optional[str]) -> List[str]:
    if not raw_roles:
        return []
    return [role.strip().upper() for role in raw_roles.split(",") if role.strip()]


def _auth_disabled() -> bool:
    return os.getenv("DEV_AUTH_DISABLED", "1").lower() in ("1", "true", "yes")


def _build_principal(
    *,
    authorization: Optional[str],
    x_irmmf_key: Optional[str],
    x_irmmf_roles: Optional[str],
    allow_anonymous: bool,
) -> Principal | None:
    disabled = _auth_disabled()
    roles = _resolve_roles(x_irmmf_roles)
    if disabled:
        return Principal(
            subject=os.getenv("DEV_SUBJECT", "dev"),
            tenant_key=x_irmmf_key,
            roles=roles or _default_roles(),
        )

    token = os.getenv("DEV_TOKEN", "dev-token")
    if not authorization or not authorization.lower().startswith("bearer "):
        if allow_anonymous:
            return None
        raise HTTPException(status_code=401, detail="Missing bearer token")

    provided = authorization.split(" ", 1)[1].strip()
    
    # 1. Try Legacy Dev Token
    if token and secrets.compare_digest(provided, token):
        return Principal(
            subject=os.getenv("DEV_SUBJECT", "dev"),
            tenant_key=x_irmmf_key,
            roles=roles or _default_roles(),
        )

    # 2. Try JWT
    payload = verify_token(provided)
    if payload:
        return Principal(
            subject=payload.get("sub"),
            tenant_key=payload.get("tenant_key") or x_irmmf_key, # JWT claim overrides header if present
            roles=payload.get("roles") or roles or _default_roles(),
        )

    # 3. Fail
    if allow_anonymous:
        return None
    raise HTTPException(status_code=401, detail="Invalid token")
