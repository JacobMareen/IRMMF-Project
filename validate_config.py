
import json
import yaml
from pathlib import Path

def validate_json():
    try:
        with open("app/core/irmmf_bank.json", "r") as f:
            data = json.load(f)
        print(f"✅ JSON Valid. Encoded {len(data.get('questions', []))} questions.")
        print(f"   ℹ️ Root Keys: {list(data.keys())}")
        if data.get('questions'):
            print(f"   ℹ️ Last Question ID: {data['questions'][-1].get('q_id')}")

        # Check for new questions
        new_ids = ["CORR-DEF-01", "CORR-PROC-01", "CORR-SUB-01"]
        
        # Debug: Print all CORR- IDs found
        corr_found = [q.get('q_id') for q in data['questions'] if str(q.get('q_id')).startswith("CORR")]
        print(f"   ℹ️ Found CORR IDs in DB: {corr_found}")

        for qid in new_ids:
            found = any(q.get('q_id') == qid for q in data['questions'])
            if found:
                print(f"   - Found {qid}")
            else:
                print(f"   ❌ Missing {qid}")

    except Exception as e:
        print(f"❌ JSON Error: {e}")

def validate_yaml():
    try:
        with open("config/risk_scenarios_simple.yaml", "r") as f:
            data = yaml.safe_load(f)
        
        scenarios = data.get("risks", [])
        print(f"✅ YAML Valid. Loaded {len(scenarios)} scenarios.")
        
        # Check for Foreign Influence
        fi = next((s for s in scenarios if s['id'] == 'Foreign_Influence'), None)
        if fi:
            print("   - Found 'Foreign_Influence' scenario")
            defense_rule = next((r for r in fi['impact_rules'] if "Defense" in r['condition']), None)
            if defense_rule:
                print(f"   - Found Defense Impact Rule: {defense_rule}")
            else:
                print("   ❌ Missing Defense Impact Rule")
        else:
            print("   ❌ Missing 'Foreign_Influence' scenario")

    except Exception as e:
        print(f"❌ YAML Error: {e}")

if __name__ == "__main__":
    validate_json()
    validate_yaml()
