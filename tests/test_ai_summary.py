from __future__ import annotations

import uuid

from app import models
from app.modules.ai.schemas import AxisScore, ExecutiveSummaryRequest, ResultsPayload
from app.modules.ai.service import ExecutiveSummaryService


def _ensure_ai_tables(db) -> None:
    engine = db.get_bind()
    models.ExecutiveSummaryCache.__table__.create(bind=engine, checkfirst=True)
    models.ExecutiveSummaryHistory.__table__.create(bind=engine, checkfirst=True)


def _cleanup_ai_rows(db, tenant_key: str, assessment_id: str) -> None:
    db.query(models.ExecutiveSummaryHistory).filter(
        models.ExecutiveSummaryHistory.tenant_key == tenant_key,
        models.ExecutiveSummaryHistory.assessment_id == assessment_id,
    ).delete()
    db.query(models.ExecutiveSummaryCache).filter(
        models.ExecutiveSummaryCache.tenant_key == tenant_key,
        models.ExecutiveSummaryCache.assessment_id == assessment_id,
    ).delete()
    db.commit()


def _payload_for(score: float) -> ResultsPayload:
    return ResultsPayload(axes=[AxisScore(axis="Governance", score=score)])


def test_executive_summary_cache_and_history(db):
    _ensure_ai_tables(db)
    tenant_key = "test-tenant"
    assessment_id = f"test-{uuid.uuid4()}"
    _cleanup_ai_rows(db, tenant_key, assessment_id)

    service = ExecutiveSummaryService(db)

    base_request = ExecutiveSummaryRequest(
        assessment_id=assessment_id,
        results=_payload_for(40),
        include_html=False,
    )

    summary1 = service.generate(base_request, tenant_key)
    assert summary1.summary_text
    assert service.get_cached_summary(tenant_key, assessment_id)
    assert len(service.list_history(tenant_key, assessment_id)) == 1

    service.generate(base_request, tenant_key)
    assert len(service.list_history(tenant_key, assessment_id)) == 1

    updated_request = ExecutiveSummaryRequest(
        assessment_id=assessment_id,
        results=_payload_for(80),
        include_html=False,
    )
    service.generate(updated_request, tenant_key)
    assert len(service.list_history(tenant_key, assessment_id)) == 2

    forced_request = ExecutiveSummaryRequest(
        assessment_id=assessment_id,
        results=_payload_for(80),
        include_html=False,
        force_refresh=True,
    )
    service.generate(forced_request, tenant_key)
    assert len(service.list_history(tenant_key, assessment_id)) == 3

    _cleanup_ai_rows(db, tenant_key, assessment_id)
