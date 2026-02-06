from __future__ import annotations

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ThirdPartyAssessmentIn(BaseModel):
    partner_name: str = Field(max_length=200)
    partner_type: Optional[str] = Field(default="Supplier", max_length=64)
    risk_tier: Optional[str] = Field(default="Tier-2", max_length=32)
    status: Optional[str] = Field(default="draft", max_length=32)
    summary: Optional[str] = Field(default=None, max_length=2000)
    responses: Optional[dict] = None
    score: Optional[float] = None


class ThirdPartyAssessmentUpdate(BaseModel):
    partner_name: Optional[str] = Field(default=None, max_length=200)
    partner_type: Optional[str] = Field(default=None, max_length=64)
    risk_tier: Optional[str] = Field(default=None, max_length=32)
    status: Optional[str] = Field(default=None, max_length=32)
    summary: Optional[str] = Field(default=None, max_length=2000)
    responses: Optional[dict] = None
    score: Optional[float] = None


class ThirdPartyAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_key: str
    assessment_id: str
    partner_name: str
    partner_type: str
    risk_tier: str
    status: str
    summary: Optional[str] = None
    responses: Optional[dict] = None
    score: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class ThirdPartyAnswerOptionOut(BaseModel):
    a_id: str = Field(max_length=128)
    label: str = Field(max_length=300)
    score: float


class ThirdPartyQuestionOut(BaseModel):
    q_id: str = Field(max_length=128)
    category: Optional[str] = Field(default=None, max_length=120)
    question_text: str = Field(max_length=2000)
    weight: Optional[float] = None
    options: List[ThirdPartyAnswerOptionOut]


class ThirdPartyAnswerIn(BaseModel):
    q_id: str = Field(max_length=128)
    a_id: str = Field(max_length=128)


class ThirdPartyResponseIn(BaseModel):
    responses: List[ThirdPartyAnswerIn]


class ThirdPartyAnalysisOut(BaseModel):
    partner_id: str
    assessment_id: str
    partner_name: str
    score: Optional[float] = None
    risk_band: Optional[str] = None
    answered: int
    total: int
    coverage: float
    responses: Optional[Dict[str, Any]] = None
