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
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException


@dataclass
class Principal:
    subject: str
    tenant_key: Optional[str] = None


def get_principal(
    authorization: Optional[str] = Header(default=None),
    x_irmmf_key: Optional[str] = Header(default=None),
) -> Principal:
    disabled = os.getenv("DEV_AUTH_DISABLED", "1").lower() in ("1", "true", "yes")
    if disabled:
        return Principal(subject=os.getenv("DEV_SUBJECT", "dev"), tenant_key=x_irmmf_key)

    token = os.getenv("DEV_TOKEN", "dev-token")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    provided = authorization.split(" ", 1)[1].strip()
    if provided != token:
        raise HTTPException(status_code=401, detail="Invalid token")

    return Principal(subject=os.getenv("DEV_SUBJECT", "dev"), tenant_key=x_irmmf_key)
