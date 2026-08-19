# LLMantis — Governance V2

## Overview

Governance V2 is the current governance framework for this repository, assessed against commit `114ebc9`. It **supersedes Governance V1** (the prior `GOV-01`..`GOV-10`/`LOG-01`/`LOG-02` framework, assessed against commit `f48fdbf`), which has been removed from the working tree per a team decision to close it out cleanly rather than carry it forward as archived clutter.

**Governance V1 remains fully recoverable via git history** even though it no longer exists as files: `git show 474b20e:governance/reports/GOVERNANCE_REPORT.md` (and any other V1 path) will return its exact content, since `474b20e` remains a permanent ancestor commit. Nothing about V1 was lost — it was deliberately not archived in the working tree, by explicit instruction, not deleted without a recovery path.

**No V1 finding was carried forward into V2.** Every one of the 17 V2 controls below was independently reassessed against the current implementation.

## Scope

17 controls across two domains:

**Frontend (5):** FE-01 AI Transparency and User Disclosure · FE-02 Legal and Regulatory Information · FE-03 User-Facing Security and Privacy · FE-04 Output, Report and Claim Integrity · FE-05 Accessibility, User Understanding and Human Interaction

**Backend / Platform (12):** BE-01 AI Component and Provider Governance · BE-02 AI Attack Library Governance · BE-03 AI Risk and Scoring Governance · BE-04 AI Judge Validation and Calibration · BE-05 Target Authorization and Active Testing Control · BE-06 Authentication and Access Control · BE-07 Sensitive Data and Secret Protection · BE-08 Application and Network Security · BE-09 Evidence, Traceability and Data Integrity · BE-10 Change, Dependency and Configuration Management · BE-11 Regression Testing and Operational Monitoring · BE-12 Security and Governance Logging

Full definitions: `controls/frontend-controls.yaml`, `controls/backend-controls.yaml`. Full assessment: `reports/GOVERNANCE_V2_REPORT.md`. Per-control evidence: `evidence/<CONTROL-ID>/EVIDENCE.md`.

## Assessment methodology

Every control was assessed against the **feature + code path + enforcement** principle — a security or compliance feature existing somewhere in the repository is not, by itself, evidence that the control it relates to is compliant. The clearest example: SSRF protection (BE-08) is real and thorough on the Art. 50 Check path but absent from the active-scan path, despite shared documentation claiming both are covered — this was found by tracing actual code usage, not by confirming a guard module exists.

## Status vocabulary

- **COMPLIANT** — every sub-requirement of the control's intent is met, with direct evidence, and no known gap remains.
- **PARTIALLY COMPLIANT — XX%** — some but not all of the control's intent is met.
- **NON-COMPLIANT** — the core thing the control checks for is absent or contradicted by evidence.

## Percentage methodology

Each control decomposes into 2–4 explicit sub-checks derived from its Control Explanation. Where sub-checks are cleanly countable, percentage = `(sub-checks met ÷ total) × 100`. Where a control is genuinely continuous (e.g. "how well do these legal claims hold up"), the percentage reflects explicit, stated qualitative reasoning rather than a forced ratio — every `EVIDENCE.md` in this framework shows its work rather than asserting a bare number. No percentage in this framework should be read as more precise than the reasoning behind it.

## Regulatory reference discipline

Every control's regulatory/reference basis distinguishes **LEGAL REQUIREMENT** (a binding law/article, cited with its specific number) from **BEST-PRACTICE** (an industry convention, e.g. OWASP) from **INTERNAL POLICY** (an LLMantis decision, not an external requirement). Where a regulation's *direct* applicability to a specific control has not been independently verified, this framework says so explicitly rather than asserting it — see, for example, BE-01's GDPR Art. 44 note, or FE-01's note on Art. 50(1)'s applicability to LLMantis's own architecture. This framework does not perform new legal research; it records what has been verified and flags what hasn't.

## Legal and claims governance

This framework is a technical governance assessment, not legal advice, and does not establish legal compliance with any statute referenced in it. See `docs/legal/DISCLAIMERS.md`, `docs/legal/LEGAL-MAP.md`, and `docs/legal/FORBIDDEN-WORDS.md` (retained outside this migration; not part of Governance V1's retirement). LLMantis is not a certification body and this framework does not certify anything — see EU AI Act Art. 43 and FE-02/BE-... references throughout.

## Distribution

This is an **internal working baseline**. It is not to be published or pushed externally in its current form without separate review and approval.

## How to use this framework going forward

1. Re-run the checker (`scripts/run_governance_v2.py`) after any change to `backend/`, `frontend/`, `attacks/`, or `calibration/`, and compare its output against `reports/GOVERNANCE_V2_REPORT.md`.
2. Treat every `PARTIALLY COMPLIANT` and `NON-COMPLIANT` control as a tracked backlog item — the Top 5 Priority Recommendations in the report are the current starting point.
3. Update `controls/*.yaml` when a control's scope or criteria change, so the checker and its documentation don't drift apart.
4. This framework does not self-certify its own completeness or currency — a human reviewer should periodically re-read the report against the live repository, the same discipline that made Governance V1 outdated in the first place.
