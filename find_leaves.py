
import json

def find_leaves():
    with open("app/core/irmmf_bank.json", "r") as f:
        data = json.load(f)

    questions = data.get("questions", [])
    
    domains = [
        "3. Governance & Policy",
        "4. Legal, Privacy & Ethics",
        "5. Human-Centric Culture"
    ]

    print(f"Total Questions: {len(questions)}")
    
    for domain in domains:
        print(f"\n--- Domain: {domain} ---")
        param_qs = [q for q in questions if q.get("domain") == domain and q.get("tier") == "T2"]
        
        for q in param_qs:
            # Check if likely a leaf
            if not q.get("next_default") and not q.get("next_if_low") and not q.get("next_if_high"):
                print(f"LEAF: [{q.get('q_id')}] {q.get('question_title')}")

if __name__ == "__main__":
    find_leaves()
