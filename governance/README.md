# LLMantis Governance V2

![LLMantis Governance V2](https://img.shields.io/badge/LLMantis-Governance%20V2-1f6feb)
![17 Controls](https://img.shields.io/badge/Controls-17-2ea043)
![5 Frontend Controls](https://img.shields.io/badge/Frontend-5%20Controls-8250df)
![12 Backend / Platform Controls](https://img.shields.io/badge/Backend%2FPlatform-12%20Controls-bc4c00)
![Evidence-Based Assessment](https://img.shields.io/badge/Assessment-Evidence--Based-6e7781)

## Overview

LLMantis Governance V2 is an evidence-based technical governance framework for the LLMantis platform. It assesses 17 controls across the frontend and backend, each independently verified against the current codebase — implementation, configuration, and enforcement — rather than against documentation or intent alone.

## Framework at a Glance

| Domain | Controls | Focus |
|---|---:|---|
| Frontend | 5 | User-facing transparency, claims, privacy, reporting and workflow |
| Backend / Platform | 12 | Security, authorization, AI evaluation, persistence and operational governance |
| Total | 17 | LLMantis Governance V2 |

## Frontend Controls

| ID | Control | Why It Matters | Reference |
|---|---|---|---|
| FE-01 | AI Transparency and User Disclosure | Confirms AI involvement is disclosed on tested sites, and that LLMantis's own interfaces never impersonate a human. | LEGAL REQUIREMENT — EU AI Act Art. 50(1) |
| FE-02 | Legal and Regulatory Information | Confirms legal and compliance claims on the marketing site do not overstate what the cited law or case actually supports. | LEGAL REQUIREMENT — § 5 UWG; EU AI Act Art. 43; CASE LAW — *Moffatt v. Air Canada* (persuasive only, not binding EU/German law) |
| FE-03 | User-Facing Security and Privacy | Confirms the Impressum and privacy notice meet basic German statutory disclosure duties for a live commercial site. | LEGAL REQUIREMENT — German DDG § 5; GDPR Art. 13, 14 |
| FE-04 | Output, Report and Claim Integrity | Confirms report and scan output accurately represent what happened — grade, scope, confidence, and authorization status. | LEGAL REQUIREMENT — § 5 UWG; INTERNAL POLICY — evidentiary-integrity policy |
| FE-05 | Accessibility, User Understanding and Human Interaction | Confirms non-technical users can understand AI-judge results and confidence levels, with basic accessibility semantics present. | BEST PRACTICE — WCAG-aligned conventions; INTERNAL POLICY — clarity policy |

## Backend / Platform Controls

| ID | Control | Why It Matters | Reference |
|---|---|---|---|
| BE-01 | AI Component and Provider Governance | Confirms AI models/providers in use are identified and consistent with a stated data-residency policy. | LEGAL REQUIREMENT — GDPR Art. 44 et seq. (applicability not independently verified); INTERNAL POLICY — PLAYBOOK.md §1 |
| BE-02 | AI Attack Library Governance | Confirms the attack library is structured, validated, and unambiguous about which version ran for a given scan. | BEST PRACTICE — OWASP Top 10 for LLM Applications |
| BE-03 | AI Risk and Scoring Governance | Confirms the scoring/grading formula is sound, internally consistent, and correctly reflected wherever it is displayed. | INTERNAL POLICY — internal scoring methodology |
| BE-04 | AI Judge Validation and Calibration | Confirms the AI judge's accuracy has been measured against human judgment, with limitations disclosed. | BEST PRACTICE — ISO/IEC 42001 (structuring reference only, not certification) |
| BE-05 | Target Authorization and Active Testing Control | Confirms an active scan against a live, customer-owned endpoint is gated on verified proof of ownership. | INTERNAL POLICY — PLAYBOOK.md Part II §4 |
| BE-06 | Authentication and Access Control | Confirms login, session, role-based permission, and API-key mechanisms are implemented securely. | LEGAL REQUIREMENT — GDPR Art. 32; BEST PRACTICE — OWASP A01, A02, A07 |
| BE-07 | Sensitive Data and Secret Protection | Confirms credentials and secrets are not hardcoded and are stored safely. | LEGAL REQUIREMENT — GDPR Art. 32 |
| BE-08 | Application and Network Security | Confirms SSRF protection covers every outbound-request code path to customer-supplied URLs, and that rate limiting is effective. | BEST PRACTICE — OWASP A10 (SSRF), A04 (resource exhaustion) |
| BE-09 | Evidence, Traceability and Data Integrity | Confirms a persisted scan record traces back to the scan, the attack-library version, and the content actually tested. | LEGAL REQUIREMENT — GDPR Art. 32; INTERNAL POLICY — traceability policy |
| BE-10 | Change, Dependency and Configuration Management | Confirms significant changes are reviewed, dependencies are complete and accurate, and deployment configuration is hardened. | BEST PRACTICE — standard change-management practice |
| BE-11 | Regression Testing and Operational Monitoring | Confirms automated tests, CI, and operational monitoring exist to catch regressions before production. | BEST PRACTICE — standard QA practice |
| BE-12 | Security and Governance Logging | Confirms security-relevant events are captured durably and administrative/security actions can be reconstructed after the fact. | LEGAL REQUIREMENT — GDPR Art. 32, Art. 5(2); BEST PRACTICE — OWASP A09 |

## Assessment Methodology

Each control receives one of three statuses:

- **COMPLIANT — 100%** — the control is implemented and supported by available evidence, with no known gap.
- **PARTIALLY COMPLIANT — 1–99%** — the control is implemented in part, but material gaps or limitations remain. The percentage reflects countable sub-checks where the control decomposes cleanly, or explicit, shown reasoning where it does not.
- **NON-COMPLIANT — 0%** — the control is absent or materially ineffective.

Every regulatory `Reference` distinguishes **LEGAL REQUIREMENT** (a binding law or article, cited by number), **BEST PRACTICE** (an industry convention, not a legal obligation), and **INTERNAL POLICY** (an LLMantis decision, not an external requirement).

## Evidence and Traceability

Every control has its own evidence directory:

```
governance/evidence/<CONTROL-ID>/EVIDENCE.md
```

Each `EVIDENCE.md` documents what was checked, what was found, and why the control's status and percentage follow from that finding — providing direct traceability from a control to the evidence behind its assessment.

## Assessment Report

The full assessment is recorded in:

```
governance/reports/GOVERNANCE_V2_REPORT.md
```

This report contains the detailed discovery, status, compliance percentage, and recommendation for all 17 controls, and is the single official assessment of record.

## Repository Structure

```
governance/
├── README.md
├── controls/
│   ├── frontend-controls.yaml
│   └── backend-controls.yaml
├── evidence/
├── reports/
│   └── GOVERNANCE_V2_REPORT.md
├── scripts/
│   └── run_governance_v2.py
└── tests/
    └── test_governance_v2.py
```

## Scope

LLMantis Governance V2 is an evidence-based technical governance assessment framework. It evaluates implemented controls and identifies areas requiring improvement. It is not a certification and does not constitute legal advice or a formal determination of legal compliance.

## Disclaimer

LLMantis Governance V2 is an evidence-based technical governance assessment framework. It evaluates implemented controls based on the evidence available at the time of assessment and identifies areas for improvement.

This framework is not a certification, legal opinion, or formal determination of regulatory compliance.
