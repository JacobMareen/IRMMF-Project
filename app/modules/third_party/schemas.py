from __future__ import annotations

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ThirdPartyAssessmentIn(BaseModel):
    partner_name: str
    partner_type: Optional[str] = "Supplier"
    risk_tier: Optional[str] = "Tier-2"
    status: Optional[str] = "draft"
    summary: Optional[str] = None
    responses: Optional[dict] = None
    score: Optional[float] = None


class ThirdPartyAssessmentUpdate(BaseModel):
    partner_name: Optional[str] = None
    partner_type: Optional[str] = None
    risk_tier: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None
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
    a_id: str
    label: str
    score: float


class ThirdPartyQuestionOut(BaseModel):
    q_id: str
    category: Optional[str] = None
    question_text: str
    weight: Optional[float] = None
    options: List[ThirdPartyAnswerOptionOut]


class ThirdPartyAnswerIn(BaseModel):
    q_id: str
    a_id: str


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
