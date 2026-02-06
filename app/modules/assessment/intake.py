"""Assessment intake flow and tags."""
from typing import Any, Dict, List, Optional
import os
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from app.modules.assessment import models


class AssessmentIntakeService:
    def submit_intake(self, assessment_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        record = (
            self.db.query(models.Assessment)
            .filter_by(assessment_id=assessment_id)
            .first()
        )
        if not record:
            raise ValueError(f"Assessment {assessment_id} not found.")
        
        benchmark_tags = self._build_benchmark_tags(answers)
        record.benchmark_tags = benchmark_tags
        
        for key, value in answers.items():
            if value is None or value == "":
                continue
            # Logic update: 'key' is the QID (e.g. INT-ORG-01). 
            # In new schema, IntakeResponse uses 'q_id' which maps to 'dim_questions.q_id'
            stmt = insert(models.IntakeResponse).values(
                assessment_id=assessment_id,
                q_id=key, 
                value=str(value),
            ).on_conflict_do_update(
                index_elements=["assessment_id", "q_id"],
                set_={"value": str(value)},
            )
            self.db.execute(stmt)
        
        self.db.commit()
        
        # Intake answers are stored before kick-start, so depth suggestion can work without responses.
        depth_suggestion = self._suggest_depth(record, None)
        if not record.depth:
            record.depth = self._normalize_depth(depth_suggestion) if hasattr(self, "_normalize_depth") else depth_suggestion
            self.db.commit()
            
        return {
            "assessment_id": assessment_id,
            "benchmark_tags": benchmark_tags,
            "depth_suggestion": depth_suggestion,
        }

    def _build_benchmark_tags(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        industry = answers.get("industry") or "Unknown"
        region = answers.get("region") or "Unknown"
        size = answers.get("size_band") or "Unknown"
        regulated = [
            k
            for k, v in answers.items()
            if k.startswith("reg_") and str(v).lower() in {"true", "yes", "1"}
        ]
        return {
            "industry": industry,
            "region": region,
            "size_band": size,
            "regulated_flags": regulated,
        }

    def _suggest_depth(self, assessment: models.Assessment, kickstart: Optional[Dict[str, Any]]) -> str:
        # Heuristic: prefer deeper paths for regulated/complex orgs or strong kick-start signal.
        tags = assessment.benchmark_tags or {}
        size = (tags.get("size_band") or "").lower()
        industry = (tags.get("industry") or "").lower()
        regulated = tags.get("regulated_flags") or []
        
        readiness = None
        if kickstart and isinstance(kickstart, dict):
            readiness = kickstart.get("readiness")
            
        if readiness is not None and readiness >= 70:
            return "Deep"
        if any(flag for flag in regulated):
            return "Deep"
        if "financial" in industry or "health" in industry:
            return "Standard"
        if "enterprise" in size:
            return "Standard"
        return "Core"

    # Helper method that might be missing in older class def but referenced globally
    def _normalize_depth(self, depth: str) -> str:
        return depth

    def _get_intake_tags(self, assessment_id: str) -> List[str]:
        # Intake tags drive risk scenario impact rules and cohort benchmarking.
        rows = self.db.query(models.IntakeResponse).filter_by(assessment_id=assessment_id).all()
        tags: List[str] = []
        seen = set()
        for row in rows:
            value = (row.value or "").strip()
            if not value:
                continue
            parts = [value]
            if "," in value:
                parts = [part.strip() for part in value.split(",")]
            for part in parts:
                if part and part not in seen:
                    seen.add(part)
                    tags.append(part)
        return tags

    def get_intake_responses(self, assessment_id: str) -> List[Dict[str, Any]]:
        rows = (
            self.db.query(models.IntakeResponse)
            .filter_by(assessment_id=assessment_id)
            .all()
        )
        return [{"intake_q_id": r.q_id, "value": r.value} for r in rows]

    def get_intake_questions(self) -> List[Dict[str, Any]]:
        # Refactor: Query dim_questions where tier='T0'
        # Also need ListOptions from dim_list_options
        
        if os.getenv("IRMMF_DEBUG_INTAKE") == "1":
            count = self.db.execute(text("SELECT COUNT(*) FROM dim_questions WHERE tier='T0'")).scalar()
            print(f"[intake] T0 Question count={count}", flush=True)

        rows = (
            self.db.query(models.Question)
            .filter(models.Question.tier == 'T0')
            .order_by(models.Question.section, models.Question.q_id)
            .all()
        )
        
        if not rows:
            # Fallback check
            q_count = self.db.execute(text("SELECT COUNT(*) FROM dim_questions WHERE tier='T0'")).scalar()
            raise ValueError(
                f"Intake questions (T0) are not present. Count={q_count}"
            )

        list_refs = {row.list_ref for row in rows if row.list_ref}
        options: Dict[str, List[Dict[str, Any]]] = {}
        if list_refs:
            opt_rows = (
                self.db.query(models.ListOption)
                .filter(models.ListOption.list_ref.in_(list_refs))
                .order_by(models.ListOption.list_ref, models.ListOption.display_order)
                .all()
            )
            for row in opt_rows:
                options.setdefault(row.list_ref, []).append({
                    "value": row.value,
                    "display_order": row.display_order,
                })
        
        payload = []
        for row in rows:
            payload.append({
                "intake_q_id": row.q_id, # Frontend expects intake_q_id
                "section": row.section,
                "question_text": row.question_text,
                "guidance": row.guidance,
                "input_type": row.input_type,
                "list_ref": row.list_ref,
                "options": options.get(row.list_ref or "", []),
            })
        return payload

    def get_intake_options(self) -> Dict[str, Any]:
        """Return intake option lists from the database instead of hardcoding."""
        rows = (
            self.db.query(models.ListOption)
            .order_by(models.ListOption.list_ref, models.ListOption.display_order)
            .all()
        )
        options_by_ref: Dict[str, List[str]] = {}
        for row in rows:
            options_by_ref.setdefault(row.list_ref, []).append(row.value)

        def _get(ref: str) -> List[str]:
            return options_by_ref.get(ref, [])

        regulated_refs = ["NIS2EntityType", "DORAScope", "CriticalInfrastructure"]
        regulated_flags: List[str] = []
        seen = set()
        for ref in regulated_refs:
            for value in options_by_ref.get(ref, []):
                if value not in seen:
                    seen.add(value)
                    regulated_flags.append(value)

        return {
            "by_list_ref": options_by_ref,
            "industry": _get("IndustryCode"),
            "region": _get("Region"),
            "size_band": _get("EmployeeBand"),
            "revenue_band": _get("RevenueBand"),
            "regulated_flags": regulated_flags,
        }
