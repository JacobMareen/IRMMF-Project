from __future__ import annotations

from app.modules.pia.schemas import PiaBullet, PiaKeyDate, PiaOverview, PiaRoadmapPhase, PiaSection


PIA_OVERVIEW = PiaOverview(
    module_key="pia",
    title="Procedural Compliance Platform",
    subtitle="Operationalizing insider risk investigations under the Belgian Private Investigations Act 2024.",
    executive_summary=(
        "The Belgian Private Investigations Act 2024 turns internal investigations into a regulated activity and "
        "makes evidence inadmissible when core procedural rules are violated. Fortune 500 organizations now need a "
        "workflow layer that translates alerts into legally compliant investigations, not just more telemetry. "
        "This module defines that workflow, embeds statutory guardrails, and links day-to-day case handling to "
        "maturity outcomes."
    ),
    key_dates=[
        PiaKeyDate(
            date="December 6, 2024",
            requirement="Act published; the new regulatory regime for private investigations begins with transitional measures.",
        ),
        PiaKeyDate(
            date="December 16, 2026",
            requirement="Mandatory internal investigation policy must be in force for employers operating in Belgium.",
        ),
    ],
    sections=[
        PiaSection(
            key="regulatory_shift",
            title="Regulatory Shift (PIA 2024)",
            summary="Internal investigation services are explicitly regulated, with licensing, policy, and evidentiary constraints.",
            bullets=[
                PiaBullet(
                    title="Licensing & credentialing",
                    detail="Systematic internal investigation services require authorization, vetted personnel, and ID cards.",
                    tags=["Licensing", "Internal Service"],
                ),
                PiaBullet(
                    title="Occasional vs. systematic",
                    detail="HR-led occasional investigations remain possible but must avoid drifting into systematic activity.",
                    tags=["HR Exemption"],
                ),
                PiaBullet(
                    title="Mandatory internal policy",
                    detail="A transparent internal regulation is required by December 16, 2026, including methods and rights.",
                    tags=["Policy", "Deadline"],
                ),
                PiaBullet(
                    title="Prohibited data",
                    detail="Political opinions, religious beliefs, union membership, and health data are off-limits for investigations.",
                    tags=["Data"],
                ),
                PiaBullet(
                    title="Statutory nullity",
                    detail="Core breaches trigger evidence nullity, removing judicial discretion to salvage the case record.",
                    tags=["Evidence"],
                ),
            ],
        ),
        PiaSection(
            key="operational_gap",
            title="Operational Gap",
            summary="Technical detection outpaces compliant resolution, especially for cross-border Fortune 500 workflows.",
            bullets=[
                PiaBullet(
                    title="Alert-to-investigation gap",
                    detail="UEBA/DLP/SIEM tools flag anomalies but do not govern interviews, mandates, or evidence handling.",
                    tags=["Detection"],
                ),
                PiaBullet(
                    title="Jurisdictional friction",
                    detail="US or UK security teams can unintentionally violate Belgian labor and privacy rules remotely.",
                    tags=["Cross-border"],
                ),
                PiaBullet(
                    title="Evidentiary risk",
                    detail="A single procedural miss can void a case, leading to reinstatement or damages despite technical proof.",
                    tags=["Litigation"],
                ),
            ],
        ),
        PiaSection(
            key="procedural_controls",
            title="Core Workflow Controls",
            summary="The module enforces required steps and artifacts before an investigation can advance.",
            bullets=[
                PiaBullet(
                    title="Legitimacy & proportionality gate",
                    detail="Mandate wizard captures legal basis and least-intrusive justification before collection begins.",
                    tags=["Mandate"],
                ),
                PiaBullet(
                    title="Investigator credentialing",
                    detail="Assignment logic blocks unlicensed users from systematic investigations.",
                    tags=["Access"],
                ),
                PiaBullet(
                    title="Adversarial debate",
                    detail="Interview rights, invitations, and response logs are mandatory prior to recommendations.",
                    tags=["Due Process"],
                ),
                PiaBullet(
                    title="Data minimization & erasure",
                    detail="Relevance tagging and timed destruction workflows align retention with outcomes.",
                    tags=["GDPR"],
                ),
                PiaBullet(
                    title="Prohibited data sanitization",
                    detail="NLP flags sensitive categories to prevent tainting the record.",
                    tags=["Safeguards"],
                ),
            ],
        ),
        PiaSection(
            key="jurisdictional_guardrails",
            title="Jurisdictional Guardrails",
            summary="Controls keep Belgian cases compliant even in global operating models.",
            bullets=[
                PiaBullet(
                    title="Geo-jurisdiction routing",
                    detail="Belgium-based subjects are routed to licensed local investigators with non-compliant users blocked.",
                    tags=["Routing"],
                ),
                PiaBullet(
                    title="Regulatory threshold monitoring",
                    detail="Alerts compliance leaders when volume or tactics risk reclassification as systematic activity.",
                    tags=["Monitoring"],
                ),
                PiaBullet(
                    title="Works council transparency",
                    detail="Aggregated audit views support social partner oversight without exposing identities.",
                    tags=["Works Council"],
                ),
            ],
        ),
        PiaSection(
            key="maturity_value",
            title="Maturity Integration & Value",
            summary="Operational data drives maturity scoring and defensibility for general counsel.",
            bullets=[
                PiaBullet(
                    title="Real-time maturity signals",
                    detail="Workflow completion metrics feed CMU SEI maturity levels continuously.",
                    tags=["Maturity"],
                ),
                PiaBullet(
                    title="Defensibility by design",
                    detail="Checklist enforcement reduces the probability of evidence exclusion in labor courts.",
                    tags=["Admissibility"],
                ),
                PiaBullet(
                    title="Executive dashboards",
                    detail="Case timelines, license status, and erasure compliance surface program health.",
                    tags=["Reporting"],
                ),
            ],
        ),
    ],
    roadmap=[
        PiaRoadmapPhase(
            phase="Phase 1",
            focus="Foundation & policy alignment",
            deliverables=[
                "Policy template library mapped to PIA requirements",
                "Legitimacy mandate generator with audit trail",
                "Investigator credential registry and access rules",
                "Case intake with legal basis capture",
            ],
        ),
        PiaRoadmapPhase(
            phase="Phase 2",
            focus="Workflow enforcement",
            deliverables=[
                "Adversarial debate workflow with automated letters",
                "Evidence intake and chain-of-custody tracking",
                "Data minimization and timed erasure certificates",
                "Prohibited data flagging for reports",
            ],
        ),
        PiaRoadmapPhase(
            phase="Phase 3",
            focus="Scale, analytics, and integration",
            deliverables=[
                "Geo-jurisdiction routing and cross-border controls",
                "HR exemption threshold monitoring",
                "Maturity dashboards tied to CMU SEI model",
                "SIEM/HRIS integration points",
            ],
        ),
    ],
)
