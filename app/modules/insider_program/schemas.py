from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


CONTROL_STATUSES = {"planned", "in_progress", "implemented", "monitored"}

MAX_TITLE_LEN = 200
MAX_TEXT_LEN = 2000
MAX_OWNER_LEN = 120
MAX_STATUS_LEN = 32
MAX_VERSION_LEN = 32
MAX_SCOPE_LEN = 200
MAX_ACTION_LEN = 200
MAX_ID_LEN = 64
MAX_CATEGORY_LEN = 120
MAX_PHASE_LEN = 32
MAX_TARGET_WINDOW_LEN = 64
MAX_BULLET_LEN = 500
MAX_ARTIFACT_LEN = 500


class PolicySection(BaseModel):
    title: str = Field(max_length=MAX_TITLE_LEN)
    intent: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    bullets: List[str] = Field(default_factory=list)
    owner: Optional[str] = Field(default=None, max_length=MAX_OWNER_LEN)
    artifacts: List[str] = Field(default_factory=list)

    @field_validator("bullets")
    @classmethod
    def validate_bullets(cls, value: List[str]) -> List[str]:
        for bullet in value or []:
            if len(bullet) > MAX_BULLET_LEN:
                raise ValueError(f"Bullet length must be <= {MAX_BULLET_LEN}")
        return value

    @field_validator("artifacts")
    @classmethod
    def validate_artifacts(cls, value: List[str]) -> List[str]:
        for artifact in value or []:
            if len(artifact) > MAX_ARTIFACT_LEN:
                raise ValueError(f"Artifact length must be <= {MAX_ARTIFACT_LEN}")
        return value


class InsiderRiskPolicyIn(BaseModel):
    status: str = Field(default="Draft", max_length=MAX_STATUS_LEN)
    version: str = Field(default="v1.0", max_length=MAX_VERSION_LEN)
    owner: Optional[str] = Field(default=None, max_length=MAX_OWNER_LEN)
    approval: Optional[str] = Field(default=None, max_length=MAX_OWNER_LEN)
    scope: Optional[str] = Field(default=None, max_length=MAX_SCOPE_LEN)
    last_reviewed: Optional[date] = None
    next_review: Optional[date] = None
    principles: List[str] = Field(default_factory=list)
    sections: List[PolicySection] = Field(default_factory=list)

    @field_validator("principles")
    @classmethod
    def validate_principles(cls, value: List[str]) -> List[str]:
        for principle in value or []:
            if len(principle) > MAX_BULLET_LEN:
                raise ValueError(f"Principle length must be <= {MAX_BULLET_LEN}")
        return value


class InsiderRiskPolicyOut(InsiderRiskPolicyIn):
    model_config = ConfigDict(from_attributes=True)
    is_template: bool = False


class InsiderRiskControlBase(BaseModel):
    control_id: str = Field(max_length=MAX_ID_LEN)
    title: Optional[str] = Field(default=None, max_length=MAX_TITLE_LEN)
    domain: str = Field(max_length=MAX_CATEGORY_LEN)
    objective: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    status: str = Field(default="planned", max_length=MAX_STATUS_LEN)
    owner: Optional[str] = Field(default=None, max_length=MAX_OWNER_LEN)
    frequency: Optional[str] = Field(default=None, max_length=MAX_STATUS_LEN)
    evidence: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    last_reviewed: Optional[date] = None
    next_review: Optional[date] = None
    linked_actions: List[str] = Field(default_factory=list)
    linked_rec_ids: List[str] = Field(default_factory=list)
    linked_categories: List[str] = Field(default_factory=list)

    @field_validator("linked_actions", "linked_rec_ids", "linked_categories")
    @classmethod
    def validate_linked_lists(cls, value: List[str]) -> List[str]:
        for item in value or []:
            if len(item) > MAX_ACTION_LEN:
                raise ValueError(f"Linked item length must be <= {MAX_ACTION_LEN}")
        return value

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
    title: Optional[str] = Field(default=None, max_length=MAX_TITLE_LEN)
    domain: Optional[str] = Field(default=None, max_length=MAX_CATEGORY_LEN)
    objective: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    status: Optional[str] = Field(default=None, max_length=MAX_STATUS_LEN)
    owner: Optional[str] = Field(default=None, max_length=MAX_OWNER_LEN)
    frequency: Optional[str] = Field(default=None, max_length=MAX_STATUS_LEN)
    evidence: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
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


class InsiderRiskRoadmapIn(BaseModel):
    phase: str = Field(default="Now", max_length=MAX_PHASE_LEN)
    title: str = Field(max_length=MAX_TITLE_LEN)
    description: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    owner: Optional[str] = Field(default=None, max_length=MAX_OWNER_LEN)
    target_window: Optional[str] = Field(default=None, max_length=MAX_TARGET_WINDOW_LEN)
    status: str = Field(default="planned", max_length=MAX_STATUS_LEN)


class InsiderRiskRoadmapUpdate(BaseModel):
    phase: Optional[str] = Field(default=None, max_length=MAX_PHASE_LEN)
    title: Optional[str] = Field(default=None, max_length=MAX_TITLE_LEN)
    description: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    owner: Optional[str] = Field(default=None, max_length=MAX_OWNER_LEN)
    target_window: Optional[str] = Field(default=None, max_length=MAX_TARGET_WINDOW_LEN)
    status: Optional[str] = Field(default=None, max_length=MAX_STATUS_LEN)


class InsiderRiskRoadmapOut(InsiderRiskRoadmapIn):
    model_config = ConfigDict(from_attributes=True)
