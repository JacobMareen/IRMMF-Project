from __future__ import annotations

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

MAX_ID_LEN = 128
MAX_SECTION_LEN = 120
MAX_TITLE_LEN = 200
MAX_TEXT_LEN = 2000
MAX_INPUT_LEN = 64
MAX_REF_LEN = 120


class DwfAnswerOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    a_id: str = Field(max_length=MAX_ID_LEN)
    answer_text: str = Field(max_length=MAX_TEXT_LEN)
    base_score: float


class DwfQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    q_id: str = Field(max_length=MAX_ID_LEN)
    section: Optional[str] = Field(default=None, max_length=MAX_SECTION_LEN)
    category: Optional[str] = Field(default=None, max_length=MAX_SECTION_LEN)
    question_title: Optional[str] = Field(default=None, max_length=MAX_TITLE_LEN)
    question_text: str = Field(max_length=MAX_TEXT_LEN)
    guidance: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    input_type: str = Field(max_length=MAX_INPUT_LEN)
    list_ref: Optional[str] = Field(default=None, max_length=MAX_REF_LEN)
    metric_key: Optional[str] = Field(default=None, max_length=MAX_REF_LEN)
    weight: Optional[float] = None
    persona_scope: Optional[str] = Field(default=None, max_length=MAX_SECTION_LEN)
    options: List[DwfAnswerOptionOut]


class DwfAssessmentRegister(BaseModel):
    assessment_id: str = Field(max_length=MAX_ID_LEN)


class DwfResponseCreate(BaseModel):
    assessment_id: str = Field(max_length=MAX_ID_LEN)
    q_id: str = Field(max_length=MAX_ID_LEN)
    a_id: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    score: float
    notes: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)


class DwfAnalysisOut(BaseModel):
    summary: Dict[str, Any]
    personas: Dict[str, Any]
