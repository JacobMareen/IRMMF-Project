from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator

# --- Outputs ---
class AnswerOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    a_id: str
    answer_text: str
    base_score: float

class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    q_id: str
    domain: str
    question_title: Optional[str] = None
    question_text: str
    guidance: Optional[str] = None
    tier: Optional[str] = None
    evidence_policy_id: Optional[str] = None
    
    # Neuro-Adaptive Logic Fields
    branch_type: Optional[str] = None
    gate_threshold: Optional[float] = None
    next_if_low: Optional[str] = None
    next_if_high: Optional[str] = None
    next_default: Optional[str] = None
    end_flag: Optional[str] = None

    options: List[AnswerOptionOut]

# --- Inputs ---
class ResponseCreate(BaseModel):
    assessment_id: str
    q_id: str
    a_id: str
    score: float
    pack_id: str
    confidence: Optional[float] = None
    evidence: Optional[Dict[str, Any]] = None
    is_deferred: bool = False
    is_flagged: bool = False
    origin: Optional[str] = None

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        if not (0 <= v <= 4):
            # Allow -1 for special "N/A" cases if needed, but standard is 0-4
            raise ValueError('Score must be between 0 and 4')
        return v

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v

    
class ResumptionState(BaseModel):
    responses: Dict[str, str | List[str]]  # Maps Q_ID to A_ID (single) or [A_ID, ...] (multi-select)
    next_best_qid: Optional[str]   # The ID of the first unanswered question in the path
    reachable_path: List[str]      # The calculated logic path based on current answers
    deferred_ids: Optional[List[str]] = None
    flagged_ids: Optional[List[str]] = None
    marked_for_review: Optional[List[str]] = None
    next_reason: Optional[str] = None
    sidebar_context: Optional[List[Dict[str, Any]]] = None
    completion_pct: Optional[int] = None
    depth: Optional[str] = None
    override_depth: Optional[bool] = None
