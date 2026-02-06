from __future__ import annotations

from typing import Any, Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_ID_LEN = 128
MAX_AUDIENCE_LEN = 64
MAX_RISK_NAME_LEN = 200
MAX_RISK_SCENARIO_LEN = 200
MAX_RISK_LEVEL_LEN = 64
MAX_REC_TITLE_LEN = 200
MAX_REC_PRIORITY_LEN = 64
MAX_REC_TIMELINE_LEN = 120
MAX_REC_RATIONALE_LEN = 2000
MAX_SUMMARY_TITLE_LEN = 200
MAX_SUMMARY_BODY_LEN = 4000
MAX_BULLET_LEN = 400
MAX_EXPLANATION_LEN = 4000


class AxisScore(BaseModel):
    axis: Optional[str] = None
    code: Optional[str] = None
    score: Optional[float] = None


class RiskItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    scenario: Optional[str] = Field(default=None, max_length=MAX_RISK_SCENARIO_LEN)
    name: Optional[str] = Field(default=None, max_length=MAX_RISK_NAME_LEN)
    likelihood: Optional[float] = None
    impact: Optional[float] = None
    risk_level: Optional[str] = Field(default=None, max_length=MAX_RISK_LEVEL_LEN)

    @field_validator("id", "scenario", "name", "risk_level")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="allow")
    title: Optional[str] = Field(default=None, max_length=MAX_REC_TITLE_LEN)
    priority: Optional[str] = Field(default=None, max_length=MAX_REC_PRIORITY_LEN)
    timeline: Optional[str] = Field(default=None, max_length=MAX_REC_TIMELINE_LEN)
    rationale: Optional[str] = Field(default=None, max_length=MAX_REC_RATIONALE_LEN)

    @field_validator("title", "priority", "timeline", "rationale")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None


class SummaryMetrics(BaseModel):
    model_config = ConfigDict(extra="allow")
    trust_index: Optional[float] = None
    friction_score: Optional[float] = None
    evidence_confidence_avg: Optional[float] = None


class ResultsPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    archetype: Optional[str] = None
    archetype_details: Optional[dict[str, Any]] = None
    summary: Optional[SummaryMetrics] = None
    axes: Optional[List[AxisScore]] = None
    expanded_axes: Optional[List[AxisScore]] = None
    declared_vector: Optional[List[AxisScore]] = None
    verified_vector: Optional[List[AxisScore]] = None
    gap_vector: Optional[List[AxisScore]] = None
    recommendations: Optional[List[Recommendation]] = None
    maturity_scores: Optional[dict[str, Any]] = None
    maturity_explanation: Optional[str] = Field(default=None, max_length=MAX_EXPLANATION_LEN)
    caps_applied: Optional[List[dict[str, Any]]] = None
    risk_heatmap: Optional[List[RiskItem]] = None
    top_risks: Optional[List[RiskItem]] = None


class ExecutiveSummaryRequest(BaseModel):
    assessment_id: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    results: ResultsPayload
    audience: Optional[str] = Field(default="C-LEVEL", max_length=MAX_AUDIENCE_LEN)
    include_html: bool = False
    force_refresh: bool = False


class SummarySection(BaseModel):
    title: str = Field(max_length=MAX_SUMMARY_TITLE_LEN)
    body: Optional[str] = Field(default=None, max_length=MAX_SUMMARY_BODY_LEN)
    bullets: List[str] = Field(default_factory=list)

    @field_validator("bullets")
    @classmethod
    def validate_bullets(cls, value: List[str]) -> List[str]:
        if not value:
            return value
        cleaned = []
        for item in value:
            if item is None:
                continue
            text = item.strip()
            if not text:
                continue
            if len(text) > MAX_BULLET_LEN:
                raise ValueError(f"Bullet length must be <= {MAX_BULLET_LEN}")
            cleaned.append(text)
        return cleaned


class ExecutiveSummaryResponse(BaseModel):
    assessment_id: Optional[str] = None
    tenant_key: Optional[str] = None
    generated_at: str
    generator: str
    maturity_band: Optional[str] = None
    maturity_level: Optional[int] = None
    maturity_label: Optional[str] = None
    average_score: Optional[float] = None
    summary_text: str
    summary_html: Optional[str] = None
    key_findings: List[str] = Field(default_factory=list)
    high_level_recommendations: List[str] = Field(default_factory=list)
    sections: List[SummarySection] = Field(default_factory=list)
    metrics: Optional[SummaryMetrics] = None
    pinned_history_id: Optional[str] = None
    pinned_at: Optional[str] = None


class ExecutiveSummaryHistoryOut(BaseModel):
    id: str
    assessment_id: Optional[str] = None
    tenant_key: Optional[str] = None
    generated_at: str
    generator: str
    maturity_band: Optional[str] = None
    maturity_level: Optional[int] = None
    maturity_label: Optional[str] = None
    average_score: Optional[float] = None
    summary_text: str
    summary_html: Optional[str] = None
    key_findings: List[str] = Field(default_factory=list)
    high_level_recommendations: List[str] = Field(default_factory=list)
    metrics: Optional[SummaryMetrics] = None
    pinned: bool = False


class ExecutiveSummaryPinIn(BaseModel):
    history_id: str = Field(max_length=MAX_ID_LEN)
