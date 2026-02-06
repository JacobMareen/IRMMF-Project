import pandas as pd
import json
import os
import sys

# Paths
EXCEL_FILE = "IRMMF_QuestionBank_v10_StreamlinedIntake_20260117.xlsx"
OUTPUT_FILE = "app/core/full_question_bank.json"

def clean_str(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    if s.lower() in ("nan", "none", ""):
        return None
    return s

def to_float(x):
    s = clean_str(x)
    if not s or s == "-":
        return None
    try:
        return float(s)
    except:
        return None

def migrate():
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: {EXCEL_FILE} not found.")
        sys.exit(1)

    print(f"Reading {EXCEL_FILE}...")
    
    # 1. Questions
    q_df = pd.read_excel(EXCEL_FILE, sheet_name="Questions").fillna("")
    questions = []
    
    for _, row in q_df.iterrows():
        qid = clean_str(row.get("Q-ID"))
        if not qid:
            continue
            
        q_obj = {
            "q_id": qid,
            "domain": clean_str(row.get("IRMMF Domain")),
            "question_title": clean_str(row.get("Question Title", row.get("Short Text", qid))),
            "question_text": clean_str(row.get("Question Text")),
            "guidance": clean_str(row.get("Guidance")),
            "tier": clean_str(row.get("Tier", "T1")),
            "branch_type": clean_str(row.get("BranchType")),
            "gate_threshold": to_float(row.get("GateThreshold")),
            "next_if_low": clean_str(row.get("NextIfLow")),
            "next_if_high": clean_str(row.get("NextIfHigh")),
            "next_default": clean_str(row.get("NextDefault")),
            "end_flag": clean_str(row.get("EndFlag")),
            "axis1": clean_str(row.get("Axis1")),
            "cw": to_float(row.get("CW")) or 1.0,
            "pts_g": to_float(row.get("Pts_G")),
            "pts_e": to_float(row.get("Pts_E")),
            "pts_t": to_float(row.get("Pts_T")),
            "pts_l": to_float(row.get("Pts_L")),
            "pts_h": to_float(row.get("Pts_H")),
            "pts_v": to_float(row.get("Pts_V")),
            "pts_r": to_float(row.get("Pts_R")),
            "pts_f": to_float(row.get("Pts_F")),
            "pts_w": to_float(row.get("Pts_W"))
        }
        # Remove None values to keep JSON clean
        questions.append({k: v for k, v in q_obj.items() if v is not None})

    print(f"Processed {len(questions)} questions.")

    # 2. Answers
    a_df = pd.read_excel(EXCEL_FILE, sheet_name="AnswerOptions").fillna("")
    answers = []
    
    for _, row in a_df.iterrows():
        aid = clean_str(row.get("A-ID"))
        qid = clean_str(row.get("Q-ID"))
        if not aid or not qid:
            continue
            
        a_obj = {
            "a_id": aid,
            "q_id": qid,
            "option_number": int(row["Option #"]) if clean_str(row.get("Option #")) else None,
            "answer_text": clean_str(row.get("Answer Option Text")),
            "base_score": to_float(row.get("BaseScore")),
            "tags": clean_str(row.get("Tags")),
            "fracture_type": clean_str(row.get("FractureType")),
            "follow_up_trigger": clean_str(row.get("FollowUpTrigger")),
            "negative_control": clean_str(row.get("NegativeControl")),
            "evidence_hint": clean_str(row.get("Evidence Hint"))
        }
        answers.append({k: v for k, v in a_obj.items() if v is not None})

    print(f"Processed {len(answers)} answers.")
    
    # 3. Intake (Keep creating it for completeness, even if we override later)
    intake_q_df = pd.read_excel(EXCEL_FILE, sheet_name="Intake_Questions").fillna("")
    intake_questions = []
    
    for _, row in intake_q_df.iterrows():
        iqid = clean_str(row.get("Q-ID"))
        if not iqid:
            continue
            
        iq_obj = {
            "intake_q_id": iqid,
            "section": clean_str(row.get("Section")),
            "question_text": clean_str(row.get("Question Text")),
            "guidance": clean_str(row.get("Guidance")),
            "input_type": clean_str(row.get("InputType")) or "Single",
            "list_ref": clean_str(row.get("ListRef")),
            "used_for": clean_str(row.get("UsedFor")),
            "benchmark_weight": to_float(row.get("BenchmarkWeight")),
            "depth_logic_ref": clean_str(row.get("DepthLogicRef"))
        }
        intake_questions.append({k: v for k, v in iq_obj.items() if v is not None})
        
    print(f"Processed {len(intake_questions)} intake questions.")

    # 4. Intake Lists
    intake_lists_df = pd.read_excel(EXCEL_FILE, sheet_name="Intake_Lists").fillna("")
    intake_lists = {}
    
    for col in intake_lists_df.columns:
        list_ref = clean_str(col)
        if not list_ref:
            continue
        values = [clean_str(v) for v in intake_lists_df[col].tolist() if clean_str(v)]
        if values:
            intake_lists[list_ref] = values
            
    print(f"Processed {len(intake_lists)} intake lists.")

    output_data = {
        "questions": questions,
        "answers": answers,
        "intake_questions": intake_questions,
        "intake_lists": intake_lists,
        "metadata": {
            "source_file": EXCEL_FILE,
            "generated_at": str(pd.Timestamp.now())
        }
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"✅ Successfully wrote to {OUTPUT_FILE}")

if __name__ == "__main__":
    migrate()
