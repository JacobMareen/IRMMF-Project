from __future__ import annotations

from typing import Any, Optional, List

from pydantic import BaseModel, ConfigDict, Field


class AxisScore(BaseModel):
    axis: Optional[str] = None
    code: Optional[str] = None
    score: Optional[float] = None


class RiskItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    scenario: Optional[str] = None
    name: Optional[str] = None
    likelihood: Optional[float] = None
    impact: Optional[float] = None
    risk_level: Optional[str] = None


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="allow")
    title: Optional[str] = None
    priority: Optional[str] = None
    timeline: Optional[str] = None
    rationale: Optional[str] = None


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
    maturity_explanation: Optional[str] = None
    caps_applied: Optional[List[dict[str, Any]]] = None
    risk_heatmap: Optional[List[RiskItem]] = None
    top_risks: Optional[List[RiskItem]] = None


class ExecutiveSummaryRequest(BaseModel):
    assessment_id: Optional[str] = None
    results: ResultsPayload
    audience: Optional[str] = "C-LEVEL"
    include_html: bool = False
    force_refresh: bool = False


class SummarySection(BaseModel):
    title: str
    body: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)


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
    history_id: str
