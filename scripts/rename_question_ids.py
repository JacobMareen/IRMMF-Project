#!/usr/bin/env python3
"""Rename IRMMF question/answer IDs across bank files and the database.

Convention:
- Question IDs become <PREFIX>-Q## (2-digit, sequential per prefix in file order)
- Answer IDs become <NEW_Q_ID>-A## (2-digit, ordered by option_number)

Prefix rules:
- If q_id contains '-Q' followed by digits, prefix is everything before '-Q'
- Otherwise prefix is everything before the last '-'

This script updates:
- app/core/irmmf_bank.json
- app/core/full_question_bank.json
- app/core/intake_data.json
- Text references in .py/.ts/.tsx/.md/.yml/.yaml/.sql
- Database tables (optional --update-db)

A mapping file is written to scripts/question_id_map.json for traceability.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
import sys
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
IRMMF_BANK = ROOT / "app/core/irmmf_bank.json"
FULL_BANK = ROOT / "app/core/full_question_bank.json"
INTAKE_DATA = ROOT / "app/core/intake_data.json"
MAP_OUT = ROOT / "scripts/question_id_map.json"

TEXT_EXTS = {".py", ".ts", ".tsx", ".md", ".yml", ".yaml", ".sql"}
SKIP_DIRS = {".git", "node_modules", "venv", "frontend/node_modules", "IRMMF-Project"}


def _module_prefix(qid: str) -> str:
    # If it already contains -Q\d at the end, use the prefix before -Q
    m = re.match(r"^(.*)-Q\d+$", qid)
    if m:
        return m.group(1)
    # Otherwise strip the final segment (e.g., FRAUD-Q01 -> FRAUD)
    if "-" in qid:
        return qid.rsplit("-", 1)[0]
    return qid


def _build_qid_map(questions: List[dict]) -> Dict[str, str]:
    module_order: List[str] = []
    modules: Dict[str, List[str]] = defaultdict(list)

    for q in questions:
        old = q.get("q_id")
        if not old:
            continue
        prefix = _module_prefix(old)
        if prefix not in modules:
            module_order.append(prefix)
        modules[prefix].append(old)

    q_map: Dict[str, str] = {}
    for prefix in module_order:
        items = modules[prefix]
        for idx, old in enumerate(items, start=1):
            new = f"{prefix}-Q{idx:02d}"
            q_map[old] = new

    if len(set(q_map.values())) != len(q_map):
        raise RuntimeError("q_id mapping contains duplicates; check prefix ordering.")
    return q_map


def _build_aid_map(answers: List[dict], q_map: Dict[str, str]) -> Dict[str, str]:
    answers_by_q: Dict[str, List[dict]] = defaultdict(list)
    for ans in answers:
        answers_by_q[ans.get("q_id")].append(ans)

    a_map: Dict[str, str] = {}
    for old_qid, ans_list in answers_by_q.items():
        new_qid = q_map.get(old_qid, old_qid)
        sorted_ans = sorted(
            ans_list,
            key=lambda a: (
                a.get("option_number") is None,
                a.get("option_number") if a.get("option_number") is not None else 0,
                a.get("a_id") or "",
            ),
        )
        for idx, ans in enumerate(sorted_ans, start=1):
            old_aid = ans.get("a_id")
            new_aid = f"{new_qid}-A{idx:02d}"
            a_map[old_aid] = new_aid

    if len(set(a_map.values())) != len(a_map):
        raise RuntimeError("a_id mapping contains duplicates; check answer ordering.")
    return a_map


def _apply_bank_updates(bank: dict, q_map: Dict[str, str], a_map: Dict[str, str]) -> dict:
    ref_fields = ["next_default", "next_if_low", "next_if_high"]
    for q in bank.get("questions", []):
        old_qid = q.get("q_id")
        if old_qid and old_qid in q_map:
            q["q_id"] = q_map[old_qid]
        for field in ref_fields:
            tgt = q.get(field)
            if tgt in q_map:
                q[field] = q_map[tgt]
    for ans in bank.get("answers", []):
        old_qid = ans.get("q_id")
        if old_qid and old_qid in q_map:
            ans["q_id"] = q_map[old_qid]
        old_aid = ans.get("a_id")
        if old_aid in a_map:
            ans["a_id"] = a_map[old_aid]
    return bank


def _apply_intake_updates(intake: dict, q_map: Dict[str, str]) -> dict:
    for q in intake.get("questions", []):
        old = q.get("intake_q_id")
        if old in q_map:
            q["intake_q_id"] = q_map[old]
    return intake


def _rewrite_text_files(q_map: Dict[str, str]) -> List[Path]:
    # Build one regex to replace any old q_id
    # Sort by length desc to avoid partial overlaps
    keys = sorted(q_map.keys(), key=len, reverse=True)
    if not keys:
        return []
    pattern = re.compile("|".join(re.escape(k) for k in keys))

    changed: List[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix not in TEXT_EXTS:
            continue
        if path.name in {"irmmf_bank.json", "full_question_bank.json", "intake_data.json"}:
            continue
        text = path.read_text()
        new_text = pattern.sub(lambda m: q_map[m.group(0)], text)
        if new_text != text:
            path.write_text(new_text)
            changed.append(path)
    return changed


def _update_database(q_map: Dict[str, str], a_map: Dict[str, str]) -> None:
    from sqlalchemy import text, inspect
    from app.db import engine

    q_rows = [{"old_qid": k, "new_qid": v} for k, v in q_map.items()]
    a_rows = [{"old_aid": k, "new_aid": v} for k, v in a_map.items()]

    with engine.begin() as conn:
        inspector = inspect(conn)
        fk_targets = {"dim_questions", "dim_answers"}
        fk_tables = {"fact_responses", "fact_intake_responses"}
        to_drop: List[Tuple[str, str]] = []
        for table in fk_tables:
            for fk in inspector.get_foreign_keys(table):
                if fk.get("referred_table") in fk_targets:
                    name = fk.get("name")
                    if name:
                        to_drop.append((table, name))
        for table, name in to_drop:
            conn.execute(text(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "{name}"'))

        conn.execute(text("CREATE TEMP TABLE tmp_qid_map (old_qid text primary key, new_qid text) ON COMMIT DROP"))
        conn.execute(text("CREATE TEMP TABLE tmp_aid_map (old_aid text primary key, new_aid text) ON COMMIT DROP"))
        if q_rows:
            conn.execute(text("INSERT INTO tmp_qid_map (old_qid, new_qid) VALUES (:old_qid, :new_qid)"), q_rows)
        if a_rows:
            conn.execute(text("INSERT INTO tmp_aid_map (old_aid, new_aid) VALUES (:old_aid, :new_aid)"), a_rows)

        # Update question IDs and references
        conn.execute(text("UPDATE dim_questions SET q_id = m.new_qid FROM tmp_qid_map m WHERE dim_questions.q_id = m.old_qid"))
        conn.execute(text("UPDATE dim_questions SET next_if_low = m.new_qid FROM tmp_qid_map m WHERE dim_questions.next_if_low = m.old_qid"))
        conn.execute(text("UPDATE dim_questions SET next_if_high = m.new_qid FROM tmp_qid_map m WHERE dim_questions.next_if_high = m.old_qid"))
        conn.execute(text("UPDATE dim_questions SET next_default = m.new_qid FROM tmp_qid_map m WHERE dim_questions.next_default = m.old_qid"))

        # Update answer records
        conn.execute(text("UPDATE dim_answers SET q_id = m.new_qid FROM tmp_qid_map m WHERE dim_answers.q_id = m.old_qid"))
        conn.execute(text("UPDATE dim_answers SET a_id = m.new_aid FROM tmp_aid_map m WHERE dim_answers.a_id = m.old_aid"))

        # Update fact tables (q_id)
        conn.execute(text("UPDATE fact_responses SET q_id = m.new_qid FROM tmp_qid_map m WHERE fact_responses.q_id = m.old_qid"))
        conn.execute(text("UPDATE fact_intake_responses SET q_id = m.new_qid FROM tmp_qid_map m WHERE fact_intake_responses.q_id = m.old_qid"))
        conn.execute(text("UPDATE fact_evidence_responses SET q_id = m.new_qid FROM tmp_qid_map m WHERE fact_evidence_responses.q_id = m.old_qid"))
        conn.execute(text("UPDATE fact_response_audits SET q_id = m.new_qid FROM tmp_qid_map m WHERE fact_response_audits.q_id = m.old_qid"))

        # Update fact tables (a_id) - handle multi-select comma-separated values
        rows = conn.execute(text("SELECT id, a_id FROM fact_responses")).mappings().all()
        updates = []
        for row in rows:
            old = row["a_id"]
            if not old:
                continue
            if "," in old:
                parts = [p.strip() for p in old.split(",") if p.strip()]
                new_parts = [a_map.get(p, p) for p in parts]
                new_val = ",".join(new_parts)
            else:
                new_val = a_map.get(old, old)
            if new_val != old:
                updates.append({"id": row["id"], "a_id": new_val})
        if updates:
            conn.execute(text("UPDATE fact_responses SET a_id = :a_id WHERE id = :id"), updates)

        rows = conn.execute(text("SELECT id, a_id FROM fact_response_audits")).mappings().all()
        updates = []
        for row in rows:
            old = row["a_id"]
            if not old:
                continue
            new_val = a_map.get(old, old)
            if new_val != old:
                updates.append({"id": row["id"], "a_id": new_val})
        if updates:
            conn.execute(text("UPDATE fact_response_audits SET a_id = :a_id WHERE id = :id"), updates)

        # Recreate constraints
        conn.execute(text("ALTER TABLE fact_responses ADD CONSTRAINT fact_responses_q_id_fkey FOREIGN KEY (q_id) REFERENCES dim_questions(q_id)"))
        conn.execute(text("ALTER TABLE fact_responses ADD CONSTRAINT fact_responses_a_id_fkey FOREIGN KEY (a_id) REFERENCES dim_answers(a_id)"))
        conn.execute(text("ALTER TABLE fact_intake_responses ADD CONSTRAINT fact_intake_responses_q_id_fkey FOREIGN KEY (q_id) REFERENCES dim_questions(q_id)"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-db", action="store_true", help="Apply ID changes to the database")
    parser.add_argument("--db-only", action="store_true", help="Only update the database using scripts/question_id_map.json")
    args = parser.parse_args()

    if args.db_only:
        if not MAP_OUT.exists():
            raise SystemExit("Mapping file not found: scripts/question_id_map.json")
        mapping = json.loads(MAP_OUT.read_text())
        q_map = mapping["q_id_map"]
        a_map = mapping["a_id_map"]
    else:
        bank = json.loads(IRMMF_BANK.read_text())
        q_map = _build_qid_map(bank.get("questions", []))
        a_map = _build_aid_map(bank.get("answers", []), q_map)

    if not args.db_only:
        # Update IRMMF bank
        bank = _apply_bank_updates(bank, q_map, a_map)
        IRMMF_BANK.write_text(json.dumps(bank, indent=2))

        # Update full bank
        if FULL_BANK.exists():
            full = json.loads(FULL_BANK.read_text())
            full = _apply_bank_updates(full, q_map, a_map)
            # intake list in full bank
            if "intake_questions" in full:
                for q in full["intake_questions"]:
                    old = q.get("intake_q_id")
                    if old in q_map:
                        q["intake_q_id"] = q_map[old]
            FULL_BANK.write_text(json.dumps(full, indent=2))

        # Update intake data
        if INTAKE_DATA.exists():
            intake = json.loads(INTAKE_DATA.read_text())
            intake = _apply_intake_updates(intake, q_map)
            INTAKE_DATA.write_text(json.dumps(intake, indent=2))

        # Update text references
        changed = _rewrite_text_files(q_map)

        # Persist mapping
        MAP_OUT.write_text(json.dumps({"q_id_map": q_map, "a_id_map": a_map}, indent=2))
    else:
        changed = []

    if args.update_db:
        _update_database(q_map, a_map)

    if not args.db_only:
        print(f"Renamed {len(q_map)} questions and {len(a_map)} answers.")
        print(f"Updated {len(changed)} text files.")
    if args.update_db:
        print("Database updated.")


if __name__ == "__main__":
    main()
