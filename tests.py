import json
from pathlib import Path
import pytest
from app.core.engines import V6_1BranchingEngine, V6_1ScoringEngine
from app import models
from app.core.risk_engine import (
    apply_curve,
    compute_risks,
    determine_risk_level,
    load_risk_scenarios,
)

# --- FIXTURES: Mock Data for Testing ---

@pytest.fixture
def mock_questions():
    """
    Creates a small graph:
    Q1 (Gatekeeper) -> Q2 (High Path) -> Q4 (Linear)
                    -> Q3 (Low Path)  -> Q4 (Linear)
    """
    return [
        models.Question(
            q_id="Q1", domain="Governance", branch_type="Gatekeeper", 
            next_if_high="Q2", next_if_low="Q3", gate_threshold=3.0
        ),
        models.Question(
            q_id="Q2", domain="Governance", branch_type="Linear", next_default="Q4"
        ),
        models.Question(
            q_id="Q3", domain="Governance", branch_type="Linear", next_default="Q4"
        ),
        models.Question(
            q_id="Q4", domain="Governance", branch_type="Linear", end_flag="Y"
        ),
    ]

# --- 1. SCORING ENGINE TESTS (Recommendation #1) ---

def test_harmonic_mean_math():
    engine = V6_1ScoringEngine()
    
    # Simple average of [5, 5, 5, 1] is 4.0
    # Harmonic mean correctly penalizes the '1' and results in 2.5
    scores = [5.0, 5.0, 5.0, 1.0]
    h_mean = engine.calculate_harmonic_mean(scores)
    
    assert h_mean < 3.0
    assert round(h_mean, 2) == 2.50

def test_confidence_score_adjustment():
    engine = V6_1ScoringEngine()
    
    # Mock data: Question with a raw score of 5 but 0% confidence
    questions = [models.Question(q_id="Q1", domain="Strategy")]
    responses = [models.Response(q_id="Q1", score_achieved=5.0)]
    evidence = [models.EvidenceResponse(q_id="Q1", confidence_score=0.0)] # 0% confidence
    
    analysis = engine.compute_analysis(questions, responses, evidence)
    
    # Adjusted score should be 0 because confidence was 0
    assert analysis['axes'][0]['score'] == 0.0

# --- 2. BRANCHING ENGINE TESTS (Recommendation #5) ---

def test_gatekeeper_high_path(mock_questions):
    engine = V6_1BranchingEngine()
    # Score 4.0 is >= Threshold 3.0
    user_responses = {"Q1": 4.0}
    
    path = engine.calculate_reachable_path(mock_questions, user_responses)
    
    assert "Q2" in path
    assert "Q3" not in path  # Low path should be pruned

def test_gatekeeper_low_path(mock_questions):
    engine = V6_1BranchingEngine()
    # Score 1.0 is < Threshold 3.0
    user_responses = {"Q1": 1.0}
    
    path = engine.calculate_reachable_path(mock_questions, user_responses)
    
    assert "Q3" in path
    assert "Q2" not in path  # High path should be pruned

def test_lookahead_reveals_unanswered_linear_chain(mock_questions):
    engine = V6_1BranchingEngine()
    # User answered Q1 High. 
    # Q2 and Q4 are linear. The engine should "look ahead" and show both in the sidebar.
    user_responses = {"Q1": 5.0}
    
    path = engine.calculate_reachable_path(mock_questions, user_responses)
    
    assert "Q2" in path
    assert "Q4" in path # Q4 is revealed even though Q2 isn't answered yet


# --- 3. RISK ENGINE TESTS ---

def _load_test_data():
    data_path = Path(__file__).resolve().parent / "FIles 4" / "test_data.json"
    with data_path.open("r") as handle:
        return json.load(handle)


def test_risk_scenario_config_loads():
    scenarios = load_risk_scenarios(Path("config/risk_scenarios_simple.yaml"))
    assert len(scenarios) == 10


def test_risk_level_mapping():
    assert determine_risk_level(5, 5)[0] == "RED"
    assert determine_risk_level(3, 5)[0] == "AMBER"
    assert determine_risk_level(2, 5)[0] == "YELLOW"
    assert determine_risk_level(1, 3)[0] == "GREEN"


def test_curve_threshold_samples():
    data = _load_test_data()
    inputs = data["curve_test_data"]["threshold_curve"]["inputs"]
    expected = data["curve_test_data"]["threshold_curve"]["expected_outputs"]
    for raw, exp in zip(inputs, expected):
        assert apply_curve(raw, "threshold") == pytest.approx(exp, abs=0.01)


def test_full_risk_calculation_case_1():
    data = _load_test_data()
    case = data["test_case_1"]
    axis_scores = case["axis_scores"]
    results, _ = compute_risks(axis_scores, case["intake_tags"])
    by_id = {r["scenario_id"]: r for r in results}
    assert len(results) == 10
    ip_theft = by_id["IP_Theft"]
    assert ip_theft["impact"] == case["expected_results"]["IP_Theft"]["impact"]
    assert ip_theft["risk_level"] == case["expected_results"]["IP_Theft"]["risk_level"]
