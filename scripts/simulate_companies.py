#!/usr/bin/env python3
"""
Simulate assessment runs for synthetic company profiles and assert logical results.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Profile:
    name: str
    strategy: str  # min | mid | max
    expected_trust_range: Tuple[float, float]
    industry: str
    region: str
    size_band: str
    revenue_band: str
    regulated: bool
    intake_overrides: Dict[str, str]
    list_ref_overrides: Dict[str, str]
    multi_pick: int = 2


def _request_json(method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
        if not raw:
            return None
        return json.loads(raw.decode("utf-8"))


def get_json(url: str) -> Any:
    return _request_json("GET", url)


def post_json(url: str, payload: Dict[str, Any]) -> Any:
    return _request_json("POST", url, payload)


def choose_option(options: List[Dict[str, Any]], strategy: str) -> Dict[str, Any]:
    scored = []
    for opt in options:
        score = opt.get("base_score")
        if score is None:
            score = 0.0
        scored.append((float(score), opt))
    scored.sort(key=lambda x: x[0])
    if not scored:
        return {}
    if strategy == "min":
        return scored[0][1]
    if strategy == "max":
        return scored[-1][1]
    return scored[len(scored) // 2][1]

def _pick_option_by_preference(options: List[Dict[str, Any]], preferred: str) -> Optional[str]:
    if not options:
        return None
    preferred_lower = preferred.lower()
    for opt in options:
        value = str(opt.get("value") or "")
        if preferred_lower in value.lower():
            return value
    return str(options[0].get("value") or "")


def _pick_multi(options: List[Dict[str, Any]], count: int) -> str:
    values = [str(opt.get("value") or "") for opt in options if opt.get("value") is not None]
    values = [value for value in values if value]
    if not values:
        return ""
    return ", ".join(values[:count])


def build_intake_answers(profile: Profile, intake_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    answers: Dict[str, Any] = {
        "industry": profile.industry,
        "region": profile.region,
        "size_band": profile.size_band,
        "revenue_band": profile.revenue_band,
    }
    for q in intake_questions:
        intake_q_id = q.get("intake_q_id")
        if not intake_q_id:
            continue
        if intake_q_id in profile.intake_overrides:
            answers[intake_q_id] = profile.intake_overrides[intake_q_id]
            continue
        if intake_q_id in answers:
            continue
        if intake_q_id.startswith("reg_"):
            answers[intake_q_id] = "yes" if profile.regulated else "no"
            continue
        options = q.get("options") or []
        list_ref = q.get("list_ref") or ""
        input_type = (q.get("input_type") or "").lower()
        if options:
            preferred = profile.list_ref_overrides.get(list_ref) or ""
            if input_type in {"multi_select", "multi-select", "checkbox", "multi"}:
                answers[intake_q_id] = _pick_multi(options, profile.multi_pick)
                continue
            if preferred:
                picked = _pick_option_by_preference(options, preferred)
                if picked is not None:
                    answers[intake_q_id] = picked
                    continue
            answers[intake_q_id] = _pick_option_by_preference(options, "") or ""
            continue
        if input_type in {"number", "numeric"}:
            answers[intake_q_id] = "1000"
        else:
            answers[intake_q_id] = "Unknown"
    return answers


def validate_analysis(payload: Dict[str, Any], profile: Profile) -> List[str]:
    issues = []
    summary = payload.get("summary") or {}
    trust = summary.get("trust_index")
    if trust is None:
        issues.append("missing trust_index")
    else:
        lo, hi = profile.expected_trust_range
        if not (lo <= trust <= hi):
            issues.append(f"trust_index {trust} out of expected range {lo}-{hi}")
    axes = payload.get("axes") or []
    if not axes:
        issues.append("axes missing or empty")
    for axis in axes:
        score = axis.get("score")
        if score is None or score < 0 or score > 100:
            issues.append(f"axis score out of range: {axis}")
    for item in payload.get("risk_heatmap") or []:
        likelihood = item.get("likelihood")
        impact = item.get("impact")
        if likelihood is not None and not (1 <= likelihood <= 7):
            issues.append(f"risk likelihood out of range: {item}")
        if impact is not None and not (1 <= impact <= 7):
            issues.append(f"risk impact out of range: {item}")
    return issues


def validate_intake(payload: Dict[str, Any], profile: Profile) -> List[str]:
    issues = []
    tags = payload.get("benchmark_tags") or {}
    if not tags:
        issues.append("missing benchmark_tags")
        return issues
    industry = tags.get("industry")
    region = tags.get("region")
    size = tags.get("size_band")
    if industry is None or profile.industry.lower() not in str(industry).lower():
        issues.append(f"benchmark industry mismatch: {industry}")
    if region is None or profile.region.lower() not in str(region).lower():
        issues.append(f"benchmark region mismatch: {region}")
    if size is None or profile.size_band.lower() not in str(size).lower():
        issues.append(f"benchmark size_band mismatch: {size}")
    if "depth_suggestion" not in payload:
        issues.append("missing depth_suggestion")
    return issues


def run_profile(
    base_url: str,
    profile: Profile,
    questions: List[Dict[str, Any]],
    intake_questions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    assessment = post_json(f"{base_url}/api/v1/assessment/new", {"user_id": f"sim_{profile.name}"})
    assessment_id = assessment.get("assessment_id")
    if not assessment_id:
        raise RuntimeError(f"Failed to create assessment for {profile.name}")

    intake_answers = build_intake_answers(profile, intake_questions)
    intake_submit = post_json(
        f"{base_url}/api/v1/intake/submit",
        {"assessment_id": assessment_id, "answers": intake_answers},
    )

    for q in questions:
        opts = q.get("options") or []
        picked = choose_option(opts, profile.strategy)
        if not picked:
            continue
        payload = {
            "assessment_id": assessment_id,
            "q_id": q.get("q_id"),
            "a_id": picked.get("a_id"),
            "score": picked.get("base_score") or 0.0,
            "pack_id": q.get("domain") or "",
            "is_deferred": False,
            "is_flagged": False,
            "origin": "adaptive",
        }
        post_json(f"{base_url}/api/v1/assessment/submit", payload)

    analysis = get_json(f"{base_url}/responses/analysis/{assessment_id}")
    return {"assessment_id": assessment_id, "analysis": analysis, "intake": intake_submit}


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate assessment runs for synthetic profiles.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of questions (0 = all).")
    args = parser.parse_args()

    questions = get_json(f"{args.base_url}/api/v1/questions/all") or []
    if args.limit:
        questions = questions[: args.limit]
    intake_questions = get_json(f"{args.base_url}/api/v1/intake/start") or []

    profiles = [
        Profile(
            name="low",
            strategy="min",
            expected_trust_range=(0, 40),
            industry="Retail",
            region="North America",
            size_band="Small",
            revenue_band="Under 10M",
            regulated=False,
            intake_overrides={},
            list_ref_overrides={"IndustryCode": "Retail", "Region": "North America"},
        ),
        Profile(
            name="mid",
            strategy="mid",
            expected_trust_range=(20, 80),
            industry="Manufacturing",
            region="Europe",
            size_band="Mid",
            revenue_band="50M-250M",
            regulated=False,
            intake_overrides={},
            list_ref_overrides={"IndustryCode": "Manufacturing", "Region": "Europe"},
        ),
        Profile(
            name="high",
            strategy="max",
            expected_trust_range=(60, 100),
            industry="Financial Services",
            region="Europe",
            size_band="Enterprise",
            revenue_band="1B+",
            regulated=True,
            intake_overrides={},
            list_ref_overrides={"IndustryCode": "Financial", "Region": "Europe"},
        ),
        Profile(
            name="healthcare_core",
            strategy="mid",
            expected_trust_range=(25, 85),
            industry="Healthcare",
            region="North America",
            size_band="Enterprise",
            revenue_band="250M-1B",
            regulated=True,
            intake_overrides={},
            list_ref_overrides={"IndustryCode": "Health", "Region": "North America"},
        ),
        Profile(
            name="tech_startup",
            strategy="min",
            expected_trust_range=(0, 50),
            industry="Technology",
            region="Asia Pacific",
            size_band="Small",
            revenue_band="Under 10M",
            regulated=False,
            intake_overrides={},
            list_ref_overrides={"IndustryCode": "Tech", "Region": "Asia"},
        ),
    ]

    results = {}
    for profile in profiles:
        result = run_profile(args.base_url, profile, questions, intake_questions)
        issues = validate_analysis(result["analysis"], profile)
        issues.extend(validate_intake(result.get("intake") or {}, profile))
        results[profile.name] = {
            "assessment_id": result["assessment_id"],
            "issues": issues,
            "trust_index": (result["analysis"].get("summary") or {}).get("trust_index"),
        }
        time.sleep(0.1)

    low = results["low"]["trust_index"]
    mid = results["mid"]["trust_index"]
    high = results["high"]["trust_index"]
    ordering_ok = low is not None and mid is not None and high is not None and low <= mid <= high

    print(json.dumps(results, indent=2))
    if not ordering_ok:
        print("Assertion failed: trust_index ordering low <= mid <= high", file=sys.stderr)
        return 2
    if any(results[p]["issues"] for p in results):
        print("Assertion failed: validation issues detected", file=sys.stderr)
        return 3
    print("All assertions passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
