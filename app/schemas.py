from __future__ import annotations
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_ID_LEN = 128
MAX_PACK_ID_LEN = 128
MAX_ORIGIN_LEN = 32
MAX_EVIDENCE_JSON_LEN = 8000
MAX_SIDEBAR_JSON_LEN = 20000

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
    assessment_id: str = Field(max_length=MAX_ID_LEN)
    q_id: str = Field(max_length=MAX_ID_LEN)
    a_id: str = Field(max_length=MAX_ID_LEN)
    score: float
    pack_id: str = Field(max_length=MAX_PACK_ID_LEN)
    confidence: Optional[float] = None
    evidence: Optional[Dict[str, Any]] = None
    is_deferred: bool = False
    is_flagged: bool = False
    origin: Optional[str] = Field(default=None, max_length=MAX_ORIGIN_LEN)

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

    @field_validator("evidence")
    @classmethod
    def validate_evidence_size(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        payload = json.dumps(v, default=str)
        if len(payload) > MAX_EVIDENCE_JSON_LEN:
            raise ValueError(f"Evidence payload must be <= {MAX_EVIDENCE_JSON_LEN} characters")
        return v

    
class TargetMaturityUpdate(BaseModel):
    target_maturity: Dict[str, float]

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
    override_depth: Optional[bool] = None
    market_research_opt_in: bool = False
    target_maturity: Optional[Dict[str, float]] = None

    @field_validator("sidebar_context")
    @classmethod
    def validate_sidebar_context_size(
        cls, v: Optional[List[Dict[str, Any]]]
    ) -> Optional[List[Dict[str, Any]]]:
        if v is None:
            return v
        payload = json.dumps(v, default=str)
        if len(payload) > MAX_SIDEBAR_JSON_LEN:
            raise ValueError(f"Sidebar context must be <= {MAX_SIDEBAR_JSON_LEN} characters")
        return v
