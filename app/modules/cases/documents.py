from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.modules.cases import models


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
    else:
        body = "Template pending."

    rendered_text = header + body
    payload = {
        "doc_type": doc_type,
        "title": template.title,
        "rendered_text": rendered_text,
    }
    return template.title, payload
