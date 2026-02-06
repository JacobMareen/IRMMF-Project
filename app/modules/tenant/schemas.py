from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


MAX_NAME_LEN = 200
MAX_SHORT_LEN = 120
MAX_ENV_LEN = 64
MAX_JURISDICTION_LEN = 64
MAX_MODE_LEN = 64
MAX_KEYWORD_LEN = 64
MAX_EMAIL_LEN = 320
MAX_JOB_TITLE_LEN = 120
MAX_PHONE_LEN = 32
MAX_URL_LEN = 2048
MAX_UTM_LEN = 120
MAX_DATE_LEN = 32

ALLOWED_INDUSTRY_SECTORS = {
    "Financial Services",
    "Healthcare",
    "Manufacturing",
    "Technology",
    "Retail",
    "Energy",
    "Government",
    "Education",
    "Other",
}

ALLOWED_EMPLOYEE_COUNTS = {
    "1-50",
    "51-200",
    "201-1000",
    "1001-5000",
    "5001-10000",
    "10000+",
}


class TenantSettingsIn(BaseModel):
    tenant_name: Optional[str] = Field(default=None, max_length=MAX_NAME_LEN)
    environment_type: Optional[str] = Field(default=None, max_length=MAX_ENV_LEN)
    company_name: Optional[str] = Field(default=None, max_length=MAX_NAME_LEN)
    industry_sector: Optional[str] = Field(default=None, max_length=MAX_NAME_LEN)
    employee_count: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    default_jurisdiction: Optional[str] = Field(default=None, max_length=MAX_JURISDICTION_LEN)
    investigation_mode: Optional[str] = Field(default=None, max_length=MAX_MODE_LEN)
    utm_campaign: Optional[str] = Field(default=None, max_length=MAX_UTM_LEN)
    utm_source: Optional[str] = Field(default=None, max_length=MAX_UTM_LEN)
    utm_medium: Optional[str] = Field(default=None, max_length=MAX_UTM_LEN)
    retention_days: Optional[int] = None
    keyword_flagging_enabled: Optional[bool] = None
    keyword_list: Optional[List[str]] = None
    weekend_days: Optional[List[int]] = None
    saturday_is_business_day: Optional[bool] = None
    deadline_cutoff_hour: Optional[int] = None
    notifications_enabled: Optional[bool] = None
    serious_cause_notifications_enabled: Optional[bool] = None
    jurisdiction_rules: Optional[dict] = None
    marketing_consent: Optional[bool] = None

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

    @field_validator("keyword_list")
    @classmethod
    def validate_keyword_list(cls, value):
        if value is None:
            return value
        for keyword in value:
            if keyword is None:
                continue
            if len(keyword) > MAX_KEYWORD_LEN:
                raise ValueError(f"Keyword length must be <= {MAX_KEYWORD_LEN}")
        return value


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
    utm_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    retention_days: int
    keyword_flagging_enabled: bool
    keyword_list: List[str]
    weekend_days: List[int]
    saturday_is_business_day: bool
    deadline_cutoff_hour: int
    notifications_enabled: bool
    serious_cause_notifications_enabled: bool
    jurisdiction_rules: dict
    marketing_consent: bool
    updated_at: datetime


class TenantHolidayCreate(BaseModel):
    holiday_date: str = Field(max_length=MAX_DATE_LEN)
    label: Optional[str] = Field(default=None, max_length=MAX_NAME_LEN)


class TenantHolidayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    holiday_date: str
    label: Optional[str] = Field(default=None, max_length=MAX_NAME_LEN)

class RegistrationRequest(BaseModel):
    company_name: str = Field(max_length=MAX_NAME_LEN)
    industry_sector: str = Field(max_length=MAX_NAME_LEN)
    employee_count: str = Field(max_length=MAX_SHORT_LEN)
    admin_email: str = Field(max_length=MAX_EMAIL_LEN)
    admin_name: str = Field(max_length=MAX_NAME_LEN)
    admin_job_title: Optional[str] = Field(default=None, max_length=MAX_JOB_TITLE_LEN)
    admin_phone_number: Optional[str] = Field(default=None, max_length=MAX_PHONE_LEN)
    admin_linkedin_url: Optional[str] = Field(default=None, max_length=MAX_URL_LEN)
    marketing_consent: bool = False
    utm_campaign: Optional[str] = Field(default=None, max_length=MAX_UTM_LEN)
    utm_source: Optional[str] = Field(default=None, max_length=MAX_UTM_LEN)
    utm_medium: Optional[str] = Field(default=None, max_length=MAX_UTM_LEN)
    environment_type: Optional[str] = Field(default="Production", max_length=MAX_ENV_LEN)

    @field_validator("company_name", "industry_sector", "employee_count", "admin_email", "admin_name")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field is required.")
        return cleaned

    @field_validator("industry_sector")
    @classmethod
    def validate_industry_sector(cls, value: str) -> str:
        cleaned = value.strip()
        for allowed in ALLOWED_INDUSTRY_SECTORS:
            if cleaned.lower() == allowed.lower():
                return allowed
        raise ValueError("Invalid industry sector.")

    @field_validator("employee_count")
    @classmethod
    def validate_employee_count(cls, value: str) -> str:
        cleaned = value.strip()
        for allowed in ALLOWED_EMPLOYEE_COUNTS:
            if cleaned == allowed:
                return allowed
        raise ValueError("Invalid employee count.")

    @field_validator("utm_campaign", "utm_source", "utm_medium")
    @classmethod
    def normalize_utm(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None

class RegistrationResponse(BaseModel):
    tenant_key: str
    admin_email: str
    status: str
    message: str
    login_url: Optional[str] = None
