from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.assessment import models
from app.db import SessionLocal, engine, ensure_pg_extensions
from app.core.settings import settings


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _table_has_column(db: Session, table: str, col: str) -> bool:
    r = db.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = :t AND column_name = :c
            LIMIT 1
            """
        ),
        {"t": table, "c": col},
    ).scalar()
    return bool(r)


def ingest(truncate_bank: bool = False) -> None:
    """Ingest the QuestionBank from JSON into Postgres.
    
    Source: app/core/irmmf_bank.json
    """

    json_file = "app/core/irmmf_bank.json"
    if not os.path.exists(json_file):
        raise FileNotFoundError(f"{json_file} not found. Please run migration script first.")

    print(f"📄 Using JSON Bank: {json_file}")

    ensure_pg_extensions()
    # Ensure tables align with latest models (Schema migration happening via create_all)
    models.Base.metadata.create_all(bind=engine)

    source_hash = sha256_file(json_file)
    version = settings.QUESTION_BANK_VERSION or _utcnow().strftime("bank-%Y%m%d-%H%M%S")

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    db: Session = SessionLocal()
    try:
        supports_bank_id = _table_has_column(db, "dim_questions", "bank_id") and _table_has_column(db, "dim_answers", "bank_id")
        
        bank = models.QuestionBank(version=version, source_file=os.path.basename(json_file), source_sha256=source_hash)
        db.add(bank)
        db.flush()
        print(f"🆕 Created new bank: {bank.version} ({bank.bank_id})")

        if not supports_bank_id:
            if truncate_bank:
                print("⚠️ Truncating tables for single-bank mode...")
                db.execute(text("TRUNCATE TABLE dim_answers RESTART IDENTITY CASCADE"))
                db.execute(text("TRUNCATE TABLE dim_questions RESTART IDENTITY CASCADE"))
                db.execute(text("TRUNCATE TABLE dim_list_options RESTART IDENTITY CASCADE"))
                # Clean up legacy table if it exists
                db.execute(text("DROP TABLE IF EXISTS dim_intake_questions CASCADE")) 
                db.flush()
            else:
                raise RuntimeError(
                    "Single-bank mode requires TRUNCATE_BANK=1 to avoid unique conflicts."
                )

        # 1) Questions (Combined)
        print("➡️ Ingesting Questions...")
        q_objects: List[models.Question] = []
        for q in data.get("questions", []):
            qid = q.get("q_id")
            if not qid: continue
            
            # BLACKLIST
            if qid in {"INT-ORG-02", "INT-ASSESS-01", "INT-ASSESS-02", "INT-ASSESS-03"}:
                continue

            q_objects.append(
                models.Question(
                    q_id=qid,
                    domain=q.get("domain"),
                    question_title=q.get("question_title"),
                    question_text=q.get("question_text"),
                    guidance=q.get("guidance"),
                    tier=q.get("tier", "T1"),
                    branch_type=q.get("branch_type"),
                    gate_threshold=q.get("gate_threshold"),
                    next_if_low=q.get("next_if_low"),
                    next_if_high=q.get("next_if_high"),
                    next_default=q.get("next_default"),
                    end_flag=q.get("end_flag"),
                    axis1=q.get("axis1"),
                    cw=q.get("cw", 1.0),
                    pts_g=q.get("pts_g"),
                    pts_e=q.get("pts_e"),
                    pts_t=q.get("pts_t"),
                    pts_l=q.get("pts_l"),
                    pts_h=q.get("pts_h"),
                    pts_v=q.get("pts_v"),
                    pts_r=q.get("pts_r"),
                    pts_f=q.get("pts_f"),
                    pts_w=q.get("pts_w"),
                    # New Unified Fields
                    input_type=q.get("input_type", "Single"),
                    list_ref=q.get("list_ref"),
                    benchmark_weight=q.get("benchmark_weight"),
                    section=q.get("section")
                )
            )

        db.bulk_save_objects(q_objects)
        db.flush()
        print(f"✅ Questions ingested: {len(q_objects)}")

        # Create quick lookup
        q_lookup = {
            q_id: int(q_db_id)
            for (q_id, q_db_id) in db.execute(text("SELECT q_id, id FROM dim_questions")).all()
        }
        
        # Pts lookup
        q_pts_lookup = {}
        for q in data.get("questions", []):
            if q.get("q_id"):
                q_pts_lookup[q["q_id"]] = {k: q.get(k) for k in ["pts_g", "pts_e", "pts_t", "pts_l", "pts_h", "pts_v", "pts_r", "pts_f", "pts_w"]}

        # 2) Answers
        print("➡️ Ingesting Answers...")
        a_objects: List[models.Answer] = []
        for a in data.get("answers", []):
            aid = a.get("a_id")
            qid = a.get("q_id")
            if not aid or not qid: continue
            
            q_db_id = q_lookup.get(qid)
            if not q_db_id: continue

            q_pts = q_pts_lookup.get(qid, {})
            base_score = float(a.get("base_score") or 0.0)
            
            a_objects.append(
                models.Answer(
                    a_id=aid,
                    q_id=qid,
                    question_id=q_db_id,
                    option_number=a.get("option_number"),
                    answer_text=a.get("answer_text"),
                    base_score=base_score,
                    pts_g=base_score * (q_pts.get('pts_g') or 0.0) if q_pts.get('pts_g') else None,
                    pts_e=base_score * (q_pts.get('pts_e') or 0.0) if q_pts.get('pts_e') else None,
                    pts_t=base_score * (q_pts.get('pts_t') or 0.0) if q_pts.get('pts_t') else None,
                    pts_l=base_score * (q_pts.get('pts_l') or 0.0) if q_pts.get('pts_l') else None,
                    pts_h=base_score * (q_pts.get('pts_h') or 0.0) if q_pts.get('pts_h') else None,
                    pts_v=base_score * (q_pts.get('pts_v') or 0.0) if q_pts.get('pts_v') else None,
                    pts_r=base_score * (q_pts.get('pts_r') or 0.0) if q_pts.get('pts_r') else None,
                    pts_f=base_score * (q_pts.get('pts_f') or 0.0) if q_pts.get('pts_f') else None,
                    pts_w=base_score * (q_pts.get('pts_w') or 0.0) if q_pts.get('pts_w') else None,
                    tags=a.get("tags"),
                    fracture_type=a.get("fracture_type"),
                    follow_up_trigger=a.get("follow_up_trigger"),
                    negative_control=a.get("negative_control"),
                    evidence_hint=a.get("evidence_hint"),
                )
            )
        db.bulk_save_objects(a_objects)
        db.flush()
        print(f"✅ Answers ingested: {len(a_objects)}")

        # 3) Intake Lists (Renamed to ListOption)
        print("➡️ Ingesting List Options...")
        list_objects: List[models.ListOption] = []
        # JSON structure might still have "intake_lists" key or I should check what merge script did
        # My merge script step 3320 did NOT rename the key. It kept "intake_lists".
        lists = data.get("intake_lists", {}) 
        # Also check for "list_options" if I decided to rename later
        if not lists: lists = data.get("list_options", {})

        for list_ref, values in lists.items():
            for idx, v in enumerate(values):
                list_objects.append(
                    models.ListOption(
                        list_ref=list_ref,
                        value=v,
                        display_order=idx,
                    )
                )
        db.bulk_save_objects(list_objects)
        db.flush()
        print(f"✅ List Options ingested: {len(list_objects)}")

        db.commit()
        print("\n🎉 Import complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ingest(truncate_bank=settings.TRUNCATE_BANK)
