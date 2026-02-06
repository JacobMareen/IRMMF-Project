from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


ALLOWED_ROLES = {
    "SUPER_ADMIN",
    "TENANT_ADMIN",
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

MAX_DISPLAY_NAME_LEN = 120
MAX_JOB_TITLE_LEN = 120
MAX_PHONE_LEN = 32
MAX_URL_LEN = 2048
MAX_PASSWORD_LEN = 256


class UserInviteIn(BaseModel):
    email: EmailStr
    display_name: Optional[str] = Field(default=None, max_length=MAX_DISPLAY_NAME_LEN)
    job_title: Optional[str] = Field(default=None, max_length=MAX_JOB_TITLE_LEN)
    phone_number: Optional[str] = Field(default=None, max_length=MAX_PHONE_LEN)
    linkedin_url: Optional[str] = Field(default=None, max_length=MAX_URL_LEN)
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
    password: Optional[str] = Field(default=None, max_length=MAX_PASSWORD_LEN)


class TenantLookupRequest(BaseModel):
    email: EmailStr


class TenantInfo(BaseModel):
    name: str
    key: str


class TenantLookupResponse(BaseModel):
    tenants: list[TenantInfo]


class TermsStatus(BaseModel):
    latest_version: str
    has_accepted: bool
    accepted_at: datetime | None = None
    required: bool = True # If false, UI can skip showing modal


class TermsAccept(BaseModel):
    version: str


class UserRoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    role: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    display_name: Optional[str] = None
    job_title: Optional[str] = None
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    marketing_consent: bool = False
    marketing_consent_at: Optional[datetime] = None
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
