#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from urllib import request, error

DEFAULT_API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000/api/v1")
DEFAULT_TENANT_KEY = os.getenv("TENANT_KEY", "default")
DEFAULT_ROLES = os.getenv("X_IRMMF_ROLES", "ADMIN")
DEFAULT_CLEANUP = os.getenv("CLEANUP", "0") in ("1", "true", "yes")

API_BASE = DEFAULT_API_BASE
TENANT_KEY = DEFAULT_TENANT_KEY
ROLES = DEFAULT_ROLES
CLEANUP = DEFAULT_CLEANUP

HEADERS = {
    "Content-Type": "application/json",
    "X-IRMMF-KEY": TENANT_KEY,
    "X-IRMMF-ROLES": ROLES,
}


FAILURES = 0


def _print(title: str, ok: bool, detail: str = ""):
    status = "PASS" if ok else "FAIL"
    line = f"[{status}] {title}"
    if detail:
        line += f" — {detail}"
    print(line)


def _report(title: str, ok: bool, detail: str = "") -> None:
    global FAILURES
    _print(title, ok, detail)
    if not ok:
        FAILURES += 1


def _request(method: str, path: str, payload=None, expect: int = 200, raw: bool = False):
    url = f"{API_BASE}{path}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, method=method, headers=HEADERS)
    try:
        with request.urlopen(req, timeout=10) as resp:
            body = resp.read()
            if raw:
                return resp.status, body
            if body:
                return resp.status, json.loads(body.decode("utf-8"))
            return resp.status, None
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {path} -> {exc.code} {body}") from exc
    except Exception as exc:
        raise RuntimeError(f"{method} {path} failed: {exc}") from exc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the investigation module smoke test.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="API base URL.")
    parser.add_argument("--tenant-key", default=DEFAULT_TENANT_KEY, help="Tenant key header value.")
    parser.add_argument("--roles", default=DEFAULT_ROLES, help="X-IRMMF-ROLES header value.")
    parser.add_argument("--cleanup", action="store_true", default=DEFAULT_CLEANUP, help="Anonymize case after run.")
    args = parser.parse_args()

    API_BASE = args.api_base
    TENANT_KEY = args.tenant_key
    ROLES = args.roles
    CLEANUP = args.cleanup
    HEADERS["X-IRMMF-KEY"] = TENANT_KEY
    HEADERS["X-IRMMF-ROLES"] = ROLES

    print("\nInvestigation Module Smoke Test")
    print(f"API_BASE={API_BASE} TENANT_KEY={TENANT_KEY}\n")
    try:
        _request("GET", "/dashboard")
        _report("Dashboard endpoint", True)
    except Exception as exc:
        _report("Dashboard endpoint", False, str(exc))
        sys.exit(1)

    title = f"Smoke Test Case {int(time.time())}"
    case_id = None
    try:
        status, case = _request(
            "POST",
            "/cases",
            {
                "title": title,
                "summary": "Automated smoke test case.",
                "jurisdiction": "Belgium",
            },
        )
        case_id = case["case_id"]
        _report("Create case", True, case_id)
    except Exception as exc:
        _report("Create case", False, str(exc))
        sys.exit(1)

    try:
        _request(
            "PATCH",
            f"/cases/{case_id}",
            {
                "summary": "Smoke test updated summary.",
                "jurisdiction": "Belgium",
            },
        )
        _report("Update case metadata", True)
    except Exception as exc:
        _report("Update case metadata", False, str(exc))

    try:
        _request(
            "POST",
            f"/cases/{case_id}/subjects",
            {"subject_type": "Employee", "display_name": "Test Subject", "reference": "EMP-1"},
        )
        _report("Add subject", True)
    except Exception as exc:
        _report("Add subject", False, str(exc))

    try:
        _request(
            "POST",
            f"/cases/{case_id}/evidence",
            {"label": "Email export", "source": "Email", "link": "file://placeholder"},
        )
        _report("Add evidence", True)
    except Exception as exc:
        _report("Add evidence", False, str(exc))

    try:
        _request(
            "POST",
            f"/cases/{case_id}/tasks",
            {"title": "Secure logs", "assignee": "investigator"},
        )
        _report("Add task", True)
    except Exception as exc:
        _report("Add task", False, str(exc))

    try:
        _request(
            "POST",
            f"/cases/{case_id}/notes",
            {"note_type": "general", "body": "Initial review complete."},
        )
        _report("Add note", True)
    except Exception as exc:
        _report("Add note", False, str(exc))

    # Stage transitions + gates
    try:
        _request("POST", f"/cases/{case_id}/stage", {"stage": "LEGITIMACY_GATE"})
        _report("Stage -> LEGITIMACY_GATE", True)
    except Exception as exc:
        _report("Stage -> LEGITIMACY_GATE", False, str(exc))

    try:
        _request(
            "POST",
            f"/cases/{case_id}/gates/legitimacy",
            {
                "legal_basis": "Suspicion of Fraud",
                "trigger_summary": "Automated trigger",
                "proportionality_confirmed": True,
                "less_intrusive_steps": "None",
                "mandate_owner": "Legal",
                "mandate_date": datetime.now(timezone.utc).date().isoformat(),
            },
        )
        _report("Legitimacy gate", True)
    except Exception as exc:
        _report("Legitimacy gate", False, str(exc))

    try:
        _request("POST", f"/cases/{case_id}/stage", {"stage": "CREDENTIALING"})
        _report("Stage -> CREDENTIALING", True)
    except Exception as exc:
        _report("Stage -> CREDENTIALING", False, str(exc))

    try:
        _request(
            "POST",
            f"/cases/{case_id}/gates/credentialing",
            {
                "investigator_name": "Automated Tester",
                "investigator_role": "Legal",
                "licensed": True,
                "license_id": "LIC-TEST",
                "conflict_check_passed": True,
                "authorizer": "General Counsel",
                "authorization_date": datetime.now(timezone.utc).date().isoformat(),
            },
        )
        _report("Credentialing gate", True)
    except Exception as exc:
        _report("Credentialing gate", False, str(exc))

    try:
        _request("POST", f"/cases/{case_id}/stage", {"stage": "INVESTIGATION"})
        _report("Stage -> INVESTIGATION", True)
    except Exception as exc:
        _report("Stage -> INVESTIGATION", False, str(exc))

    try:
        _request("POST", f"/cases/{case_id}/stage", {"stage": "ADVERSARIAL_DEBATE"})
        _report("Stage -> ADVERSARIAL_DEBATE", True)
    except Exception as exc:
        _report("Stage -> ADVERSARIAL_DEBATE", False, str(exc))

    try:
        _request(
            "POST",
            f"/cases/{case_id}/gates/adversarial",
            {
                "invitation_sent": True,
                "invitation_date": datetime.now(timezone.utc).date().isoformat(),
                "rights_acknowledged": True,
                "representative_present": "Union rep",
                "interview_summary": "Summary captured.",
            },
        )
        _report("Adversarial gate", True)
    except Exception as exc:
        _report("Adversarial gate", False, str(exc))

    try:
        _request("POST", f"/cases/{case_id}/stage", {"stage": "DECISION"})
        _report("Stage -> DECISION", True)
    except Exception as exc:
        _report("Stage -> DECISION", False, str(exc))

    try:
        _request(
            "POST",
            f"/cases/{case_id}/decision",
            {"outcome": "SANCTION", "summary": "Automated test decision."},
        )
        _report("Decision recorded", True)
    except Exception as exc:
        _report("Decision recorded", False, str(exc))

    try:
        _request(
            "POST",
            f"/cases/{case_id}/remediation-export",
            {"remediation_statement": "Test remediation export statement.", "format": "json"},
            raw=True,
        )
        _report("Remediation export", True)
    except Exception as exc:
        _report("Remediation export", False, str(exc))

    # Serious cause + notifications
    try:
        now = datetime.now(timezone.utc)
        _request(
            "POST",
            f"/cases/{case_id}/serious-cause/enable",
            {
                "enabled": True,
                "date_incident_occurred": now.isoformat(),
                "date_investigation_started": now.isoformat(),
                "decision_maker": "General Counsel",
            },
        )
        _report("Serious cause enabled", True)
    except Exception as exc:
        _report("Serious cause enabled", False, str(exc))

    try:
        _request(
            "POST",
            f"/cases/{case_id}/actions/submit-findings",
            {"confirmed_at": datetime.now(timezone.utc).isoformat()},
        )
        _report("Serious cause findings submitted", True)
    except Exception as exc:
        _report("Serious cause findings submitted", False, str(exc))

    try:
        status, notifications = _request("GET", f"/notifications?case_id={case_id}")
        found = bool(notifications)
        _report("Notifications created", found, f"count={len(notifications)}")
        if notifications:
            _request("POST", f"/notifications/{notifications[0]['id']}/ack")
            _report("Notification acknowledged", True)
    except Exception as exc:
        _report("Notifications flow", False, str(exc))

    try:
        _request("POST", f"/cases/{case_id}/documents/INVESTIGATION_MANDATE", {"format": "txt"})
        _report("Document generation", True)
    except Exception as exc:
        _report("Document generation", False, str(exc))

    try:
        _request("POST", f"/cases/{case_id}/stage", {"stage": "CLOSURE"})
        _report("Stage -> CLOSURE", True)
    except Exception as exc:
        _report("Stage -> CLOSURE", False, str(exc))

    if CLEANUP:
        try:
            _request("POST", f"/cases/{case_id}/anonymize", {"reason": "Smoke test cleanup"})
            _report("Cleanup anonymize", True)
        except Exception as exc:
            _report("Cleanup anonymize", False, str(exc))

    print("\nSmoke test complete.")
    if FAILURES:
        print(f"{FAILURES} check(s) failed.")
        sys.exit(1)
