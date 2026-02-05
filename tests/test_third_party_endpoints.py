from __future__ import annotations

import uuid

from app.modules.third_party import models as third_party_models


def _ensure_third_party_table(db) -> None:
    engine = db.get_bind()
    third_party_models.ThirdPartyAssessment.__table__.create(bind=engine, checkfirst=True)


def _cleanup_rows(db, tenant_key: str, assessment_id: str) -> None:
    db.query(third_party_models.ThirdPartyAssessment).filter(
        third_party_models.ThirdPartyAssessment.tenant_key == tenant_key,
        third_party_models.ThirdPartyAssessment.assessment_id == assessment_id,
    ).delete()
    db.commit()


def test_third_party_questions_endpoint(client, db):
    _ensure_third_party_table(db)
    resp = client.get("/api/v1/third-party/questions/all")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data, "Question bank should not be empty."
    sample = data[0]
    assert "q_id" in sample
    assert "question_text" in sample
    assert "options" in sample
    assert isinstance(sample["options"], list)
    assert sample["options"], "Question options should not be empty."
    opt = sample["options"][0]
    assert "a_id" in opt
    assert "label" in opt
    assert "score" in opt


def test_third_party_create_and_score(client, db):
    _ensure_third_party_table(db)
    tenant_key = "default"
    assessment_id = f"TPR-{uuid.uuid4().hex[:8].upper()}"
    _cleanup_rows(db, tenant_key, assessment_id)

    create_resp = client.post(
        f"/api/v1/third-party/assessments?assessment_id={assessment_id}",
        json={"partner_name": "Acme Cloud"},
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    third_party_id = created["id"]
    assert created["assessment_id"] == assessment_id
    assert created["partner_name"] == "Acme Cloud"

    update_resp = client.patch(
        f"/api/v1/third-party/assessments/{third_party_id}",
        json={"status": "active", "summary": "Initial vendor review"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["status"] == "active"
    assert updated["summary"] == "Initial vendor review"

    questions_resp = client.get("/api/v1/third-party/questions/all")
    assert questions_resp.status_code == 200
    questions = questions_resp.json()
    assert questions

    responses = []
    for question in questions[:2]:
        options = question.get("options") or []
        if not options:
            continue
        responses.append({"q_id": question["q_id"], "a_id": options[0]["a_id"]})

    assert responses, "Expected at least one response for scoring."

    score_resp = client.post(
        f"/api/v1/third-party/assessments/{third_party_id}/responses",
        json={"responses": responses},
    )
    assert score_resp.status_code == 200
    scored = score_resp.json()
    assert scored.get("score") is not None

    analysis_resp = client.get(f"/api/v1/third-party/assessments/{third_party_id}/analysis")
    assert analysis_resp.status_code == 200
    analysis = analysis_resp.json()
    assert analysis.get("partner_id") == third_party_id
    assert analysis.get("score") is not None
    assert analysis.get("answered") >= 1
    assert analysis.get("total") >= analysis.get("answered")
    assert analysis.get("coverage") >= 0
    assert analysis.get("risk_band")

    _cleanup_rows(db, tenant_key, assessment_id)
