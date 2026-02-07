---
title: "Insider Threat Investigation Playbook"
description: "Standard operating procedure for investigating potential insider threat indicators."
type: "playbook"
format: "markdown"
version: "1.0"
author: "Security Operations"
---

# Insider Threat Investigation Playbook

## 1. Initial Triage
- **Trigger**: Alert received from DLP, SIEM, or HR referral.
- **Action**: Verify the user identity and role.
- **Decision**: Is this anomalous behavior for this role?
    - *Yes*: Proceed to Step 2.
    - *No*: Close as False Positive.

## 2. Data Collection
Gather the following logs for the last 30 days:
- Web Proxy Logs
- Email Archives
- USB Activity Logs
- Building Access Logs

## 3. Analysis
Look for:
- [ ] Large data uploads to personal cloud storage.
- [ ] Emails with attachments sent to personal accounts.
- [ ] Off-hours building access.

## 4. Response
If intent is confirmed:
1.  Notify Legal and HR.
2.  Preserve evidence forensic image.
3.  Conduct interview (if approved).

## 5. Closure
Document all findings in the Case Management System.
