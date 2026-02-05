from __future__ import annotations

import uuid

from app import models


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


def _payload(assessment_id: str, score: float = 42.0):
    return {
        "assessment_id": assessment_id,
        "results": {
            "axes": [
                {"axis": "Governance", "score": score},
                {"axis": "Culture", "score": score - 5},
            ]
        },
        "include_html": True,
    }


def test_executive_summary_endpoints(client, db):
    _ensure_ai_tables(db)
    tenant_key = "default"
    assessment_id = f"test-{uuid.uuid4()}"
    _cleanup_ai_rows(db, tenant_key, assessment_id)

    resp = client.post("/api/v1/ai/executive-summary", json=_payload(assessment_id, 40))
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("summary_text")

    cached = client.get(f"/api/v1/ai/executive-summary/{assessment_id}")
    assert cached.status_code == 200
    cached_data = cached.json()
    assert cached_data.get("summary_text")

    history = client.get(f"/api/v1/ai/executive-summary/{assessment_id}/history")
    assert history.status_code == 200
    history_rows = history.json()
    assert history_rows
    history_id = history_rows[0]["id"]

    pin_resp = client.post(f"/api/v1/ai/executive-summary/{assessment_id}/pin", json={"history_id": history_id})
    assert pin_resp.status_code == 200
    pin_data = pin_resp.json()
    assert pin_data.get("pinned_history_id") == history_id

    history_after_pin = client.get(f"/api/v1/ai/executive-summary/{assessment_id}/history").json()
    assert any(item.get("pinned") for item in history_after_pin)

    pdf_resp = client.get(f"/api/v1/ai/executive-summary/history/{history_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"].startswith("application/pdf")

    docx_resp = client.get(f"/api/v1/ai/executive-summary/history/{history_id}/docx")
    assert docx_resp.status_code == 200
    assert docx_resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    html_resp = client.get(f"/api/v1/ai/executive-summary/history/{history_id}/html")
    assert html_resp.status_code == 200
    assert html_resp.headers["content-type"].startswith("text/html")

    unpin_resp = client.delete(f"/api/v1/ai/executive-summary/{assessment_id}/pin")
    assert unpin_resp.status_code == 200

    history_after_unpin = client.get(f"/api/v1/ai/executive-summary/{assessment_id}/history").json()
    assert not any(item.get("pinned") for item in history_after_unpin)

    _cleanup_ai_rows(db, tenant_key, assessment_id)
