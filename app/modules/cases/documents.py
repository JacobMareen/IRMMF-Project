from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import io
import textwrap
from typing import Optional

from app.modules.cases import models

SUPPORTED_DOCUMENT_FORMATS = {"txt", "pdf", "docx"}


@dataclass(frozen=True)
class DocumentTemplate:
    doc_type: str
    title: str
    description: str


TEMPLATES = {
    "INVESTIGATION_MANDATE": DocumentTemplate(
        doc_type="INVESTIGATION_MANDATE",
        title="Investigation Mandate",
        description="Mandate capturing legal basis and proportionality.",
    ),
    "INTERVIEW_INVITATION": DocumentTemplate(
        doc_type="INTERVIEW_INVITATION",
        title="Interview Invitation",
        description="Invitation letter for adversarial debate step.",
    ),
    "DISMISSAL_REASONS_LETTER": DocumentTemplate(
        doc_type="DISMISSAL_REASONS_LETTER",
        title="Dismissal Reasons Letter",
        description="Generated from proven facts record.",
    ),
    "INVESTIGATION_REPORT": DocumentTemplate(
        doc_type="INVESTIGATION_REPORT",
        title="Investigation Report",
        description="Executive summary and evidence-based report compiled from case data.",
    ),
    "ERASURE_CERTIFICATE": DocumentTemplate(
        doc_type="ERASURE_CERTIFICATE",
        title="Certificate of Destruction",
        description="Certificate confirming data erasure for no-sanction cases.",
    ),
    "SILENT_LEGAL_HOLD": DocumentTemplate(
        doc_type="SILENT_LEGAL_HOLD",
        title="Silent Legal Hold Instruction",
        description="Confidential preservation instruction for IT contact.",
    ),
    "US_LEGAL_HOLD": DocumentTemplate(
        doc_type="US_LEGAL_HOLD",
        title="US Legal Hold Instruction",
        description="Silent legal hold notification for US cases.",
    ),
    "WORKS_COUNCIL_REQUEST": DocumentTemplate(
        doc_type="WORKS_COUNCIL_REQUEST",
        title="Works Council Approval Request",
        description="Request for Works Council approval before monitoring.",
    ),
}


def render_document(
    doc_type: str,
    case: models.Case,
    gate_data: dict | None,
    proven_facts: Optional[models.CaseNote],
    extra_data: dict | None = None,
) -> tuple[str, dict]:
    template = TEMPLATES.get(doc_type)
    if not template:
        raise ValueError("Unsupported document type")

    header = f"{template.title}\nCase: {case.case_id} ({case.case_uuid})\nJurisdiction: {case.jurisdiction}\n"
    header += f"Generated: {datetime.utcnow().isoformat()}Z\n\n"

    if doc_type == "INVESTIGATION_MANDATE":
        gate = gate_data or {}
        body = (
            f"Legal basis: {gate.get('legal_basis', 'TBD')}\n"
            f"Trigger summary: {gate.get('trigger_summary', 'TBD')}\n"
            f"Proportionality confirmed: {gate.get('proportionality_confirmed', False)}\n"
            f"Less intrusive steps: {gate.get('less_intrusive_steps', 'TBD')}\n"
            f"Mandate owner: {gate.get('mandate_owner', 'TBD')}\n"
            f"Mandate date: {gate.get('mandate_date', 'TBD')}\n"
        )
    elif doc_type == "INTERVIEW_INVITATION":
        gate = gate_data or {}
        body = (
            "Interview invitation\n"
            f"Invitation sent: {gate.get('invitation_sent', False)}\n"
            f"Invitation date: {gate.get('invitation_date', 'TBD')}\n"
            f"Rights acknowledged: {gate.get('rights_acknowledged', False)}\n"
            f"Representative present: {gate.get('representative_present', 'TBD')}\n"
            "Please attend the interview with your representative if desired.\n"
        )
    elif doc_type == "DISMISSAL_REASONS_LETTER":
        if not proven_facts:
            raise ValueError("Proven facts note required.")
        body = (
            "Dismissal reasons based on proven facts:\n\n"
            f"{proven_facts.body}\n"
        )
    elif doc_type == "INVESTIGATION_REPORT":
        data = extra_data or {}
        impact = data.get("impact_analysis") or {}
        outcome = data.get("outcome") or {}
        triage = data.get("triage") or {}
        gates = data.get("gates") or {}
        evidence = data.get("evidence") or []
        tasks = data.get("tasks") or []
        experts = data.get("experts") or []
        timeline = data.get("timeline") or []
        lessons = data.get("lessons_learned") or ""
        def _format_lines(items, prefix="- "):
            return "\n".join(f"{prefix}{item}" for item in items) if items else "None"

        summary_lines = [
            f"Status: {case.status}",
            f"Stage: {case.stage}",
            f"Jurisdiction: {case.jurisdiction}",
            f"Outcome: {outcome.get('outcome', 'TBD')}",
            f"Decision summary: {outcome.get('summary', 'TBD')}",
        ]
        impact_lines = [
            f"Estimated loss: {impact.get('estimated_loss', 'TBD')}",
            f"Regulation breached: {impact.get('regulation_breached', 'TBD')}",
            f"Operational impact: {impact.get('operational_impact', 'TBD')}",
            f"Financial impact: {impact.get('financial_impact', 'TBD')}",
            f"Reputational impact: {impact.get('reputational_impact', 'TBD')}",
            f"People impact: {impact.get('people_impact', 'TBD')}",
        ]
        triage_labels = {
            1: "Minimal",
            2: "Low",
            3: "Moderate",
            4: "High",
            5: "Severe",
        }
        triage_outcomes = {
            "DISMISS": "No further action",
            "ROUTE_TO_HR": "HR / Employee Relations review",
            "OPEN_FULL_INVESTIGATION": "Open investigation",
        }

        def _triage_label(value):
            try:
                numeric = int(value)
            except (TypeError, ValueError):
                return value or "TBD"
            return triage_labels.get(numeric, value)

        triage_lines = [
            f"Impact level: {_triage_label(triage.get('impact'))}",
            f"Likelihood: {_triage_label(triage.get('probability'))}",
            f"Overall risk: {_triage_label(triage.get('risk_score'))}",
            f"Triage outcome: {triage_outcomes.get(str(triage.get('outcome', '')).upper(), triage.get('outcome', 'TBD'))}",
        ]
        if triage.get("trigger_source"):
            triage_lines.append(f"Trigger source: {triage.get('trigger_source')}")
        if triage.get("business_impact"):
            triage_lines.append(f"Business impact summary: {triage.get('business_impact')}")
        if triage.get("exposure_summary"):
            triage_lines.append(f"Exposure summary: {triage.get('exposure_summary')}")
        if triage.get("data_sensitivity"):
            triage_lines.append(f"Data sensitivity: {triage.get('data_sensitivity')}")
        if triage.get("stakeholders"):
            triage_lines.append(f"Stakeholders impacted: {triage.get('stakeholders')}")
        if triage.get("confidence_level"):
            triage_lines.append(f"Confidence level: {triage.get('confidence_level')}")
        if triage.get("recommended_actions"):
            triage_lines.append(f"Recommended actions: {triage.get('recommended_actions')}")
        triage_lines.append(f"Triage notes: {triage.get('notes', 'TBD')}")
        gate_lines = [
            f"Legitimacy gate: {gates.get('legitimacy', 'pending')}",
            f"Credentialing gate: {gates.get('credentialing', 'pending')}",
            f"Adversarial gate: {gates.get('adversarial', 'pending')}",
            f"Legal approval: {gates.get('legal', 'pending')}",
        ]
        evidence_lines = [f"{item.get('label')} ({item.get('source')})" for item in evidence]
        task_lines = [f"{item.get('title')} [{item.get('status')}]" for item in tasks]
        expert_lines = [
            f"{item.get('email')} ({item.get('status')}, expires {item.get('expires_at')})"
            for item in experts
        ]
        timeline_lines = [
            f"{item.get('date')} [{item.get('type')}] {item.get('summary')}" for item in timeline
        ]
        body = (
            "Executive summary\n"
            f"{_format_lines(summary_lines)}\n\n"
            "Initial assessment (triage)\n"
            f"{_format_lines(triage_lines)}\n\n"
            "Impact analysis\n"
            f"{_format_lines(impact_lines)}\n\n"
            "Gate completion\n"
            f"{_format_lines(gate_lines)}\n\n"
            "Timeline of facts\n"
            f"{_format_lines(timeline_lines)}\n\n"
            "Evidence register\n"
            f"{_format_lines(evidence_lines)}\n\n"
            "Task checklist\n"
            f"{_format_lines(task_lines)}\n\n"
            "External expert access\n"
            f"{_format_lines(expert_lines)}\n\n"
            "Root cause & recommendations\n"
            f"{lessons or 'TBD'}\n"
        )
    elif doc_type == "ERASURE_CERTIFICATE":
        body = (
            "Certificate of destruction\n"
            "This certificate confirms that investigation data associated with the case has been erased.\n"
        )
    elif doc_type == "SILENT_LEGAL_HOLD":
        hold = extra_data or {}
        body = (
            "Confidential preservation instruction\n"
            f"Hold ID: {hold.get('hold_id', 'TBD')}\n"
            f"Contact: {hold.get('contact_name', 'TBD')}\n"
            f"Contact role: {hold.get('contact_role', 'TBD')}\n"
            f"Contact email: {hold.get('contact_email', 'TBD')}\n"
            f"Delivery channel: {hold.get('delivery_channel', 'TBD')}\n"
            f"Preservation scope: {hold.get('preservation_scope', 'TBD')}\n"
            "Access code delivered out-of-band.\n"
        )
    elif doc_type == "US_LEGAL_HOLD":
        hold = extra_data or {}
        body = (
            "US legal hold notification\n"
            f"Hold ID: {hold.get('hold_id', 'TBD')}\n"
            f"Preserve mailbox/system: {hold.get('preservation_scope', 'TBD')}\n"
            f"Contact: {hold.get('contact_name', 'TBD')}\n"
            f"Contact role: {hold.get('contact_role', 'TBD')}\n"
            f"Contact email: {hold.get('contact_email', 'TBD')}\n"
            f"Delivery channel: {hold.get('delivery_channel', 'TBD')}\n"
            "Do not notify the subject of this hold.\n"
        )
    elif doc_type == "WORKS_COUNCIL_REQUEST":
        data = extra_data or {}
        body = (
            "Works Council approval request\n"
            f"Case: {case.case_id}\n"
            f"Jurisdiction: {case.jurisdiction}\n"
            f"Monitoring required: {data.get('monitoring', False)}\n"
            f"Summary: {data.get('summary', 'TBD')}\n"
            f"Requester: {data.get('requested_by', 'TBD')}\n"
            "Please review and provide approval documentation before monitoring begins.\n"
        )
    else:
        body = "Template pending."

    rendered_text = header + body
    payload = {
        "doc_type": doc_type,
        "title": template.title,
        "rendered_text": rendered_text,
    }
    return template.title, payload


def normalize_document_format(format_value: str | None) -> str:
    if not format_value:
        return "txt"
    normalized = format_value.strip().lower()
    if normalized in {"text", "plain"}:
        normalized = "txt"
    if normalized not in SUPPORTED_DOCUMENT_FORMATS:
        raise ValueError("Unsupported document format")
    return normalized


def render_document_bytes(format_value: str, rendered_text: str) -> tuple[bytes, str]:
    normalized = normalize_document_format(format_value)
    if normalized == "txt":
        return rendered_text.encode("utf-8"), "text/plain"
    if normalized == "pdf":
        try:
            from reportlab.lib.pagesizes import LETTER
            from reportlab.pdfgen import canvas
        except Exception as exc:  # pragma: no cover - optional dependency
            raise ValueError("PDF rendering requires reportlab.") from exc
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=LETTER)
        width, height = LETTER
        text = pdf.beginText(40, height - 40)
        text.setLeading(14)
        for line in rendered_text.splitlines() or [""]:
            for wrapped in textwrap.wrap(line, width=110) or [""]:
                if text.getY() < 40:
                    pdf.drawText(text)
                    pdf.showPage()
                    text = pdf.beginText(40, height - 40)
                    text.setLeading(14)
                text.textLine(wrapped)
        pdf.drawText(text)
        pdf.save()
        buffer.seek(0)
        return buffer.read(), "application/pdf"
    if normalized == "docx":
        try:
            from docx import Document
        except Exception as exc:  # pragma: no cover - optional dependency
            raise ValueError("DOCX rendering requires python-docx.") from exc
        doc = Document()
        for line in rendered_text.splitlines() or [""]:
            doc.add_paragraph(line)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    raise ValueError("Unsupported document format")
