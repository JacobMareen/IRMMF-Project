"""Core branching + scoring engines for IRMMF assessments."""
from typing import Dict, List, Tuple, Any, Optional, Set
from app import models
from app.core.risk_engine import compute_risks
import math

class V6_1BranchingEngine:
    """
    Graph-Based Neuro-Adaptive Engine.
    - Determines flow by parsing NextIfLow/High/Default connections.
    - Lookahead: Reveals entire unlocked branches up to the next Gatekeeper.
    """

    def determine_next_step(self, current_q: models.Question, score: float) -> Tuple[Optional[str], str]:
        # 1. Gatekeeper Logic
        if current_q.branch_type == 'Gatekeeper':
            threshold = current_q.gate_threshold or 0.0
            if score >= threshold:
                return current_q.next_if_high, f"Score {score} ≥ {threshold}. High path unlocked."
            else:
                return current_q.next_if_low, f"Score {score} < {threshold}. Low path followed."
        
        # 2. End Flag (Explicit Stop)
        if hasattr(current_q, 'end_flag') and current_q.end_flag == 'Y':
             return None, "Path Complete."

        # 3. Linear Logic
        if current_q.next_default:
            return current_q.next_default, ""
            
        return None, "End of Branch"

    def calculate_reachable_path(self, all_questions: List[models.Question], user_responses: Dict[str, float]) -> List[str]:
        q_map = {q.q_id: q for q in all_questions}
        
        # --- STEP 1: TOPOLOGY (Find Roots) ---
        referenced_ids = set()
        for q in all_questions:
            if q.next_if_low: referenced_ids.add(q.next_if_low)
            if q.next_if_high: referenced_ids.add(q.next_if_high)
            if q.next_default: referenced_ids.add(q.next_default)
        
        # Domain-ordered traversal keeps the UI sidebar predictable.
        domains = sorted(list(set(q.domain for q in all_questions if q.domain)))
        ordered_path = []

        for domain in domains:
            domain_qs = [q for q in all_questions if q.domain == domain]
            # Roots = Questions in this domain that no other question points to
            roots = [q.q_id for q in domain_qs if q.q_id not in referenced_ids]
            
            if not roots and domain_qs:
                domain_qs.sort(key=lambda x: x.q_id)
                roots = [domain_qs[0].q_id]
            
            roots.sort()
            
            # --- STEP 2: TRAVERSAL WITH LOOKAHEAD ---
            queue = list(roots)
            visited_in_domain = set()
            
            while queue:
                curr_id = queue.pop(0)
                if curr_id in visited_in_domain or curr_id not in q_map:
                    continue
                if q_map[curr_id].domain != domain: 
                    continue

                visited_in_domain.add(curr_id)
                ordered_path.append(curr_id)
                
                q = q_map[curr_id]
                
                # If answered, follow the strict logic branch
                if curr_id in user_responses:
                    score = user_responses[curr_id]
                    next_id, _ = self.determine_next_step(q, score)
                    if next_id and next_id in q_map:
                        queue.append(next_id)
                
                # If NOT answered (LOOKAHEAD): 
                # Only reveal the next step if it's a linear connection.
                # Stop if we hit a Gatekeeper (we can't predict the path).
                else:
                    if q.branch_type == 'Gatekeeper':
                        continue 
                    if q.next_default and q.next_default in q_map:
                        queue.append(q.next_default)
        
        return ordered_path


class V6_1ScoringEngine:
    """
    Advanced IRMMF v6.1 Scoring.
    - Uses Harmonic Mean to penalize "Paper Dragons" (uneven maturity).
    - Incorporates Confidence Scores from Evidence Challenges.
    """

    def _infer_layer(self, tier: Optional[str]) -> str:
        if not tier:
            return "declared"
        norm = str(tier).strip().upper()
        if norm in {"T3", "T4"}:
            return "verified"
        if "VERIF" in norm or norm.startswith("V"):
            return "verified"
        if "DECLAR" in norm or norm.startswith("D"):
            return "declared"
        return "declared"

    def _apply_alpha_penalty(self, score: float, cw: Optional[float], th: Optional[float]) -> Tuple[float, bool]:
        weight = 0.3
        cw_val = cw if cw is not None else 1.0
        th_val = th if th is not None else 0.0
        if cw_val > 1.2 and score < th_val:
            return score * weight, True
        return score, False

    def calculate_harmonic_mean(self, scores: List[float]) -> float:
        """
        Harmonic Mean = n / (sum(1/x)). 
        Punishes low outliers (the 'weakest link' principle).
        """
        if not scores:
            return 0.0

        if any(s <= 0 for s in scores):
            return 0.0

        reciprocal_sum = sum(1.0 / s for s in scores)
        return len(scores) / reciprocal_sum

    def _weighted_harmonic_mean(self, values: List[float], weights: List[float]) -> float:
        if not values or not weights or len(values) != len(weights):
            return 0.0
        if any(v <= 0 for v, w in zip(values, weights) if w > 0):
            return 0.0
        weight_sum = sum(weights)
        if weight_sum <= 0:
            return 0.0
        denom = sum((w / v) for v, w in zip(values, weights) if w > 0)
        if denom <= 0:
            return 0.0
        return weight_sum / denom

    def _build_axis_scores(self, axis_scores: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        final_axes = []
        for axis, data in axis_scores.items():
            if data.get("use_hmean"):
                values = data.get("values", [])
                weights = data.get("weights", [])
                hmean = self._weighted_harmonic_mean(values, weights)
                pct = (hmean / 5.0) * 100 if hmean > 0 else 0.0
            else:
                total = data.get("sum", 0.0)
                maximum = data.get("max", 0.0)
                pct = (total / maximum) * 100 if maximum > 0 else 0.0
            final_axes.append({
                "axis": axis,
                "score": round(pct, 1),
                "code": axis[0].upper() if axis else "X"
            })
        return final_axes

    def _apply_caps(self, axes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        caps = []
        by_code = {a.get("code"): a for a in axes}

        fatigue_threshold = 50.0
        fatigue_cap = 70.0
        if by_code.get("H", {}).get("score", 0.0) < fatigue_threshold and "R" in by_code:
            original = by_code["R"]["score"]
            if original > fatigue_cap:
                by_code["R"]["score"] = round(fatigue_cap, 1)
                caps.append({
                    "type": "fatigue_cap",
                    "axis": "R",
                    "cap_to": fatigue_cap,
                    "reason": f"H below {fatigue_threshold}%"
                })

        shadow_threshold = 50.0
        shadow_cap = 70.0
        if by_code.get("V", {}).get("score", 0.0) < shadow_threshold and "G" in by_code:
            original = by_code["G"]["score"]
            if original > shadow_cap:
                by_code["G"]["score"] = round(shadow_cap, 1)
                caps.append({
                    "type": "shadow_cap",
                    "axis": "G",
                    "cap_to": shadow_cap,
                    "reason": f"V below {shadow_threshold}%"
                })

        return list(by_code.values()), caps


    def compute_analysis(
        self,
        questions: List[models.Question],
        responses: List[models.Response],
        evidence_list: List[models.EvidenceResponse] = None,
        intake_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        
        q_lookup = {q.q_id: q for q in questions}
        
        # Build Evidence/Confidence Map (Q_ID -> Confidence Score 0.0 to 1.0)
        # Defaults to 1.0 for questions that didn't trigger a challenge.
        conf_map = {}
        if evidence_list:
            for ev in evidence_list:
                conf_map[ev.q_id] = ev.confidence_score

        if not responses:
            return {
                "archetype": "Insufficient Data",
                "summary": {"trust_index": 0, "friction_score": 0, "evidence_confidence_avg": 0.0},
                "axes": [],
                "declared_vector": [],
                "verified_vector": [],
                "gap_vector": [],
                "caps_applied": [],
                "risk_heatmap": [],
                "top_risks": []
            }

        axis_scores = {}
        layer_scores = {"declared": {}, "verified": {}}
        alpha_penalty_count = 0
        confidence_values = []

        axis_labels = {
            "G": "Governance",
            "E": "Execution",
            "T": "Technical Orchestration",
            "L": "Legal & Privacy",
            "H": "Human Sentiment",
            "V": "Visibility",
            "R": "Resilience",
            "F": "Friction Management",
            "W": "Control Lag Management"
        }

        axis_keys = list(axis_labels.keys())
        for key in axis_keys:
            axis_scores[key] = {"use_hmean": True, "values": [], "weights": []}
            layer_scores["declared"][key] = {"use_hmean": True, "values": [], "weights": []}
            layer_scores["verified"][key] = {"use_hmean": True, "values": [], "weights": []}

        for r in responses:
            if r.q_id in q_lookup:
                question = q_lookup[r.q_id]

                # Apply Confidence Adjustment: Adjusted Score = Raw Score * Confidence
                if hasattr(r, "evidence_confidence") and r.evidence_confidence is not None:
                    confidence = r.evidence_confidence
                else:
                    confidence = conf_map.get(r.q_id, 1.0)
                confidence_values.append(confidence)
                penalized_score, alpha_applied = self._apply_alpha_penalty(
                    r.score_achieved,
                    question.cw,
                    question.th
                )
                if alpha_applied:
                    alpha_penalty_count += 1
                adjusted_score = penalized_score * confidence
                weight = question.cw if question.cw is not None else 1.0

                pts_map = {
                    "G": question.pts_g or 0.0,
                    "E": question.pts_e or 0.0,
                    "T": question.pts_t or 0.0,
                    "L": question.pts_l or 0.0,
                    "H": question.pts_h or 0.0,
                    "V": question.pts_v or 0.0,
                    "R": question.pts_r or 0.0,
                    "F": question.pts_f or 0.0,
                    "W": question.pts_w or 0.0
                }
                layer = self._infer_layer(question.tier)
                for axis, pts in pts_map.items():
                    if pts <= 0:
                        continue
                    w = weight * pts
                    axis_scores[axis]["values"].append(adjusted_score)
                    axis_scores[axis]["weights"].append(w)
                    layer_scores[layer][axis]["values"].append(adjusted_score)
                    layer_scores[layer][axis]["weights"].append(w)

        final_axes = self._build_axis_scores(axis_scores)
        final_axes, caps_applied = self._apply_caps(final_axes)
        declared_axes = self._build_axis_scores(layer_scores["declared"])
        declared_axes, declared_caps = self._apply_caps(declared_axes)
        verified_axes = self._build_axis_scores(layer_scores["verified"])
        verified_axes, verified_caps = self._apply_caps(verified_axes)
        caps_applied.extend(declared_caps)
        caps_applied.extend(verified_caps)

        # Risk engine expects axis scores normalized to 0-6.
        axis_score_map = {
            a.get("code"): max(0.0, min(6.0, (a.get("score", 0.0) / 100.0) * 6.0))
            for a in final_axes
            if a.get("code")
        }
            
        # Overall Trust Index (Simple average of domain percentages)
        trust_index = 0.0
        if final_axes:
            trust_index = sum([x['score'] for x in final_axes]) / len(final_axes)
        
        friction_score = 100.0 - trust_index
        evidence_confidence_avg = round(
            sum(confidence_values) / len(confidence_values), 2
        ) if confidence_values else 0.0

        # Safe Fallback for UI
        if not final_axes:
            return {
                "archetype": "Insufficient Data",
                "summary": {"trust_index": 0, "friction_score": 0, "evidence_confidence_avg": 0.0},
                "axes": [],
                "declared_vector": [],
                "verified_vector": [],
                "gap_vector": [],
                "caps_applied": [],
                "risk_heatmap": [],
                "top_risks": []
            }

        # Archetype Logic based on Friction vs. Trust
        archetype = "Resilient Optimiser"
        if friction_score > trust_index:
            archetype = "Paper Dragon"
        elif trust_index > 80:
            archetype = "Cyber Sovereign"

        # Replace axis labels for UI
        def _label_axes(axes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            out = []
            for a in axes:
                code = a.get("code") or a.get("axis")
                out.append({
                    "axis": axis_labels.get(code, a.get("axis")),
                    "code": code,
                    "score": a.get("score", 0.0)
                })
            return out

        final_axes = _label_axes(final_axes)
        declared_axes = _label_axes(declared_axes)
        verified_axes = _label_axes(verified_axes)

        declared_by_axis = {a["code"]: a for a in declared_axes}
        verified_by_axis = {a["code"]: a for a in verified_axes}
        gap_vector = []
        for axis in axis_keys:
            declared_score = declared_by_axis.get(axis, {}).get("score", 0.0)
            verified_score = verified_by_axis.get(axis, {}).get("score", 0.0)
            gap = round(declared_score - verified_score, 1)
            gap_vector.append({
                "axis": axis_labels.get(axis, axis),
                "score": gap,
                "code": axis
            })

        # Scenario-driven risk scoring uses intake tags for impact adjustments.
        risk_heatmap, top_risks = compute_risks(axis_score_map, intake_tags or [])

        ranked_axes = sorted(final_axes, key=lambda a: a.get("score", 0.0))
        weakest = [a["axis"] for a in ranked_axes[:2]]
        strongest = [a["axis"] for a in ranked_axes[-2:]]
        archetype_details = {
            "primary": archetype,
            "rationale": [
                f"Strongest axes: {', '.join(strongest)}" if strongest else "Strongest axes: n/a",
                f"Weakest axes: {', '.join(weakest)}" if weakest else "Weakest axes: n/a",
                f"Trust index {round(trust_index, 1)} vs friction {round(friction_score, 1)}",
            ],
            "runner_up": None,
            "confidence": 0.5,
        }

        return {
            "archetype": archetype,
            "archetype_details": archetype_details,
            "summary": {
                "trust_index": round(trust_index, 1),
                "friction_score": round(friction_score, 1),
                "alpha_penalty_count": alpha_penalty_count,
                "evidence_confidence_avg": evidence_confidence_avg
            },
            "axes": final_axes,
            "declared_vector": declared_axes,
            "verified_vector": verified_axes,
            "gap_vector": gap_vector,
            "caps_applied": caps_applied,
            "risk_heatmap": risk_heatmap,
            "top_risks": top_risks
        }

    def compute_kickstart_diagnostic(
        self,
        questions: List[models.Question],
        responses: List[models.Response],
        evidence_list: List[models.EvidenceResponse] = None
    ) -> Dict[str, Any]:
        q_lookup = {q.q_id: q for q in questions}
        conf_map = {}
        if evidence_list:
            for ev in evidence_list:
                conf_map[ev.q_id] = ev.confidence_score

        axis_labels = {
            "G": "Governance",
            "E": "Execution",
            "T": "Technical Orchestration",
            "L": "Legal & Privacy",
            "H": "Human Sentiment",
            "V": "Visibility",
            "R": "Resilience",
            "F": "Friction Management",
            "W": "Control Lag Management"
        }
        axis_keys = list(axis_labels.keys())
        accum = {k: {"sum": 0.0, "max": 0.0} for k in axis_keys}

        for r in responses:
            q = q_lookup.get(r.q_id)
            if not q:
                continue
            if (q.tier or "").upper() != "T1" or (q.branch_type or "") != "Gatekeeper":
                continue
            if getattr(r, "is_deferred", False):
                continue
            if hasattr(r, "evidence_confidence") and r.evidence_confidence is not None:
                confidence = r.evidence_confidence
            else:
                confidence = conf_map.get(r.q_id, 1.0)
            penalized_score, _ = self._apply_alpha_penalty(
                r.score_achieved,
                q.cw,
                q.th
            )
            adjusted_score = penalized_score * confidence
            weight = q.cw if q.cw is not None else 1.0
            pts_map = {
                "G": q.pts_g or 0.0,
                "E": q.pts_e or 0.0,
                "T": q.pts_t or 0.0,
                "L": q.pts_l or 0.0,
                "H": q.pts_h or 0.0,
                "V": q.pts_v or 0.0,
                "R": q.pts_r or 0.0,
                "F": q.pts_f or 0.0,
                "W": q.pts_w or 0.0
            }
            for axis, pts in pts_map.items():
                if pts <= 0:
                    continue
                accum[axis]["sum"] += adjusted_score * weight * pts
                accum[axis]["max"] += 5.0 * weight * pts

        axes_out = []
        scores = []
        for axis in axis_keys:
            total = accum[axis]["sum"]
            maximum = accum[axis]["max"]
            pct = (total / maximum) * 100 if maximum > 0 else 0.0
            scores.append(pct)
            axes_out.append({
                "axis": axis_labels[axis],
                "code": axis,
                "score": round(pct, 1)
            })
        readiness = round(sum(scores) / len(scores), 1) if scores else 0.0
        return {"readiness": readiness, "axes": axes_out}

    def compute_soft_vector(
        self,
        questions: List[models.Question],
        responses: List[models.Response],
        evidence_list: List[models.EvidenceResponse] = None
    ) -> Dict[str, Any]:
        q_lookup = {q.q_id: q for q in questions}
        conf_map = {}
        if evidence_list:
            for ev in evidence_list:
                conf_map[ev.q_id] = ev.confidence_score

        axis_labels = {
            "G": "Governance",
            "E": "Execution",
            "T": "Technical Orchestration",
            "L": "Legal & Privacy",
            "H": "Human Sentiment",
            "V": "Visibility",
            "R": "Resilience",
            "F": "Friction Management",
            "W": "Control Lag Management"
        }
        axis_keys = list(axis_labels.keys())
        accum = {k: {"sum": 0.0, "max": 0.0} for k in axis_keys}

        for r in responses:
            q = q_lookup.get(r.q_id)
            if not q:
                continue
            if getattr(r, "is_deferred", False):
                continue
            if hasattr(r, "evidence_confidence") and r.evidence_confidence is not None:
                confidence = r.evidence_confidence
            else:
                confidence = conf_map.get(r.q_id, 1.0)
            penalized_score, _ = self._apply_alpha_penalty(
                r.score_achieved,
                q.cw,
                q.th
            )
            adjusted_score = penalized_score * confidence
            weight = q.cw if q.cw is not None else 1.0
            pts_map = {
                "G": q.pts_g or 0.0,
                "E": q.pts_e or 0.0,
                "T": q.pts_t or 0.0,
                "L": q.pts_l or 0.0,
                "H": q.pts_h or 0.0,
                "V": q.pts_v or 0.0,
                "R": q.pts_r or 0.0,
                "F": q.pts_f or 0.0,
                "W": q.pts_w or 0.0
            }
            for axis, pts in pts_map.items():
                if pts <= 0:
                    continue
                accum[axis]["sum"] += adjusted_score * weight * pts
                accum[axis]["max"] += 5.0 * weight * pts

        axes_out = []
        scores = []
        for axis in axis_keys:
            total = accum[axis]["sum"]
            maximum = accum[axis]["max"]
            pct = (total / maximum) * 100 if maximum > 0 else 0.0
            scores.append(pct)
            axes_out.append({
                "axis": axis_labels[axis],
                "code": axis,
                "score": round(pct, 1)
            })
        overall = round(sum(scores) / len(scores), 1) if scores else 0.0
        return {"overall": overall, "axes": axes_out}
