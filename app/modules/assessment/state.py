"""Assessment workflow state changes and exports."""
from typing import Any, Dict, List
import secrets
from sqlalchemy.dialects.postgresql import insert

from app import schemas
from app.modules.assessment import models


class AssessmentStateService:
    def create_new_assessment(
        self,
        tenant_key: str = "default",
        user_id: str | None = None,
    ) -> str:
        """Generate a secure assessment key server-side."""
        secure_key = f"IRMMF-{secrets.token_urlsafe(24)}"
        new_assessment = models.Assessment(
            assessment_id=secure_key,
            tenant_key=tenant_key,
            is_active=True,
            user_id=user_id,
        )
        self.db.add(new_assessment)
        self.db.commit()
        return secure_key

    def submit_answer(self, payload: schemas.ResponseCreate) -> Dict[str, Any]:
        """Save response and return full state including logic reasons."""
        current_q = self.q_repo.get_by_id(payload.q_id)
        if not current_q:
            raise ValueError(f"Question {payload.q_id} not found.")
        assessment = (
            self.db.query(models.Assessment)
            .filter_by(assessment_id=payload.assessment_id)
            .first()
        )
        # Evidence confidence influences scoring and is stored for auditability.
        evidence_confidence = None
        if payload.evidence:
            evidence_confidence = self._compute_evidence_confidence(current_q, payload.evidence)
        elif payload.confidence is not None:
            evidence_confidence = payload.confidence

        # Deferred answers still need a stable A_ID for integrity and resuming.
        safe_a_id = payload.a_id
        if payload.is_deferred:
            if not safe_a_id or safe_a_id == "DEFERRED":
                existing = (
                    self.db.query(models.Response)
                    .filter_by(assessment_id=payload.assessment_id, q_id=payload.q_id)
                    .first()
                )
                if existing and existing.a_id:
                    safe_a_id = existing.a_id
                elif current_q and current_q.options:
                    safe_a_id = current_q.options[0].a_id

        # Origin tags are used to exclude override answers from baseline metrics.
        origin = payload.origin or ("override" if assessment and assessment.override_depth else "adaptive")
        update_fields = {
            "a_id": safe_a_id,
            "score_achieved": payload.score,
            "is_deferred": payload.is_deferred,
            "is_flagged": payload.is_flagged,
            "origin": origin,
        }
        if payload.is_deferred:
            update_fields.update({
                "evidence": None,
                "evidence_confidence": None,
                "evidence_policy_id": None,
            })
        elif payload.evidence is not None:
            update_fields.update({
                "evidence": payload.evidence,
                "evidence_confidence": evidence_confidence,
                "evidence_policy_id": current_q.evidence_policy_id,
            })
        elif payload.confidence is not None:
            update_fields.update({
                "evidence_confidence": evidence_confidence,
                "evidence_policy_id": current_q.evidence_policy_id,
            })

        # Upsert keeps one canonical response per assessment/question.
        stmt = insert(models.Response).values(
            assessment_id=payload.assessment_id,
            q_id=payload.q_id,
            a_id=safe_a_id,
            score_achieved=payload.score,
            pack_id=payload.pack_id,
            is_deferred=payload.is_deferred,
            is_flagged=payload.is_flagged,
            origin=origin,
            evidence=payload.evidence if not payload.is_deferred else None,
            evidence_confidence=evidence_confidence if not payload.is_deferred else None,
            evidence_policy_id=current_q.evidence_policy_id if not payload.is_deferred else None,
        ).on_conflict_do_update(
            index_elements=["assessment_id", "q_id"],
            set_=update_fields,
        )
        self.db.execute(stmt)

        if not payload.is_deferred and evidence_confidence is not None:
            ev_stmt = insert(models.EvidenceResponse).values(
                assessment_id=payload.assessment_id,
                q_id=payload.q_id,
                confidence_score=evidence_confidence if evidence_confidence is not None else 1.0,
            ).on_conflict_do_update(
                index_elements=["assessment_id", "q_id"],
                set_={"confidence_score": evidence_confidence if evidence_confidence is not None else 1.0},
            )
            self.db.execute(ev_stmt)

        self.db.commit()

        # Logic reason for the adaptive toast in the UI.
        _, logic_reason = self.branch_engine.determine_next_step(current_q, payload.score)

        state = self.get_resumption_state(payload.assessment_id)
        state["logic_reason"] = logic_reason
        return state

    def _compute_evidence_confidence(self, question: models.Question, evidence: Dict[str, Any]) -> float:
        has_evidence = bool(evidence.get("has_evidence"))
        checks = evidence.get("checks") or {}
        if not isinstance(checks, dict):
            checks = {}

        policy_id = (question.evidence_policy_id or "").strip().upper()
        policy_rules = {
            "GOV_STD": {"base_no_evidence": 0.5, "required": ["freshness", "scope"], "min_ratio": 0.6},
            "RISK_STD": {"base_no_evidence": 0.5, "required": ["scope"], "min_ratio": 0.6},
            "OPS_STD": {"base_no_evidence": 0.45, "required": ["ops_usage"], "min_ratio": 0.6},
            "CULT_SOFT": {"base_no_evidence": 0.6, "required": [], "min_ratio": 0.5},
            "LEG_STRICT": {"base_no_evidence": 0.3, "required": ["freshness", "traceability"], "min_ratio": 0.7},
            "HUMAN_BIO": {"base_no_evidence": 0.35, "required": ["scope", "sampling"], "min_ratio": 0.7},
            "FRICTION_AI": {"base_no_evidence": 0.35, "required": ["sampling", "traceability"], "min_ratio": 0.7},
            "TECH_STRICT": {"base_no_evidence": 0.35, "required": ["sampling", "traceability"], "min_ratio": 0.7},
        }
        rule = policy_rules.get(policy_id, {"base_no_evidence": 0.4, "required": [], "min_ratio": 0.5})

        total = len(checks)
        passed = sum(1 for v in checks.values() if bool(v))
        ratio = (passed / total) if total > 0 else 1.0
        base = 1.0 if has_evidence else rule["base_no_evidence"]
        confidence = base * ratio

        if has_evidence and rule["required"]:
            required_passed = sum(1 for key in rule["required"] if checks.get(key))
            if required_passed < len(rule["required"]):
                confidence *= 0.6
        if has_evidence and ratio < rule["min_ratio"]:
            confidence *= 0.7

        return max(0.1, min(1.0, round(confidence, 2)))

    def _normalize_depth(self, depth: str | None) -> str:
        if not depth:
            return "Lightweight"
        norm = depth.strip().lower()
        if norm in {"core", "light", "lightweight"}:
            return "Lightweight"
        if norm in {"standard"}:
            return "Standard"
        if norm in {"deep"}:
            return "Deep"
        return "Standard"

    def _allowed_tiers_by_maturity(self, readiness: float | None, override_depth: bool) -> set[str]:
        if override_depth:
            return {"T1", "T2", "T3", "T4"}
        readiness = readiness if readiness is not None else 0.0
        if readiness < 40.0:
            return {"T1"}
        if readiness < 70.0:
            return {"T1", "T2", "T3"}
        return {"T1", "T2", "T3", "T4"}

    def _filter_questions_for_maturity(
        self,
        questions: List[models.Question],
        readiness: float | None,
        override_depth: bool,
    ) -> List[models.Question]:
        allowed = self._allowed_tiers_by_maturity(readiness, override_depth)
        filtered = []
        for q in questions:
            tier = (q.tier or "").strip().upper()
            if not tier or tier in allowed:
                filtered.append(q)
        return filtered

    def get_resumption_state(self, assessment_id: str) -> Dict[str, Any]:
        """Security + Next Best + Sidebar Builder."""
        record = self.db.query(models.Assessment).filter_by(assessment_id=assessment_id).first()
        if not record:
            raise ValueError(f"Assessment {assessment_id} not found.")
        if not record.is_active:
            raise ValueError("This assessment key has been revoked.")

        all_qs = self.q_repo.get_all()
        all_qs_map = {q.q_id: q for q in all_qs}

        responses = self.r_repo.get_by_assessment(assessment_id)
        evidence = self.db.query(models.EvidenceResponse).filter_by(assessment_id=assessment_id).all()
        valid_map = {r.q_id: r.score_achieved for r in responses if not r.is_deferred}

        kickstart = self.scoring_engine.compute_kickstart_diagnostic(all_qs, responses, evidence)
        eligible_qs = self._filter_questions_for_maturity(
            all_qs,
            kickstart.get("readiness"),
            record.override_depth,
        )
        eligible_qs_map = {q.q_id: q for q in eligible_qs}

        reachable = self.branch_engine.calculate_reachable_path(eligible_qs, valid_map)
        reachable_set = set(reachable)

        sidebar_context = []
        active_domains = {eligible_qs_map[qid].domain for qid in reachable if qid in eligible_qs_map}

        for q in eligible_qs:
            status = "hidden"
            reason = None

            if q.q_id in reachable_set:
                status = "active"
            elif q.domain in active_domains:
                status = "locked"
                reason = "Requires higher maturity score in foundational gates to unlock."

            sidebar_context.append({
                "q_id": q.q_id,
                "domain": q.domain,
                "title": q.question_title or q.q_id,
                "status": status,
                "reason": reason,
            })

        flagged_ids = {r.q_id for r in responses if r.is_flagged}
        deferred_ids = {r.q_id for r in responses if r.is_deferred}
        answered_ids = set(valid_map.keys())

        next_id = None
        next_reason = "Start here"

        for qid in reachable:
            if qid in flagged_ids:
                next_id = qid
                next_reason = "Marked for Review"
                break

        if not next_id:
            for qid in reachable:
                if qid in deferred_ids:
                    next_id = qid
                    next_reason = "Previously Deferred"
                    break

        if not next_id:
            for qid in reachable:
                if qid not in answered_ids and qid not in deferred_ids:
                    next_id = qid
                    next_reason = "Next Step"
                    break

        total_potential = len(reachable)
        progress = int((len(answered_ids) / total_potential * 100)) if total_potential > 0 else 0
        dashboard_soft = self.scoring_engine.compute_soft_vector(eligible_qs, responses, evidence)

        # Convert multi-select responses (comma-separated a_ids) back to arrays
        responses_dict = {}
        for r in responses:
            # Check if this is a multi-select question by looking at answer options
            q = all_qs_map.get(r.q_id)
            is_multiselect = False
            if q and q.options:
                is_multiselect = any(opt.tags == 'multiselect' for opt in q.options)

            if is_multiselect and ',' in r.a_id:
                # Split comma-separated IDs into array
                responses_dict[r.q_id] = r.a_id.split(',')
            else:
                responses_dict[r.q_id] = r.a_id

        return {
            "responses": responses_dict,
            "deferred_ids": list(deferred_ids),
            "flagged_ids": list(flagged_ids),
            "marked_for_review": list(flagged_ids),
            "next_best_qid": next_id,
            "next_reason": next_reason,
            "reachable_path": reachable,
            "sidebar_context": sidebar_context,
            "completion_pct": progress,
            "kickstart": kickstart,
            "dashboard_soft": dashboard_soft,
            "override_depth": bool(record.override_depth),
            "depth_suggestion": self._suggest_depth(record, kickstart),
            "depth_mode": self._normalize_depth(record.depth or self._suggest_depth(record, kickstart)),
        }

    def get_questions_for_assessment(self, assessment_id: str) -> List[models.Question]:
        record = self.db.query(models.Assessment).filter_by(assessment_id=assessment_id).first()
        if not record:
            raise ValueError(f"Assessment {assessment_id} not found.")
        all_qs = self.q_repo.get_all()
        responses = self.r_repo.get_by_assessment(assessment_id)
        evidence = self.db.query(models.EvidenceResponse).filter_by(assessment_id=assessment_id).all()
        kickstart = self.scoring_engine.compute_kickstart_diagnostic(all_qs, responses, evidence)
        return self._filter_questions_for_maturity(
            all_qs,
            kickstart.get("readiness"),
            record.override_depth,
        )

    def set_override_depth(self, assessment_id: str, override_depth: bool) -> Dict[str, Any]:
        record = self.db.query(models.Assessment).filter_by(assessment_id=assessment_id).first()
        if not record:
            raise ValueError(f"Assessment {assessment_id} not found.")
        record.override_depth = bool(override_depth)
        self.db.commit()
        return {"assessment_id": assessment_id, "override_depth": record.override_depth}

    def list_assessments_for_user(self, user_id: str, tenant_key: str | None = None) -> List[Dict[str, Any]]:
        query = self.db.query(models.Assessment).filter_by(user_id=user_id)
        if tenant_key:
            query = query.filter_by(tenant_key=tenant_key)
        rows = query.order_by(models.Assessment.updated_at.desc(), models.Assessment.created_at.desc()).all()
        return [
            {
                "assessment_id": r.assessment_id,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
                "is_active": r.is_active,
            }
            for r in rows
        ]

    def get_latest_assessment_for_user(self, user_id: str, tenant_key: str | None = None) -> Dict[str, Any] | None:
        rows = self.list_assessments_for_user(user_id, tenant_key=tenant_key)
        return rows[0] if rows else None

    def reset_assessment_data(self, assessment_id: str) -> Dict[str, Any]:
        record = self.db.query(models.Assessment).filter_by(assessment_id=assessment_id).first()
        if not record:
            raise ValueError(f"Assessment {assessment_id} not found.")

        responses_deleted = (
            self.db.query(models.Response)
            .filter_by(assessment_id=assessment_id)
            .delete(synchronize_session=False)
        )
        evidence_deleted = (
            self.db.query(models.EvidenceResponse)
            .filter_by(assessment_id=assessment_id)
            .delete(synchronize_session=False)
        )
        intake_deleted = (
            self.db.query(models.IntakeResponse)
            .filter_by(assessment_id=assessment_id)
            .delete(synchronize_session=False)
        )
        audits_deleted = (
            self.db.query(models.ResponseAudit)
            .filter_by(assessment_id=assessment_id)
            .delete(synchronize_session=False)
        )
        snapshots_deleted = (
            self.db.query(models.ReportSnapshot)
            .filter_by(assessment_id=assessment_id)
            .delete(synchronize_session=False)
        )

        record.override_depth = False
        record.benchmark_tags = None
        record.is_active = True
        self.db.commit()

        return {
            "assessment_id": assessment_id,
            "responses_deleted": responses_deleted,
            "evidence_deleted": evidence_deleted,
            "intake_deleted": intake_deleted,
            "audits_deleted": audits_deleted,
            "snapshots_deleted": snapshots_deleted,
        }

    def get_context(self, assessment_id: str) -> Dict[str, Any]:
        """Compatibility wrapper for older API route."""
        return self.get_resumption_state(assessment_id)

    def get_full_export_data(self, assessment_id: str) -> Dict[str, Any]:
        responses = self.r_repo.get_by_assessment(assessment_id)
        evidence = self.db.query(models.EvidenceResponse).filter_by(assessment_id=assessment_id).all()
        return {
            "meta": {"assessment_id": assessment_id, "version": "6.1"},
            "responses": [
                {
                    "q_id": r.q_id,
                    "a_id": r.a_id,
                    "score": r.score_achieved,
                    "is_deferred": r.is_deferred,
                    "is_flagged": r.is_flagged,
                }
                for r in responses
            ],
            "evidence": [{"q_id": e.q_id, "confidence": e.confidence_score} for e in evidence],
        }

    def get_csv_export_data(self, assessment_id: str) -> List[Dict[str, Any]]:
        all_qs = {q.q_id: q for q in self.q_repo.get_all()}
        responses = self.r_repo.get_by_assessment(assessment_id)
        evidence = {
            e.q_id: e
            for e in self.db.query(models.EvidenceResponse).filter_by(assessment_id=assessment_id).all()
        }
        rows = []
        for r in responses:
            q = all_qs.get(r.q_id)
            ev = evidence.get(r.q_id)
            if not q:
                continue
            rows.append({
                "Domain": q.domain,
                "ID": q.q_id,
                "Question": q.question_text[:60],
                "Answer": r.a_id,
                "Score": r.score_achieved,
                "Status": "Deferred" if r.is_deferred else "Completed",
                "Confidence": f"{int((ev.confidence_score if ev else 1.0) * 100)}%",
            })
        return rows

    def get_review_table(self, assessment_id: str) -> List[Dict[str, Any]]:
        all_qs = self.q_repo.get_all()
        q_map = {q.q_id: q for q in all_qs}
        ans_map = {}
        for q in all_qs:
            for opt in q.options:
                ans_map[opt.a_id] = opt
        rows = []
        for r in self.r_repo.get_by_assessment(assessment_id):
            q = q_map.get(r.q_id)
            if not q:
                continue
            ans = ans_map.get(r.a_id)
            rows.append({
                "q_id": r.q_id,
                "question": q.question_text,
                "question_title": q.question_title,
                "answer": ans.answer_text if ans else r.a_id,
                "a_id": r.a_id,
                "score": r.score_achieved,
                "domain": q.domain,
                "axis1": q.axis1,
                "axis2": q.axis2,
                "tier": q.tier,
                "evidence_confidence": r.evidence_confidence,
                "is_deferred": r.is_deferred,
                "is_flagged": r.is_flagged,
                "evidence_policy_id": q.evidence_policy_id,
            })
        return rows
