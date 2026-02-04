from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


ALLOWED_ROLES = {
    "ADMIN",
    "INVESTIGATOR",
    "LEGAL",
    "LEGAL_COUNSEL",
    "HR",
    "EXTERNAL_EXPERT",
    "AUDITOR",
    "DPO_AUDITOR",
    "VIEWER",
}


class UserInviteIn(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        role = value.strip().upper()
        if role not in ALLOWED_ROLES:
            raise ValueError(f"Invalid role: {role}")
        return role


class UserLoginIn(BaseModel):
    email: EmailStr
    password: Optional[str] = None


class UserRoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    role: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    display_name: Optional[str] = None
    status: str
    roles: List[UserRoleOut]
    invited_at: datetime
    last_login_at: Optional[datetime] = None
    created_at: datetime


class LoginResponse(BaseModel):
    user: UserOut
    token: Optional[str] = None


class UserRolesUpdate(BaseModel):
    roles: List[str]

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("At least one role is required")
        normalized = []
        for role in value:
            role_value = role.strip().upper()
            if role_value not in ALLOWED_ROLES:
                raise ValueError(f"Invalid role: {role_value}")
            normalized.append(role_value)
        seen = set()
        deduped = []
        for role in normalized:
            if role not in seen:
                seen.add(role)
                deduped.append(role)
        return deduped
