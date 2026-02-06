from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class TenantSettingsIn(BaseModel):
    tenant_name: Optional[str] = None
    environment_type: Optional[str] = None
    company_name: Optional[str] = None
    industry_sector: Optional[str] = None
    employee_count: Optional[str] = None
    default_jurisdiction: Optional[str] = None
    investigation_mode: Optional[str] = None
    retention_days: Optional[int] = None
    keyword_flagging_enabled: Optional[bool] = None
    keyword_list: Optional[List[str]] = None
    weekend_days: Optional[List[int]] = None
    saturday_is_business_day: Optional[bool] = None
    deadline_cutoff_hour: Optional[int] = None
    notifications_enabled: Optional[bool] = None
    serious_cause_notifications_enabled: Optional[bool] = None
    jurisdiction_rules: Optional[dict] = None

    @field_validator("retention_days")
    @classmethod
    def validate_retention(cls, value):
        if value is None:
            return value
        if value < 0:
            raise ValueError("retention_days must be >= 0")
        return value

    @field_validator("deadline_cutoff_hour")
    @classmethod
    def validate_cutoff(cls, value):
        if value is None:
            return value
        if value < 0 or value > 23:
            raise ValueError("deadline_cutoff_hour must be between 0 and 23")
        return value

    @field_validator("weekend_days")
    @classmethod
    def validate_weekend_days(cls, value):
        if value is None:
            return value
        cleaned = []
        for day in value:
            if day < 0 or day > 6:
                raise ValueError("weekend_days must be between 0 and 6")
            cleaned.append(day)
        return cleaned


class TenantSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_key: str
    tenant_name: str
    environment_type: str
    company_name: Optional[str] = None
    industry_sector: Optional[str] = None
    employee_count: Optional[str] = None
    default_jurisdiction: str
    investigation_mode: str
    retention_days: int
    keyword_flagging_enabled: bool
    keyword_list: List[str]
    weekend_days: List[int]
    saturday_is_business_day: bool
    deadline_cutoff_hour: int
    notifications_enabled: bool
    serious_cause_notifications_enabled: bool
    jurisdiction_rules: dict
    updated_at: datetime


class TenantHolidayCreate(BaseModel):
    holiday_date: str
    label: Optional[str] = None


class TenantHolidayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    holiday_date: str
    label: Optional[str] = None

class RegistrationRequest(BaseModel):
    company_name: str
    industry_sector: Optional[str] = None
    employee_count: Optional[str] = None
    admin_email: str
    admin_name: str
    environment_type: Optional[str] = "Production"

class RegistrationResponse(BaseModel):
    tenant_key: str
    admin_email: str
    status: str
    message: str
    login_url: Optional[str] = None

