
import json

def analyze_transitions():
    with open("app/core/irmmf_bank.json", "r") as f:
        data = json.load(f)

    questions = data.get("questions", [])
    q_map = {q["q_id"]: q for q in questions}
    
    domains = [
        "3. Governance & Policy",
        "4. Legal, Privacy & Ethics",
        "5. Human-Centric Culture"
    ]

    for domain in domains:
        print(f"\n--- Domain: {domain} ---")
        t2_qs = [q for q in questions if q.get("domain") == domain and q.get("tier") == "T2"]
        
        for q in t2_qs:
            next_ids = []
            if q.get("next_default"): next_ids.append(q.get("next_default"))
            if q.get("next_if_low"): next_ids.append(q.get("next_if_low"))
            if q.get("next_if_high"): next_ids.append(q.get("next_if_high"))
            
            for nid in next_ids:
                target = q_map.get(nid)
                if not target:
                    print(f"[{q['q_id']}] -> {nid} (MISSING)")
                    continue
                
                # Check for transition out of T2 or out of Domain
                if target.get("tier") != "T2" or target.get("domain") != domain:
                    print(f"TRANSITION: [{q['q_id']}] -> [{nid}] ({target.get('tier')}, {target.get('domain')})")

if __name__ == "__main__":
    analyze_transitions()
