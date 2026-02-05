from __future__ import annotations

from datetime import datetime, timezone
from html import escape
import hashlib
import json
from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from app import models
from app.modules.ai.schemas import (
    AxisScore,
    ExecutiveSummaryRequest,
    ExecutiveSummaryResponse,
    ExecutiveSummaryHistoryOut,
    ResultsPayload,
    RiskItem,
    SummarySection,
    SummaryMetrics,
)


class ExecutiveSummaryService:
    def __init__(self, db: Session | None = None):
        self.db = db

    def generate(self, payload: ExecutiveSummaryRequest, tenant_key: Optional[str]) -> ExecutiveSummaryResponse:
        results = payload.results or ResultsPayload()
        assessment_id = payload.assessment_id
        payload_hash = _hash_results(results)

        if self.db and assessment_id and not payload.force_refresh:
            cached = self._get_cached_row(tenant_key, assessment_id)
            if cached and cached.payload_hash == payload_hash:
                return _row_to_response(cached)

        axes = results.expanded_axes or results.axes or []
        avg_score = _average_score(axes)
        maturity_band = _maturity_band(avg_score)
        maturity_level, maturity_label = _maturity_level(avg_score, maturity_band)
        strengths = _top_axes(axes, reverse=True, limit=2)
        gaps = _top_axes(axes, reverse=False, limit=2)
        risk_labels = _risk_labels(results.top_risks or results.risk_heatmap or [])

        key_findings = []
        if strengths:
            key_findings.append(f"Top strengths: {', '.join(strengths)}.")
        if gaps:
            key_findings.append(f"Largest gaps: {', '.join(gaps)}.")
        if risk_labels:
            key_findings.append(f"Primary risk signals: {', '.join(risk_labels[:3])}.")

        recommendations = _recommendations(results, gaps)

        summary_text = _build_summary_text(
            maturity_band=maturity_band,
            average_score=avg_score,
            archetype=results.archetype,
            risk_labels=risk_labels,
        )

        sections = [
            SummarySection(title="Executive Summary", body=summary_text),
            SummarySection(title="Key Findings", bullets=key_findings),
            SummarySection(title="High-Level Recommendations", bullets=recommendations),
        ]

        summary_html = None
        if payload.include_html:
            summary_html = _render_html(summary_text, key_findings, recommendations)

        generated_at = datetime.now(timezone.utc).isoformat()

        response = ExecutiveSummaryResponse(
            assessment_id=payload.assessment_id,
            tenant_key=tenant_key,
            generated_at=generated_at,
            generator="template-v1",
            maturity_band=maturity_band,
            maturity_level=maturity_level,
            maturity_label=maturity_label,
            average_score=avg_score,
            summary_text=summary_text,
            summary_html=summary_html,
            key_findings=key_findings,
            high_level_recommendations=recommendations,
            sections=sections,
            metrics=results.summary,
        )

        if self.db and assessment_id:
            cached = self._get_cached_row(tenant_key, assessment_id)
            if cached:
                cached.payload_hash = payload_hash
                cached.summary_text = response.summary_text
                cached.summary_html = response.summary_html
                cached.key_findings = response.key_findings
                cached.high_level_recommendations = response.high_level_recommendations
                cached.maturity_band = response.maturity_band
                cached.average_score = response.average_score
                cached.generator = response.generator
                cached.metrics = response.metrics.model_dump() if response.metrics else None
            else:
                cached = models.ExecutiveSummaryCache(
                    tenant_key=tenant_key or "default",
                    assessment_id=assessment_id,
                    payload_hash=payload_hash,
                    summary_text=response.summary_text,
                    summary_html=response.summary_html,
                    key_findings=response.key_findings,
                    high_level_recommendations=response.high_level_recommendations,
                    maturity_band=response.maturity_band,
                    average_score=response.average_score,
                    generator=response.generator,
                    metrics=response.metrics.model_dump() if response.metrics else None,
                )
                self.db.add(cached)
            self.db.commit()
            self.db.refresh(cached)
            self._record_history(response, tenant_key, assessment_id, payload_hash)
            return _row_to_response(cached)

        return response

    def get_cached_summary(self, tenant_key: Optional[str], assessment_id: str) -> ExecutiveSummaryResponse | None:
        if not self.db:
            return None
        row = self._get_cached_row(tenant_key, assessment_id)
        if not row:
            return None
        if row.pinned_history_id:
            pinned = self.get_history_item(tenant_key, row.pinned_history_id)
            if pinned:
                return _history_row_to_response(
                    pinned,
                    pinned_history_id=str(row.pinned_history_id),
                    pinned_at=row.pinned_at,
                )
        return _row_to_response(row)

    def list_history(self, tenant_key: Optional[str], assessment_id: str, limit: int = 10) -> list[ExecutiveSummaryHistoryOut]:
        if not self.db:
            return []
        pinned_id = None
        cached = self._get_cached_row(tenant_key, assessment_id)
        if cached and cached.pinned_history_id:
            pinned_id = str(cached.pinned_history_id)
        rows = (
            self.db.query(models.ExecutiveSummaryHistory)
            .filter(models.ExecutiveSummaryHistory.tenant_key == (tenant_key or "default"))
            .filter(models.ExecutiveSummaryHistory.assessment_id == assessment_id)
            .order_by(models.ExecutiveSummaryHistory.generated_at.desc())
            .limit(limit)
            .all()
        )
        return [_history_row_to_out(row, pinned=str(row.id) == pinned_id if pinned_id else False) for row in rows]

    def get_history_item(
        self,
        tenant_key: Optional[str],
        history_id,
    ) -> models.ExecutiveSummaryHistory | None:
        if not self.db:
            return None
        return (
            self.db.query(models.ExecutiveSummaryHistory)
            .filter(models.ExecutiveSummaryHistory.tenant_key == (tenant_key or "default"))
            .filter(models.ExecutiveSummaryHistory.id == history_id)
            .first()
        )

    def pin_history(
        self,
        tenant_key: Optional[str],
        assessment_id: str,
        history_id,
    ) -> ExecutiveSummaryResponse:
        if not self.db:
            raise ValueError("Database unavailable.")
        history = self.get_history_item(tenant_key, history_id)
        if not history or history.assessment_id != assessment_id:
            raise ValueError("Summary history not found.")
        cached = self._get_cached_row(tenant_key, assessment_id)
        if cached:
            cached.pinned_history_id = history.id
            cached.pinned_at = datetime.now(timezone.utc)
        else:
            cached = models.ExecutiveSummaryCache(
                tenant_key=tenant_key or "default",
                assessment_id=assessment_id,
                payload_hash=history.payload_hash,
                summary_text=history.summary_text,
                summary_html=history.summary_html,
                key_findings=history.key_findings,
                high_level_recommendations=history.high_level_recommendations,
                maturity_band=history.maturity_band,
                average_score=history.average_score,
                generator=history.generator,
                metrics=history.metrics,
                pinned_history_id=history.id,
                pinned_at=datetime.now(timezone.utc),
            )
            self.db.add(cached)
        self.db.commit()
        self.db.refresh(cached)
        return _history_row_to_response(history, pinned_history_id=str(history.id), pinned_at=cached.pinned_at)

    def unpin_history(self, tenant_key: Optional[str], assessment_id: str) -> None:
        if not self.db:
            raise ValueError("Database unavailable.")
        cached = self._get_cached_row(tenant_key, assessment_id)
        if not cached:
            return
        cached.pinned_history_id = None
        cached.pinned_at = None
        self.db.commit()

    def _get_cached_row(self, tenant_key: Optional[str], assessment_id: str):
        if not self.db:
            return None
        return (
            self.db.query(models.ExecutiveSummaryCache)
            .filter(models.ExecutiveSummaryCache.tenant_key == (tenant_key or "default"))
            .filter(models.ExecutiveSummaryCache.assessment_id == assessment_id)
            .first()
        )

    def _record_history(
        self,
        response: ExecutiveSummaryResponse,
        tenant_key: Optional[str],
        assessment_id: str,
        payload_hash: str,
    ) -> None:
        if not self.db:
            return
        history = models.ExecutiveSummaryHistory(
            tenant_key=tenant_key or "default",
            assessment_id=assessment_id,
            payload_hash=payload_hash,
            summary_text=response.summary_text,
            summary_html=response.summary_html,
            key_findings=response.key_findings,
            high_level_recommendations=response.high_level_recommendations,
            maturity_band=response.maturity_band,
            average_score=response.average_score,
            generator=response.generator,
            metrics=response.metrics.model_dump() if response.metrics else None,
        )
        self.db.add(history)
        self.db.commit()


def _axis_label(axis: AxisScore) -> str:
    return axis.axis or axis.code or "Axis"


def _average_score(axes: Iterable[AxisScore]) -> Optional[float]:
    scores = [axis.score for axis in axes if axis.score is not None]
    if not scores:
        return None
    avg = sum(scores) / len(scores)
    if avg <= 4.0:
        avg *= 25.0
    return round(avg, 1)


def _maturity_band(avg_score: Optional[float]) -> Optional[str]:
    if avg_score is None:
        return None
    if avg_score >= 80:
        return "Optimized"
    if avg_score >= 60:
        return "Managed"
    if avg_score >= 40:
        return "Defined"
    if avg_score >= 20:
        return "Developing"
    return "Ad-hoc"


def _maturity_level(avg_score: Optional[float], maturity_band: Optional[str]) -> tuple[Optional[int], Optional[str]]:
    if avg_score is not None:
        if avg_score >= 80:
            return 5, "Optimized"
        if avg_score >= 60:
            return 4, "Managed"
        if avg_score >= 40:
            return 3, "Defined"
        if avg_score >= 20:
            return 2, "Developing"
        return 1, "Ad-hoc"
    if maturity_band:
        mapping = {
            "Optimized": (5, "Optimized"),
            "Managed": (4, "Managed"),
            "Defined": (3, "Defined"),
            "Developing": (2, "Developing"),
            "Ad-hoc": (1, "Ad-hoc"),
        }
        return mapping.get(maturity_band, (None, None))
    return None, None


def _top_axes(axes: Iterable[AxisScore], *, reverse: bool, limit: int) -> List[str]:
    scored = [axis for axis in axes if axis.score is not None]
    sorted_axes = sorted(scored, key=lambda axis: axis.score or 0, reverse=reverse)
    labels = []
    for axis in sorted_axes:
        label = _axis_label(axis)
        if label not in labels:
            labels.append(label)
        if len(labels) >= limit:
            break
    return labels


def _risk_labels(risks: Iterable[RiskItem]) -> List[str]:
    labels: List[str] = []
    for risk in risks:
        label = risk.scenario or risk.name
        if label and label not in labels:
            labels.append(label)
    return labels


def _recommendations(results: ResultsPayload, gaps: List[str]) -> List[str]:
    recs: List[str] = []
    if results.recommendations:
        for rec in results.recommendations:
            if rec.title and rec.title not in recs:
                recs.append(rec.title)
            if len(recs) >= 3:
                break
    if recs:
        return recs
    for gap in gaps:
        recs.append(f"Prioritize targeted uplift for {gap} to close maturity gaps.")
    if not recs:
        recs.append("Confirm scope, validate evidence, and align remediation with business priorities.")
    return recs[:3]


def _build_summary_text(
    *,
    maturity_band: Optional[str],
    average_score: Optional[float],
    archetype: Optional[str],
    risk_labels: List[str],
) -> str:
    sentences: List[str] = []
    if maturity_band and average_score is not None:
        sentences.append(f"Overall maturity is {maturity_band} with an average score of {average_score}/100.")
    elif maturity_band:
        sentences.append(f"Overall maturity is {maturity_band}.")
    elif average_score is not None:
        sentences.append(f"Average maturity score is {average_score}/100.")
    if archetype:
        sentences.append(f"Current archetype alignment: {archetype}.")
    if risk_labels:
        sentences.append(f"Leading risk themes include {', '.join(risk_labels[:3])}.")
    if not sentences:
        sentences.append("Assessment results received. Executive summary pending richer inputs.")
    return " ".join(sentences)


def _render_html(summary_text: str, findings: List[str], recommendations: List[str]) -> str:
    lines = [
        "<h1>Executive Summary</h1>",
        f"<p>{escape(summary_text)}</p>",
        "<h2>Key Findings</h2>",
        "<ul>",
        *[f"<li>{escape(item)}</li>" for item in findings],
        "</ul>",
        "<h2>High-Level Recommendations</h2>",
        "<ul>",
        *[f"<li>{escape(item)}</li>" for item in recommendations],
        "</ul>",
    ]
    return "\n".join(lines)


def _hash_results(results: ResultsPayload) -> str:
    payload = results.model_dump() if results else {}
    encoded = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_to_response(row: models.ExecutiveSummaryCache) -> ExecutiveSummaryResponse:
    metrics = SummaryMetrics.model_validate(row.metrics) if row.metrics else None
    summary_text = row.summary_text or ""
    key_findings = row.key_findings or []
    recommendations = row.high_level_recommendations or []
    maturity_level, maturity_label = _maturity_level(row.average_score, row.maturity_band)
    sections = [
        SummarySection(title="Executive Summary", body=summary_text),
        SummarySection(title="Key Findings", bullets=key_findings),
        SummarySection(title="High-Level Recommendations", bullets=recommendations),
    ]
    return ExecutiveSummaryResponse(
        assessment_id=row.assessment_id,
        tenant_key=row.tenant_key,
        generated_at=row.generated_at.isoformat() if row.generated_at else datetime.now(timezone.utc).isoformat(),
        generator=row.generator or "template-v1",
        maturity_band=row.maturity_band,
        maturity_level=maturity_level,
        maturity_label=maturity_label,
        average_score=row.average_score,
        summary_text=summary_text,
        summary_html=row.summary_html,
        key_findings=key_findings,
        high_level_recommendations=recommendations,
        sections=sections,
        metrics=metrics,
        pinned_history_id=str(row.pinned_history_id) if row.pinned_history_id else None,
        pinned_at=row.pinned_at.isoformat() if row.pinned_at else None,
    )


def _history_row_to_out(row: models.ExecutiveSummaryHistory, pinned: bool = False) -> ExecutiveSummaryHistoryOut:
    metrics = SummaryMetrics.model_validate(row.metrics) if row.metrics else None
    maturity_level, maturity_label = _maturity_level(row.average_score, row.maturity_band)
    return ExecutiveSummaryHistoryOut(
        id=str(row.id),
        assessment_id=row.assessment_id,
        tenant_key=row.tenant_key,
        generated_at=row.generated_at.isoformat() if row.generated_at else datetime.now(timezone.utc).isoformat(),
        generator=row.generator or "template-v1",
        maturity_band=row.maturity_band,
        maturity_level=maturity_level,
        maturity_label=maturity_label,
        average_score=row.average_score,
        summary_text=row.summary_text or "",
        summary_html=row.summary_html,
        key_findings=row.key_findings or [],
        high_level_recommendations=row.high_level_recommendations or [],
        metrics=metrics,
        pinned=pinned,
    )


def _history_row_to_response(
    row: models.ExecutiveSummaryHistory,
    pinned_history_id: str | None = None,
    pinned_at: datetime | None = None,
) -> ExecutiveSummaryResponse:
    metrics = SummaryMetrics.model_validate(row.metrics) if row.metrics else None
    summary_text = row.summary_text or ""
    key_findings = row.key_findings or []
    recommendations = row.high_level_recommendations or []
    maturity_level, maturity_label = _maturity_level(row.average_score, row.maturity_band)
    sections = [
        SummarySection(title="Executive Summary", body=summary_text),
        SummarySection(title="Key Findings", bullets=key_findings),
        SummarySection(title="High-Level Recommendations", bullets=recommendations),
    ]
    return ExecutiveSummaryResponse(
        assessment_id=row.assessment_id,
        tenant_key=row.tenant_key,
        generated_at=row.generated_at.isoformat() if row.generated_at else datetime.now(timezone.utc).isoformat(),
        generator=row.generator or "template-v1",
        maturity_band=row.maturity_band,
        maturity_level=maturity_level,
        maturity_label=maturity_label,
        average_score=row.average_score,
        summary_text=summary_text,
        summary_html=row.summary_html,
        key_findings=key_findings,
        high_level_recommendations=recommendations,
        sections=sections,
        metrics=metrics,
        pinned_history_id=pinned_history_id,
        pinned_at=pinned_at.isoformat() if pinned_at else None,
    )


def render_summary_html(summary: ExecutiveSummaryResponse) -> str:
    return _render_html(summary.summary_text, summary.key_findings, summary.high_level_recommendations)
