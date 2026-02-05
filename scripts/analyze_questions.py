import pandas as pd
import os

FILE = "IRMMF_QuestionBank_v10_StreamlinedIntake_20260117.xlsx"

if not os.path.exists(FILE):
    print(f"File not found: {FILE}")
    exit(1)

print(f"Anayzing {FILE}...")

try:
    # Load Questions
    df_q = pd.read_excel(FILE, sheet_name="Questions").fillna("")
    df_intake = pd.read_excel(FILE, sheet_name="Intake_Questions").fillna("")
    
    # 1. Counts
    total_q = len(df_q)
    total_intake = len(df_intake)
    
    # 2. Gates
    # Check if GateThreshold column exists and has values
    gates = 0
    if "GateThreshold" in df_q.columns:
        # Count non-empty, non-zero thresholds
        gates = len(df_q[df_q["GateThreshold"].astype(str).str.strip() != ""])
        
    # 3. Domains
    domains = df_q["IRMMF Domain"].value_counts()
    
    print("-" * 30)
    print("FATIGUE ANALYSIS REPORT")
    print("-" * 30)
    print(f"Total Full Questions:   {total_q}")
    print(f"Intake / Triage Questions: {total_intake}")
    print(f"Gated Questions (Skips): {gates} ({(gates/total_q)*100:.1f}%)")
    print("-" * 30)
    print("Breakdown by Domain:")
    for domain, count in domains.items():
        print(f"  - {domain}: {count}")
    print("-" * 30)

    # 4. Triage Assessment - Is it separate?
    # If Intake exists, justify the "Lite" mode recommendations
    if total_intake > 0:
        print("\nObservation: An Intake/Triage module ALREADY exists.")
        print(f"It contains {total_intake} questions. Is the frontend using it?")
    else:
        print("\nObservation: NO Intake/Triage module found.")

except Exception as e:
    print(f"Error reading excel: {e}")
