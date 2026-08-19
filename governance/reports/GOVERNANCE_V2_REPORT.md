# LLMantis — Governance V2 Report

- **Baseline commit:** `114ebc9`
- **Supersedes:** Governance V1 (assessed against commit `f48fdbf`; V1 findings were not carried forward — every control below is an independent reassessment against the current implementation)
- **Scope:** 17 controls — 5 Frontend, 12 Backend/Platform
- **Methodology:** direct source-code inspection, cross-referenced against recorded project documentation (`PROJECT-STATE.md`, `GREGOR_WORKLOG.md`, `PLAYBOOK.md`) and, where noted, live-tested runtime behavior. Commit messages were not trusted as evidence on their own.
- **Distribution:** internal working baseline only. Not for external publication in its current form. Not a certification and does not establish legal compliance with any statute referenced below — see `docs/legal/DISCLAIMERS.md`.

---

## Summary

| | Count |
|---|---|
| Compliant | 3 |
| Partially Compliant | 11 |
| Non-Compliant | 3 |
| **Total** | **17** |

**Overall Governance Maturity: 57%** (simple, unweighted average across all 17 control percentages — not a formal statistical model.)

---

## FRONTEND CONTROLS

Control No.: FE-01
Control Name: AI Transparency and User Disclosure
Control Explanation: Does LLMantis clearly disclose AI involvement where it matters — both in what it tests for on customer sites, and in its own interfaces?
Regulation: LEGAL REQUIREMENT — EU AI Act, Regulation (EU) 2024/1689
Reference: Art. 50(1) (direct applicability to the Art. 50 Check's stated purpose; applicability to LLMantis's own non-conversational architecture not independently established)
Discovery: The Art. 50 Check is real, browser-automated, and correctly implements the disclosure test, including a verified fix for a prior false positive (a widget merely *named* "KI-Assistent" no longer counts as disclosure). LLMantis's own UI never impersonates a human anywhere.
Compliance Status: COMPLIANT
Compliance Percentage: 100%
Recommendation: None required.

---

Control No.: FE-02
Control Name: Legal and Regulatory Information
Control Explanation: Are the legal/compliance claims on the marketing site accurate and not overstated relative to what the cited law or case actually supports?
Regulation: LEGAL REQUIREMENT — § 5 UWG; CASE LAW — *Moffatt v. Air Canada* (foreign, persuasive only, not binding EU/German law); LEGAL REQUIREMENT — EU AI Act
Reference: § 5 UWG (direct); 2024 BCCRT 149; Art. 43 (basis for the "not a certification" claim)
Discovery: Certification language is correct and consistent site-wide. Three specific claims remain overstated on the live page: the Air Canada case is presented without a "foreign precedent, illustrative only" qualifier; "no regulation requires testing a chatbot" is stated as settled fact where the project's own analysis marks it unresolved; the GDPR Art. 33 (72-hour breach) claim omits its risk-based conditionality.
Compliance Status: PARTIALLY COMPLIANT
Compliance Percentage: 50%
Recommendation: Add the missing qualifiers to all three claims on `landing.html` directly.

---

Control No.: FE-03
Control Name: User-Facing Security and Privacy
Control Explanation: Do the Impressum and privacy notice meet basic German statutory disclosure duties?
Regulation: LEGAL REQUIREMENT — German DDG; LEGAL REQUIREMENT — GDPR
Reference: § 5 DDG; Art. 13, 14 GDPR
Discovery: Both `impressum.html` and `datenschutz.html` remain explicit, self-labelled "TODO — not legally reviewed" placeholders with unfilled fields.
Compliance Status: NON-COMPLIANT
Compliance Percentage: 0%
Recommendation: Complete both pages with real data and legal sign-off before public launch.

---

Control No.: FE-04
Control Name: Output, Report and Claim Integrity
Control Explanation: Does the report/scan output accurately represent what actually happened — the grade, the scan's scope, and the authorization status of the test?
Regulation: LEGAL REQUIREMENT — § 5 UWG; BEST-PRACTICE — internal evidentiary-integrity policy
Reference: § 5 UWG; N/A (internal policy, no external reference number)
Discovery: Scoring/grade display is consistent with the backend formula, and the report correctly shows the real attack-library version/name. Confidence display and the "no quote, no finding" rule are correctly applied in `report.html` but absent from `index.html`. Most significantly: `report.html`'s disclaimer unconditionally states *"Testing was performed with the verified consent of the system's owner"* on every report, regardless of whether verification actually occurred.
Compliance Status: PARTIALLY COMPLIANT
Compliance Percentage: 50%
Recommendation: Make the ownership-consent statement conditional on an actual verification flag from the scan record. Bring `index.html`'s confidence display up to `report.html`'s standard.

---

Control No.: FE-05
Control Name: Accessibility, User Understanding and Human Interaction
Control Explanation: Can a non-technical user understand what the AI judge did, what confidence levels mean, and interact with results appropriately?
Regulation: BEST-PRACTICE — WCAG-aligned accessibility conventions; internal clarity policy
Reference: WCAG (general conventions, no specific success criterion independently verified); N/A (internal policy)
Discovery: ARIA roles/live regions are present in the live feed and findings accordion; `report.html` explains the two-layer judging method in plain language. Several real backend capabilities (login, ownership verification, API keys, org/branding management) have no corresponding frontend workflow.
Compliance Status: PARTIALLY COMPLIANT
Compliance Percentage: 70%
Recommendation: Prioritize a minimal UI for ownership verification and API key management.

---

## BACKEND / PLATFORM CONTROLS

Control No.: BE-01
Control Name: AI Component and Provider Governance
Control Explanation: Are the AI models/providers identified, and is their configuration consistent with a stated data-residency policy?
Regulation: LEGAL REQUIREMENT — GDPR (applicability not independently verified); INTERNAL POLICY — `PLAYBOOK.md`
Reference: Art. 44 et seq.; PLAYBOOK.md §1 (EU-only invariant, explicitly withdrawn)
Discovery: Default provider is now a generic Azure OpenAI-compatible endpoint with an operator-configured, unenforced region; Mistral remains available; Anthropic fully removed. No replacement residency policy exists.
Compliance Status: PARTIALLY COMPLIANT
Compliance Percentage: 50%
Recommendation: Document a current data-residency stance.

---

Control No.: BE-02
Control Name: AI Attack Library Governance
Control Explanation: Is the attack library structured, validated, and unambiguous about which version ran?
Regulation: BEST-PRACTICE — OWASP Top 10 for LLM Applications
Reference: N/A (general framework reference, no specific numbered item cited)
Discovery: Two libraries coexist (`attacks.yaml` v2.0/78 attacks; `attacks_short.yaml` v1.4/21 attacks, the default). Both pass the same validation logic. No automated test protects it. Disambiguating which library ran requires checking two fields together.
Compliance Status: PARTIALLY COMPLIANT
Compliance Percentage: 70%
Recommendation: Add a prominent "library used" indicator and a validation test.

---

Control No.: BE-03
Control Name: AI Risk and Scoring Governance
Control Explanation: Is the scoring/grading formula sound, internally consistent, and correctly displayed?
Regulation: BEST-PRACTICE — internal scoring methodology
Reference: N/A (internal policy, no external reference number)
Discovery: Deduction-based formula verified in sync between implementation and its offline reference copy, and matches frontend display.
Compliance Status: COMPLIANT
Compliance Percentage: 100%
Recommendation: None on the formula itself; see BE-11 for the separate lack of test coverage.

---

Control No.: BE-04
Control Name: AI Judge Validation and Calibration
Control Explanation: Has the AI judge's accuracy been measured against human judgment, with limitations disclosed?
Regulation: BEST-PRACTICE — ISO/IEC 42001
Reference: Structuring reference only, not certification
Discovery: Real, reproducible calibration: 29/29 stable agreement on the original set across 10 runs; deterministic layer 11/11 and 13/13 with zero disagreements; 95.3% mean agreement on an expanded set. Six newly-added criteria are validated only in the false-positive direction, honestly disclosed.
Compliance Status: PARTIALLY COMPLIANT
Compliance Percentage: 85%
Recommendation: Extend calibration to validate newer criteria in both directions.

---

Control No.: BE-05
Control Name: Target Authorization and Active Testing Control
Control Explanation: Is an active scan against a live endpoint gated on verified ownership?
Regulation: INTERNAL POLICY — `PLAYBOOK.md`
Reference: Part II §4 (ownership-verification rule)
Discovery: Real DNS-TXT verification with secure tokens, a 24-hour challenge window, and a 90-day re-verification window, both enforced. One org-unscoped waiver list exists, empty by default.
Compliance Status: PARTIALLY COMPLIANT
Compliance Percentage: 85%
Recommendation: Scope the waiver mechanism per-organization.

---

Control No.: BE-06
Control Name: Authentication and Access Control
Control Explanation: Are login, session, role-based permission, and API-key mechanisms secure?
Regulation: LEGAL REQUIREMENT — GDPR (general); BEST-PRACTICE — OWASP Top 10
Reference: Art. 32; A01, A02, A07
Discovery: Bcrypt hashing, JWT with revocation, lockout, a verified fix for a login timing side-channel. Role checks use rank comparison, fail closed. API keys are SHA-256 hashed at rest, revocation checked on every use. Cross-tenant isolation not independently tested.
Compliance Status: COMPLIANT
Compliance Percentage: 100%
Recommendation: Perform explicit cross-tenant access testing before onboarding multiple real organizations.

---

Control No.: BE-07
Control Name: Sensitive Data and Secret Protection
Control Explanation: Are credentials and secrets handled without hardcoding?
Regulation: LEGAL REQUIREMENT — GDPR (general)
Reference: Art. 32
Discovery: API keys/passwords properly hashed. A development database credential is hardcoded in `config.py`, `.env.example`, and `docker-compose.yml`.
Compliance Status: PARTIALLY COMPLIANT
Compliance Percentage: 70%
Recommendation: Remove the hardcoded default; require an explicit `DATABASE_URL`.

---

Control No.: BE-08
Control Name: Application and Network Security
Control Explanation: Is SSRF protection applied to every outbound-request code path, and is rate limiting effective?
Regulation: BEST-PRACTICE — OWASP Top 10
Reference: A10 (SSRF), A04 (resource exhaustion)
Discovery: SSRF protection is thorough on the Art. 50 Check path (per-redirect-hop, per-request, DNS-rebinding-aware). **Entirely absent** from the active-scan path in `scanner.py`, despite the guard module's own documentation claiming both paths are covered. Per-IP rate limiting is real and endpoint-sensitivity-aware.
Compliance Status: PARTIALLY COMPLIANT
Compliance Percentage: 50%
Recommendation: **Highest-priority technical finding.** Apply the SSRF guard to the active-scan HTTP client.

---

Control No.: BE-09
Control Name: Evidence, Traceability and Data Integrity
Control Explanation: Does a persisted scan record trace back to the scan, attack-library version, and tested content?
Regulation: LEGAL REQUIREMENT — GDPR (general); BEST-PRACTICE — internal traceability policy
Reference: Art. 32; N/A (internal policy)
Discovery: Attack-library version and the actual tested prompt now genuinely persist. Target display name remains a hardcoded placeholder ("Prompt-based target") in the common scan mode. At-rest encryption not independently verified.
Compliance Status: PARTIALLY COMPLIANT
Compliance Percentage: 70%
Recommendation: Persist the real target display name; verify at-rest encryption.

---

Control No.: BE-10
Control Name: Change, Dependency and Configuration Management
Control Explanation: Are changes reviewed, dependencies complete, and deployment configuration hardened?
Regulation: BEST-PRACTICE — standard change-management practice
Reference: N/A (general industry practice, no specific standard cited)
Discovery: Only 19 of 168 commits since the prior baseline (11%) were merged via reviewed PRs. Dependency declarations are now complete. Production deployment configuration unconditionally trusts `X-Forwarded-For`.
Compliance Status: PARTIALLY COMPLIANT
Compliance Percentage: 25%
Recommendation: Require review for auth/ownership/SSRF/deployment changes; constrain trusted-proxy IPs.

---

Control No.: BE-11
Control Name: Regression Testing and Operational Monitoring
Control Explanation: Do automated tests, CI, and monitoring exist to catch regressions?
Regulation: BEST-PRACTICE — standard QA practice
Reference: N/A (general industry practice, no specific standard cited)
Discovery: Zero test files anywhere in `backend/`. No CI configuration anywhere. No monitoring/alerting beyond a basic `/api/health` endpoint.
Compliance Status: NON-COMPLIANT
Compliance Percentage: 0%
Recommendation: Prioritize tests for auth, ownership verification, and SSRF handling, plus a CI gate.

---

Control No.: BE-12
Control Name: Security and Governance Logging
Control Explanation: Are security events captured durably, and can administrative actions be reconstructed?
Regulation: LEGAL REQUIREMENT — GDPR (general); BEST-PRACTICE — OWASP Top 10
Reference: Art. 32, Art. 5(2); A09
Discovery: Zero use of Python's `logging` module anywhere in `backend/`. No dedicated audit-log entity for authentication, ownership-verification, or API-key events.
Compliance Status: NON-COMPLIANT
Compliance Percentage: 0%
Recommendation: Introduce structured logging and an append-only audit-log table.

---

## TOP 5 PRIORITY RECOMMENDATIONS

1. Make the report's ownership-consent statement conditional on real verification (FE-04).
2. Extend SSRF protection to the active-scan HTTP path (BE-08).
3. Introduce structured logging and a dedicated audit-log entity (BE-12).
4. Build a regression safety net and require review for security-relevant changes (BE-11, BE-10).
5. Complete the Impressum and Datenschutz pages (FE-03).

---
*Governance V2 baseline: commit `114ebc9`. Governance V1 (baseline `f48fdbf`) has been removed from the working tree per team decision; its content remains recoverable via `git show 474b20e:governance/...`.*
