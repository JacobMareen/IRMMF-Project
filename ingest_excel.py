from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models
from app.db import SessionLocal, engine, ensure_pg_extensions


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean_str(x: Any) -> str:
    if x is None:
        return ""
    s = str(x).strip()
    return "" if s.lower() in ("nan", "none") else s


def _to_float(x: Any) -> Optional[float]:
    s = _clean_str(x)
    if not s or s == "-":
        return None
    try:
        return float(s)
    except Exception:
        return None


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
    """Ingest the Excel QuestionBank into Postgres.

This script supports two modes:

1) Single-bank mode (your current schema): dim_* tables have no bank_id.
   - The script TRUNCATES dim_* tables and re-imports.

2) Multi-bank mode (future): dim_* tables have bank_id and relationships.
   - The script can keep multiple banks side-by-side.
"""

    excel_file = os.getenv("IRMMF_EXCEL_FILE", "IRMMF_QuestionBank_v6_with_IntakeModule_v2.4_P0P1.xlsx")
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"{excel_file} not found. Set IRMMF_EXCEL_FILE.")

    print(f"📄 Using Excel file: {excel_file}")

    ensure_pg_extensions()
    models.Base.metadata.create_all(bind=engine)

    source_hash = sha256_file(excel_file)
    version = os.getenv("QUESTION_BANK_VERSION") or _utcnow().strftime("bank-%Y%m%d-%H%M%S")

    q_df = pd.read_excel(excel_file, sheet_name="Questions").fillna("")
    a_df = pd.read_excel(excel_file, sheet_name="AnswerOptions").fillna("")
    intake_q_df = pd.read_excel(excel_file, sheet_name="Intake_Questions").fillna("")
    intake_lists_df = pd.read_excel(excel_file, sheet_name="Intake_Lists").fillna("")

    has_title = "Question Title" in q_df.columns
    print("✅ Found 'Question Title' column in Questions sheet." if has_title else "ℹ️ No 'Question Title' column found.")

    db: Session = SessionLocal()
    try:
        supports_bank_id = _table_has_column(db, "dim_questions", "bank_id") and _table_has_column(db, "dim_answers", "bank_id")
        supports_question_id_fk = _table_has_column(db, "dim_answers", "question_id")
        print(f"🔎 Schema: supports_bank_id={supports_bank_id}, supports_question_id_fk={supports_question_id_fk}")

        bank = models.QuestionBank(version=version, source_file=os.path.basename(excel_file), source_sha256=source_hash)
        db.add(bank)
        db.flush()
        print(f"🆕 Created new bank: {bank.version} ({bank.bank_id})")

        if not supports_bank_id:
            print("⚠️ Your dim_* tables do NOT have bank_id columns yet.")
            print("   Proceeding in single-bank mode: will TRUNCATE and import into the existing tables.")
            if truncate_bank:
                # Single-bank mode must truncate to avoid unique constraint conflicts.
                db.execute(text("TRUNCATE TABLE dim_answers RESTART IDENTITY CASCADE"))
                db.execute(text("TRUNCATE TABLE dim_questions RESTART IDENTITY CASCADE"))
                db.execute(text("TRUNCATE TABLE dim_intake_list_options RESTART IDENTITY CASCADE"))
                db.execute(text("TRUNCATE TABLE dim_intake_questions RESTART IDENTITY CASCADE"))
                db.flush()
            else:
                raise RuntimeError(
                    "Single-bank mode requires TRUNCATE_BANK=1 to avoid unique conflicts."
                )

        # 1) Questions
        print("➡️ Ingesting Questions...")
        q_objects: List[models.Question] = []
        for _, row in q_df.iterrows():
            qid = _clean_str(row.get("Q-ID"))
            if not qid:
                continue
            q_objects.append(	
                models.Question(
                    q_id=_clean_str(row["Q-ID"]),
            domain=_clean_str(row["IRMMF Domain"]),
            # Fallback: if Title is missing, use Short Text, else ID
            question_title=_clean_str(row.get("Question Title", row.get("Short Text", row["Q-ID"]))),
            question_text=_clean_str(row["Question Text"]),
            guidance=_clean_str(row.get("Guidance", "")),
            tier=_clean_str(row.get("Tier", "T1")),
            
            # --- NEURO-ADAPTIVE MAPPING START ---
            branch_type=_clean_str(row.get("BranchType")), 
            # Handle empty thresholds safely
            gate_threshold=float(row["GateThreshold"]) if _clean_str(row.get("GateThreshold")) else None,
            next_if_low=_clean_str(row.get("NextIfLow")),
            next_if_high=_clean_str(row.get("NextIfHigh")),
            next_default=_clean_str(row.get("NextDefault")),
            end_flag=_clean_str(row.get("EndFlag")),
            # --- NEURO-ADAPTIVE MAPPING END ---
            
            # Reporting
            axis1=_clean_str(row.get("Axis1")),
            cw=float(row["CW"]) if _clean_str(row.get("CW")) else 1.0
            ,
            pts_g=_to_float(row.get("Pts_G")),
            pts_e=_to_float(row.get("Pts_E")),
            pts_t=_to_float(row.get("Pts_T")),
            pts_l=_to_float(row.get("Pts_L")),
            pts_h=_to_float(row.get("Pts_H")),
            pts_v=_to_float(row.get("Pts_V")),
            pts_r=_to_float(row.get("Pts_R")),
            pts_f=_to_float(row.get("Pts_F")),
            pts_w=_to_float(row.get("Pts_W"))
        )
            )

        db.bulk_save_objects(q_objects)
        db.flush()
        print(f"✅ Questions ingested: {len(q_objects)}")

        q_lookup: Dict[str, int] = {
            q_id: int(q_db_id)
            for (q_id, q_db_id) in db.execute(text("SELECT q_id, id FROM dim_questions")).all()
        }

        # 2) Answers
        print("➡️ Ingesting Answers...")
        a_objects: List[models.Answer] = []
        for _, row in a_df.iterrows():
            aid = _clean_str(row.get("A-ID"))
            qid = _clean_str(row.get("Q-ID"))
            if not aid or not qid:
                continue
            q_db_id = q_lookup.get(qid)
            if not q_db_id:
                continue
            a_objects.append(
                models.Answer(
                    a_id=aid,
                    q_id=qid,
                    question_id=q_db_id,
                    option_number=int(row["Option #"]) if _clean_str(row.get("Option #")) else None,
                    answer_text=_clean_str(row.get("Answer Option Text")),
                    base_score=float(_clean_str(row.get("BaseScore")) or 0.0),
                    tags=_clean_str(row.get("Tags")) or None,
                    fracture_type=_clean_str(row.get("FractureType")) or None,
                    follow_up_trigger=_clean_str(row.get("FollowUpTrigger")) or None,
                    negative_control=_clean_str(row.get("NegativeControl")) or None,
                    evidence_hint=_clean_str(row.get("Evidence Hint")) or None,
                )
            )
        db.bulk_save_objects(a_objects)
        db.flush()
        print(f"✅ Answers ingested: {len(a_objects)}")

        # 3) Intake Questions
        print("➡️ Ingesting Intake Questions...")
        iq_objects: List[models.IntakeQuestion] = []
        for _, row in intake_q_df.iterrows():
            iqid = _clean_str(row.get("Q-ID"))
            if not iqid:
                continue
            iq_objects.append(
                models.IntakeQuestion(
                    intake_q_id=iqid,
                    section=_clean_str(row.get("Section")) or None,
                    question_text=_clean_str(row.get("Question Text")),
                    guidance=_clean_str(row.get("Guidance")) or None,
                    input_type=_clean_str(row.get("InputType")) or "Single",
                    list_ref=_clean_str(row.get("ListRef")) or None,
                    used_for=_clean_str(row.get("UsedFor")) or None,
                    benchmark_weight=_to_float(row.get("BenchmarkWeight")),
                    depth_logic_ref=_clean_str(row.get("DepthLogicRef")) or None,
                )
            )
        db.bulk_save_objects(iq_objects)
        db.flush()
        print(f"✅ Intake Questions ingested: {len(iq_objects)}")

        # 4) Intake Lists
        print("➡️ Ingesting Intake Lists...")
        list_objects: List[models.IntakeListOption] = []
        for col in intake_lists_df.columns:
            list_ref = _clean_str(col)
            if not list_ref:
                continue
            values = [v for v in intake_lists_df[col].tolist() if _clean_str(v)]
            for idx, v in enumerate(values):
                list_objects.append(
                    models.IntakeListOption(
                        list_ref=list_ref,
                        value=_clean_str(v),
                        display_order=idx,
                    )
                )
        db.bulk_save_objects(list_objects)
        db.flush()
        print(f"✅ Intake List values ingested: {len(list_objects)}")

        db.commit()
        print("\n🎉 Import complete.")
        print(f"Bank version: {bank.version}")
        print(f"Bank id: {bank.bank_id}")
        print(f"Source sha256: {source_hash[:12]}...")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ingest(truncate_bank=bool(os.getenv("TRUNCATE_BANK", "").lower() in ("1", "true", "yes")))
