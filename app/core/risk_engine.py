"""Scenario-based risk scoring driven by axis maturity + intake tags."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

AXES = ("G", "E", "T", "L", "H", "V", "R", "F", "W")
CURVE_TYPES = {"threshold", "standard", "logarithmic", "enhanced_sigmoid"}
RISK_SCALE_MAX = 7
IMPACT_BASE_MAX = RISK_SCALE_MAX
AXIS_SCALE_MAX = 6.0


def _default_config_path() -> Path:
    # Config lives at repo-root ./config to keep it editable without code changes.
    base_dir = Path(__file__).resolve().parent
    repo_root = base_dir.parent.parent
    return repo_root / "config" / "risk_scenarios_simple.yaml"


def _resolve_config_path(path: Optional[str]) -> Path:
    config_root = _default_config_path().parent
    if not path:
        return _default_config_path()
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = config_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(config_root)
    except ValueError as exc:
        raise ValueError("Config path must resolve under config/") from exc
    return resolved


@lru_cache(maxsize=1)
def load_risk_scenarios(path: Optional[str] = None) -> List[Dict[str, Any]]:
    config_path = _resolve_config_path(path)
    with open(config_path, "r") as handle:
        config = yaml.safe_load(handle) or {}
    scenarios = config.get("risks") or []
    _validate_scenarios(scenarios)
    return scenarios


def _validate_scenarios(scenarios: Iterable[Dict[str, Any]]) -> None:
    # Enforces basic invariants to avoid silent mis-scoring.
    for scenario in scenarios:
        scenario_id = scenario.get("id", "<unknown>")
        axes = scenario.get("axes") or {}
        curves = scenario.get("curves") or {}
        impact_rules = scenario.get("impact_rules") or []

        weight_total = sum(float(value) for value in axes.values())
        if not (0.99 <= weight_total <= 1.01):
            raise ValueError(f"{scenario_id}: axis weights sum to {weight_total:.3f}")

        for axis, curve_config in curves.items():
            if axis not in AXES:
                raise ValueError(f"{scenario_id}: invalid axis {axis}")
            
            if isinstance(curve_config, str):
                curve_type = curve_config
            elif isinstance(curve_config, dict):
                curve_type = curve_config.get("type")
            else:
                raise ValueError(f"{scenario_id}: invalid curve config for axis {axis}")

            if curve_type not in CURVE_TYPES:
                raise ValueError(f"{scenario_id}: invalid curve type {curve_type}")

        if not impact_rules:
            raise ValueError(f"{scenario_id}: missing impact rules")

        if not any(rule.get("condition") == "default" for rule in impact_rules):
            raise ValueError(f"{scenario_id}: missing default impact rule")


def _clip_score(score: float) -> float:
    return max(0.0, min(AXIS_SCALE_MAX, score))


def _scale_impact(value: int) -> int:
    if IMPACT_BASE_MAX == RISK_SCALE_MAX:
        return value
    scaled = round(((value - 1) / (IMPACT_BASE_MAX - 1)) * (RISK_SCALE_MAX - 1) + 1)
    return int(max(1, min(RISK_SCALE_MAX, scaled)))


def apply_curve(axis_score: float, curve_type: str, k: float = 1.2) -> float:
    score = _clip_score(axis_score)
    if curve_type == "threshold":
        if score < 3.0:
            return 0.1
        return 0.5 + (score - 3.0) * 0.15
    if curve_type == "logarithmic":
        # More pronounced curve, faster initial rise
        return 1.0 - math.exp(-0.6 * score)
    if curve_type == "enhanced_sigmoid":
        # Sigmoid with configurable steepness
        return 1.0 / (1.0 + math.exp(-k * (score - 3.0)))
    # Standard sigmoid as default
    return 1.0 / (1.0 + math.exp(-1.2 * (score - 3.0)))


def evaluate_condition(condition: str, intake_tags: Iterable[str]) -> bool:
    if condition == "default":
        return True

    tags = set(tag.strip() for tag in intake_tags if tag)
    if " OR " in condition:
        return any(part.strip() in tags for part in condition.split(" OR "))
    if " AND " in condition:
        return all(part.strip() in tags for part in condition.split(" AND "))
    return condition.strip() in tags

MODIFIER_MAP = {
    "+1": lambda x: x + 1,
    "-1": lambda x: x - 1,
    "x2": lambda x: x * 2,
    "/2": lambda x: x / 2,
}

def calculate_impact(
    scenario: Dict[str, Any],
    intake_tags: Iterable[str],
    responses: Dict[str, float] | None = None,
) -> int:
    rules = scenario.get("impact_rules") or []
    impact = 1
    for rule in rules:
        if rule.get("condition") == "default":
            impact = int(rule.get("value", 1))
            break

    for rule in rules:
        condition = rule.get("condition")
        if condition == "default":
            continue
        if evaluate_condition(condition, intake_tags):
            value = rule.get("value")
            if isinstance(value, str) and value in MODIFIER_MAP:
                impact = MODIFIER_MAP[value](impact)
            else:
                impact = int(value)
            break
    
    # Process question-based modifiers
    if responses:
        modifiers = scenario.get("impact_modifiers", {})
        for q_id, modifier_rules in modifiers.items():
            if q_id in responses:
                answer_score = responses[q_id]
                for rule in modifier_rules:
                    if "lt" in rule and answer_score < rule["lt"]:
                        impact = MODIFIER_MAP[rule["adjust"]](impact)
                    elif "gt" in rule and answer_score > rule["gt"]:
                        impact = MODIFIER_MAP[rule["adjust"]](impact)

    impact = max(1, min(IMPACT_BASE_MAX, impact))
    return _scale_impact(impact)


def calculate_mitigation_score(scenario: Dict[str, Any], axis_scores: Dict[str, float]) -> float:
    # Weighted blend of axis scores after applying scenario-specific curves.
    mitigation = 0.0
    axes = scenario.get("axes") or {}
    curves = scenario.get("curves") or {}
    for axis, weight in axes.items():
        axis_score = axis_scores.get(axis, 0.0)
        
        curve_config = curves.get(axis, {"type": "standard"})
        if isinstance(curve_config, str):
            curve_type = curve_config
            k = 1.2 # default k
        else:
            curve_type = curve_config.get("type", "standard")
            k = float(curve_config.get("k", 1.2))

        mitigation += float(weight) * apply_curve(axis_score, curve_type, k=k)
    return max(0.0, min(1.0, mitigation))


def calculate_likelihood(mitigation_score: float) -> int:
    raw_likelihood = RISK_SCALE_MAX - (mitigation_score * (RISK_SCALE_MAX - 1))
    return max(1, min(RISK_SCALE_MAX, int(round(raw_likelihood))))


def determine_risk_level(likelihood: int, impact: int) -> Tuple[str, int]:
    risk_score = likelihood * impact
    if risk_score >= 39:
        return "RED", risk_score
    if risk_score >= 24:
        return "AMBER", risk_score
    if risk_score >= 12:
        return "YELLOW", risk_score
    return "GREEN", risk_score


def calculate_axis_scores(
    responses: Dict[str, float] | Iterable[Any],
    questions: Iterable[Any],
) -> Dict[str, float]:
    if isinstance(responses, dict):
        response_map = responses
    else:
        response_map = {r.q_id: r.score_achieved for r in responses}

    q_map = {q.q_id: q for q in questions}
    axis_scores: Dict[str, float] = {}
    for axis in AXES:
        weighted_sum = 0.0
        total_weight = 0.0
        axis_attr = f"pts_{axis.lower()}"
        for q_id, answer_score in response_map.items():
            question = q_map.get(q_id)
            if not question:
                continue
            axis_weight = getattr(question, axis_attr, 0.0) or 0.0
            if axis_weight <= 0:
                continue
            weighted_sum += float(answer_score) * axis_weight
            total_weight += axis_weight
        axis_scores[axis] = _clip_score(weighted_sum / total_weight) if total_weight > 0 else 0.0
    return axis_scores


def _identify_key_gaps(scenario: Dict[str, Any], axis_scores: Dict[str, float]) -> List[str]:
    axis_names = {
        "G": "Governance",
        "E": "Execution",
        "T": "Technical",
        "L": "Legal",
        "H": "Human",
        "V": "Visibility",
        "R": "Resilience",
        "F": "Friction",
        "W": "Control Lag",
    }
    gaps: List[str] = []
    for axis, weight in (scenario.get("axes") or {}).items():
        if weight < 0.15:
            continue
        score = axis_scores.get(axis, 0.0)
        if score < 4.5:
            gaps.append(f"{axis_names.get(axis, axis)}: {score:.1f}/6")
    return gaps[:3]


def compute_risks(
    axis_scores: Dict[str, float],
    intake_tags: Optional[Iterable[str]] = None,
    scenarios: Optional[List[Dict[str, Any]]] = None,
    responses: Optional[Dict[str, float]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    tags = list(intake_tags or [])
    scenarios = scenarios or load_risk_scenarios()
    results: List[Dict[str, Any]] = []

    for scenario in scenarios:
        mitigation = calculate_mitigation_score(scenario, axis_scores)
        likelihood = calculate_likelihood(mitigation)
        impact = calculate_impact(scenario, tags, responses)
        risk_level, risk_score = determine_risk_level(likelihood, impact)
        results.append({
            "scenario_id": scenario.get("id"),
            "scenario": scenario.get("name"),
            "category": scenario.get("category"),
            "description": scenario.get("description"),
            "likelihood": likelihood,
            "impact": impact,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "mitigation_score": round(mitigation, 3),
            "key_gaps": _identify_key_gaps(scenario, axis_scores),
        })

    results.sort(
        key=lambda item: (
            item["risk_score"],
            item.get("mitigation_score", 0.0),
        ),
        reverse=True,
    )
    top = results[:5]
    return results, top
