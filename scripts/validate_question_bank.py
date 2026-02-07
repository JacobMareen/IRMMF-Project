#!/usr/bin/env python3
"""Validate IRMMF question bank integrity.

Checks:
- Unique question IDs and answer IDs
- All answer q_id references exist
- All next_* references exist
- Gatekeepers have next_if_low/high
- option_number sequences start at 0 with no gaps
- Missing answers allowed only for intake/corruption prefixes

Warnings (do not fail build):
- Gatekeepers with identical low/high targets
- Non-monotonic base_score sequences
- High proportion of Unknown fracture types
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

BANK_PATH = Path("app/core/irmmf_bank.json")

ALLOWED_MISSING_ANSWER_PREFIXES = ("INT-", "CORR-")
ALLOWED_BRANCH_TYPES = {"Gatekeeper", "Drilldown", "ShadowProbe", "Linear", "End", "Annex"}


def _fail(errors: list[str]) -> None:
    for err in errors:
        print(f"ERROR: {err}")
    raise SystemExit(1)


def _warn(warnings: Iterable[str]) -> None:
    for warning in warnings:
        print(f"WARNING: {warning}")


def main() -> None:
    if not BANK_PATH.exists():
        _fail([f"Missing bank file: {BANK_PATH}"])

    bank = json.loads(BANK_PATH.read_text())
    questions = bank.get("questions", [])
    answers = bank.get("answers", [])

    errors: list[str] = []
    warnings: list[str] = []

    q_ids = [q.get("q_id") for q in questions]
    q_id_set = {qid for qid in q_ids if qid}
    if len(q_id_set) != len(q_ids):
        errors.append("Duplicate or missing q_id values detected.")

    a_ids = [a.get("a_id") for a in answers]
    a_id_set = {aid for aid in a_ids if aid}
    if len(a_id_set) != len(a_ids):
        errors.append("Duplicate or missing a_id values detected.")

    # Answer references
    bad_answer_refs = [a for a in answers if a.get("q_id") not in q_id_set]
    if bad_answer_refs:
        errors.append(f"{len(bad_answer_refs)} answers reference missing q_id values.")

    # Next references
    ref_fields = ["next_default", "next_if_low", "next_if_high"]
    broken_refs = []
    for q in questions:
        for field in ref_fields:
            target = q.get(field)
            if target and target not in q_id_set:
                broken_refs.append((q.get("q_id"), field, target))
    if broken_refs:
        sample = ", ".join(f"{src}:{field}->{tgt}" for src, field, tgt in broken_refs[:10])
        errors.append(f"{len(broken_refs)} broken next_* references (sample: {sample}).")

    # Gatekeeper integrity
    fake_gatekeepers = []
    for q in questions:
        if str(q.get("branch_type")) == "Gatekeeper":
            if not q.get("next_if_low") or not q.get("next_if_high"):
                errors.append(f"Gatekeeper {q.get('q_id')} missing next_if_low/next_if_high.")
            if q.get("next_if_low") == q.get("next_if_high"):
                fake_gatekeepers.append(q.get("q_id"))

    if fake_gatekeepers:
        warnings.append(
            f"{len(fake_gatekeepers)} Gatekeepers have identical low/high targets (example: {fake_gatekeepers[:5]})."
        )

    # Branch type sanity
    bad_branch = [q.get("q_id") for q in questions if q.get("branch_type") and q.get("branch_type") not in ALLOWED_BRANCH_TYPES]
    if bad_branch:
        warnings.append(f"Unexpected branch_type values on {len(bad_branch)} questions (sample: {bad_branch[:5]}).")

    # Option number sequences
    answers_by_q = defaultdict(list)
    for ans in answers:
        answers_by_q[ans.get("q_id")].append(ans)

    for qid, ans in answers_by_q.items():
        opt_numbers = [a.get("option_number") for a in ans if a.get("option_number") is not None]
        if not opt_numbers:
            continue
        if min(opt_numbers) != 0:
            errors.append(f"{qid}: option_number does not start at 0.")
            continue
        expected = list(range(0, len(opt_numbers)))
        actual = sorted(opt_numbers)
        if actual != expected:
            errors.append(f"{qid}: option_number sequence is not contiguous (expected {expected}, got {actual}).")

    # Missing answers (allow intake/corruption)
    missing_answers = [qid for qid in q_id_set if qid not in answers_by_q]
    unexpected_missing = [qid for qid in missing_answers if not qid.startswith(ALLOWED_MISSING_ANSWER_PREFIXES)]
    if unexpected_missing:
        errors.append(f"{len(unexpected_missing)} questions missing answers outside intake/corruption (sample: {unexpected_missing[:5]}).")

    # Base score warnings
    score_patterns = Counter()
    non_monotonic = []
    for qid, ans in answers_by_q.items():
        scores = [a.get("base_score") for a in ans if a.get("base_score") is not None]
        if not scores:
            continue
        score_patterns[tuple(scores)] += 1
        if any(scores[i] > scores[i + 1] for i in range(len(scores) - 1)):
            non_monotonic.append(qid)
    if non_monotonic:
        warnings.append(f"{len(non_monotonic)} questions have non-monotonic base_score sequences (sample: {non_monotonic[:5]}).")

    # Fracture type coverage
    fracture_total = 0
    fracture_unknown = 0
    for ans in answers:
        ft = ans.get("fracture_type")
        if ft is None:
            continue
        fracture_total += 1
        if ft == "Unknown":
            fracture_unknown += 1
    if fracture_total:
        unknown_pct = (fracture_unknown / fracture_total) * 100
        if unknown_pct > 40:
            warnings.append(f"High Unknown fracture_type rate: {fracture_unknown}/{fracture_total} ({unknown_pct:.1f}%).")

    # Summary
    print(f"Validated {len(q_id_set)} questions and {len(a_id_set)} answers.")

    if warnings:
        _warn(warnings)

    if errors:
        _fail(errors)


if __name__ == "__main__":
    main()
