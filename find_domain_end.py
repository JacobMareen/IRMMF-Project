
import json

def find_domain_ends():
    with open("app/core/irmmf_bank.json", "r") as f:
        data = json.load(f)

    questions = data.get("questions", [])
    q_map = {q["q_id"]: q for q in questions}
    
    domains = [
        "3. Governance & Policy",
        "5. Human-Centric Culture"
    ]

    for domain in domains:
        print(f"\n--- Domain: {domain} ---")
        # Get all T2 questions in this domain
        t2_qs = [q for q in questions if q.get("domain") == domain and q.get("tier") == "T2"]
        
        for q in t2_qs:
            # Check next_default
            next_id = q.get("next_default")
            if next_id:
                next_q = q_map.get(next_id)
                if next_q and next_q.get("domain") != domain:
                    print(f"EXIT NODE: [{q['q_id']}] -> [{next_id}] starts {next_q.get('domain')}")
            
            # Check branches (less common for domain exits but possible)
            if q.get("next_if_high"):
                nid = q.get("next_if_high")
                nq = q_map.get(nid)
                if nq and nq.get("domain") != domain:
                     print(f"EXIT NODE (High): [{q['q_id']}] -> [{nid}] starts {nq.get('domain')}")

if __name__ == "__main__":
    find_domain_ends()
