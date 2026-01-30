from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class PlaybookTask:
    title: str
    description: str


@dataclass(frozen=True)
class PlaybookEvidence:
    label: str
    source: str
    description: str


@dataclass(frozen=True)
class Playbook:
    key: str
    title: str
    description: str
    tasks: List[PlaybookTask]
    evidence: List[PlaybookEvidence]


PLAYBOOKS: List[Playbook] = [
    Playbook(
        key="DATA_EXFIL",
        title="Data Exfiltration",
        description="High-risk data movement to external destinations.",
        tasks=[
            PlaybookTask("Confirm scope of access", "Identify systems and repositories accessed."),
            PlaybookTask("Review export vectors", "Check cloud uploads, removable media, and email exports."),
            PlaybookTask("Validate authorization", "Confirm whether data transfer was approved."),
        ],
        evidence=[
            PlaybookEvidence("Cloud upload logs", "DLP/SIEM", "Upload telemetry for external destinations."),
            PlaybookEvidence("Endpoint file access", "EDR/Endpoint", "File access and copy telemetry."),
            PlaybookEvidence("Email forwarding records", "Email gateway", "Forwarding rules and large attachments."),
        ],
    ),
    Playbook(
        key="FRAUD",
        title="Fraud",
        description="Financial misuse, expense fraud, or procurement manipulation.",
        tasks=[
            PlaybookTask("Identify impacted accounts", "List accounts, vendors, and systems involved."),
            PlaybookTask("Collect transaction trail", "Gather approvals, payments, and audit logs."),
            PlaybookTask("Interview decision makers", "Document approvals and justifications."),
        ],
        evidence=[
            PlaybookEvidence("Approval workflow logs", "ERP", "Approval chain and timestamps."),
            PlaybookEvidence("Payment records", "Finance system", "Transaction history and anomalies."),
            PlaybookEvidence("Vendor master changes", "ERP", "Recent edits to vendor profiles."),
        ],
    ),
    Playbook(
        key="SABOTAGE",
        title="Sabotage",
        description="Intentional disruption, system tampering, or damage.",
        tasks=[
            PlaybookTask("Isolate affected assets", "Identify systems, services, or IP impacted."),
            PlaybookTask("Preserve forensic data", "Snapshot logs and access history."),
            PlaybookTask("Assess safety impact", "Confirm whether safety controls were affected."),
        ],
        evidence=[
            PlaybookEvidence("Change management records", "ITSM", "Approved vs. unapproved changes."),
            PlaybookEvidence("Access badge logs", "Physical security", "Facility access during incident."),
            PlaybookEvidence("System audit logs", "SIEM", "Admin actions around disruption."),
        ],
    ),
]


def get_playbook(key: str) -> Playbook | None:
    for playbook in PLAYBOOKS:
        if playbook.key == key:
            return playbook
    return None
