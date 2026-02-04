import pytest

from app.modules.cases.schemas import CaseStageUpdate, CaseStatusUpdate, CaseTriageForm


def test_valid_case_stage():
    payload = CaseStageUpdate(stage='INTAKE')
    assert payload.stage == 'INTAKE'


def test_invalid_case_stage():
    with pytest.raises(ValueError):
        CaseStageUpdate(stage='UNKNOWN')


def test_valid_case_status():
    payload = CaseStatusUpdate(status='OPEN')
    assert payload.status == 'OPEN'


def test_invalid_case_status():
    with pytest.raises(ValueError):
        CaseStatusUpdate(status='INVALID')


def test_valid_triage_form():
    payload = CaseTriageForm(
        impact=3,
        probability=4,
        risk_score=4,
        outcome='dismiss',
        notes='No escalation required',
        trigger_source='Automated alert',
        business_impact='Limited exposure',
        exposure_summary='Single endpoint',
        data_sensitivity='Internal',
        stakeholders='HR',
        confidence_level='Medium',
        recommended_actions='Monitor only',
    )
    assert payload.outcome == 'DISMISS'
    assert payload.trigger_source == 'Automated alert'


def test_invalid_triage_scores():
    with pytest.raises(ValueError):
        CaseTriageForm(impact=0, probability=3, risk_score=3, outcome='DISMISS')
    with pytest.raises(ValueError):
        CaseTriageForm(impact=3, probability=6, risk_score=3, outcome='DISMISS')
    with pytest.raises(ValueError):
        CaseTriageForm(impact=3, probability=3, risk_score=0, outcome='DISMISS')


def test_invalid_triage_outcome():
    with pytest.raises(ValueError):
        CaseTriageForm(impact=3, probability=3, risk_score=3, outcome='UNKNOWN')
