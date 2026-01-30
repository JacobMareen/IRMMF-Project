from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


CONTROL_STATUSES = {"planned", "in_progress", "implemented", "monitored"}


class PolicySection(BaseModel):
    title: str
    intent: Optional[str] = None
    bullets: List[str] = []
    owner: Optional[str] = None
    artifacts: List[str] = []


class InsiderRiskPolicyIn(BaseModel):
    status: str = "Draft"
    version: str = "v1.0"
    owner: Optional[str] = None
    approval: Optional[str] = None
    scope: Optional[str] = None
    last_reviewed: Optional[date] = None
    next_review: Optional[date] = None
    principles: List[str] = []
    sections: List[PolicySection] = []


class InsiderRiskPolicyOut(InsiderRiskPolicyIn):
    model_config = ConfigDict(from_attributes=True)
    is_template: bool = False


class InsiderRiskControlBase(BaseModel):
    control_id: str
    title: Optional[str] = None
    domain: str
    objective: Optional[str] = None
    status: str = "planned"
    owner: Optional[str] = None
    frequency: Optional[str] = None
    evidence: Optional[str] = None
    last_reviewed: Optional[date] = None
    next_review: Optional[date] = None
    linked_actions: List[str] = []
    linked_rec_ids: List[str] = []
    linked_categories: List[str] = []

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in CONTROL_STATUSES:
            raise ValueError(f"Invalid status: {value}")
        return normalized


class InsiderRiskControlIn(InsiderRiskControlBase):
    pass


class InsiderRiskControlUpdate(BaseModel):
    title: Optional[str] = None
    domain: Optional[str] = None
    objective: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    frequency: Optional[str] = None
    evidence: Optional[str] = None
    last_reviewed: Optional[date] = None
    next_review: Optional[date] = None
    linked_actions: Optional[List[str]] = None
    linked_rec_ids: Optional[List[str]] = None
    linked_categories: Optional[List[str]] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in CONTROL_STATUSES:
            raise ValueError(f"Invalid status: {value}")
        return normalized


class InsiderRiskControlOut(InsiderRiskControlBase):
    model_config = ConfigDict(from_attributes=True)
