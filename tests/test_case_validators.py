import pytest

from app.modules.cases.schemas import CaseStageUpdate, CaseStatusUpdate


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
