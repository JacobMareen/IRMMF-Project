from __future__ import annotations

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict


class DwfAnswerOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    a_id: str
    answer_text: str
    base_score: float


class DwfQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    q_id: str
    section: Optional[str] = None
    category: Optional[str] = None
    question_title: Optional[str] = None
    question_text: str
    guidance: Optional[str] = None
    input_type: str
    list_ref: Optional[str] = None
    metric_key: Optional[str] = None
    weight: Optional[float] = None
    persona_scope: Optional[str] = None
    options: List[DwfAnswerOptionOut]


class DwfAssessmentRegister(BaseModel):
    assessment_id: str


class DwfResponseCreate(BaseModel):
    assessment_id: str
    q_id: str
    a_id: Optional[str] = None
    score: float
    notes: Optional[str] = None


class DwfAnalysisOut(BaseModel):
    summary: Dict[str, Any]
    personas: Dict[str, Any]
