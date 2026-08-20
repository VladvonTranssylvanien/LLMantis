# LLMantis — Governance V2 Report

- **Baseline commit:** `f301d3e` (second full re-assessment)
- **Previous baseline:** `114ebc9` (first Governance V2 pass; findings below are independently re-verified against current code, not carried forward)
- **Scope:** 17 controls — 5 Frontend, 12 Backend/Platform
- **Methodology:** direct source-code inspection at the current commit, cross-referenced against recorded project documentation (`PROJECT-STATE.md`, `GREGOR_WORKLOG.md`, `PLAYBOOK.md`) and, where noted, live-tested runtime behavior. Commit messages were not trusted as evidence on their own — every claim below is backed by a file path, and every changed file since the previous baseline was independently re-read rather than assumed unaffected.
- **Distribution:** internal working baseline. Not a certification and does not establish legal compliance with any statute referenced below — see `docs/legal/DISCLAIMERS.md`.

---

## Summary

| | Count |
|---|---|
| Compliant | 2 |
| Partially Compliant | 13 |
| Non-Compliant | 2 |
| **Total** | **17** |

**Overall Governance Maturity: 54%** (simple, unweighted average across all 17 control percentages — not a formal statistical model.)

**Change since the previous pass (`114ebc9`, 57%):** the maturity figure has moved down, not up, even though real engineering work landed in between. Two controls previously marked with high confidence (BE-03 at 100%, BE-04 at 85%) turned out on deeper re-verification to rest on evidence that no longer describes the current system precisely — a formula fix that didn't reach its own reference copy, and calibration numbers that predate two judge changes. One control (BE-10) regressed on a measurable fact (the reviewed-PR rate fell from 11% to 0%). Two controls improved in substance (BE-03's production behavior, BE-09's traceability) even though their scores moved down once the deeper gaps were counted. This is discussed control-by-control below.

---

## FRONTEND CONTROLS

Control No.: FE-01
Control Name: AI Transparency and User Disclosure
Control Explanation: Does LLMantis clearly disclose AI involvement where it matters — both in what it tests for on customer sites, and in its own interfaces?
Regulation: LEGAL REQUIREMENT — EU AI Act, Regulation (EU) 2024/1689
Reference: Art. 50(1) (direct applicability to the Art. 50 Check's stated purpose; applicability to LLMantis's own non-conversational architecture not independently established)
Discovery: `backend/art50engine.py` is byte-for-byte unchanged since the previous baseline and remains the real, live implementation behind `POST /api/art50check`, which `frontend/art50check.html` posts to. Two additions since the previous pass do not change this control: `frontend/art50report.html` is a print/PDF sibling of `report.html`, populated only from data the backend already returned (no new claim, no new endpoint); `tools/voice50/` (phone-based disclosure checking) is confirmed unshipped — zero references to it exist anywhere in `backend/`, `frontend/`, or the `Dockerfile`, and its own README states "Nothing in the shipped product is touched by this file." A test fixture inside it deliberately impersonates a human, but only as the simulated *target* the checker is validated against, not as an LLMantis-owned interface. No LLMantis interface anywhere presents itself as human.
Status: COMPLIANT
Compliance Percentage: 100%
Recommendation: None required. If `tools/voice50` is later wired into the shipped product, re-assess this control against the live call flow before claiming the same status.

---

Control No.: FE-02
Control Name: Legal and Regulatory Information
Control Explanation: Are the legal/compliance claims on the marketing site accurate and not overstated relative to what the cited law or case actually supports?
Regulation: LEGAL REQUIREMENT — § 5 UWG; CASE LAW — *Moffatt v. Air Canada* (foreign, persuasive only, not binding EU/German law); LEGAL REQUIREMENT — EU AI Act
Reference: § 5 UWG (direct); 2024 BCCRT 149; Art. 43 (basis for the "not a certification" claim)
Discovery: Two of the three previously-flagged claims are unchanged, byte-for-byte, in `frontend/landing.html`: the Air Canada citation still lacks a "foreign, non-binding" qualifier, and the GDPR Art. 33 72-hour claim still omits its risk-based conditionality — both sit under a `<!-- REVIEW: Kwabena -->` marker, i.e. already flagged internally but not yet fixed. The third item ("no regulation requires testing a chatbot," previously stated as settled fact) no longer appears verbatim; the underlying risk is now managed through a real, if manually-enforced, `docs/legal/FORBIDDEN-WORDS.md` and `docs/legal/LEGAL-MAP.md` tracking claims as VERIFIED/UNDER REVIEW/UNSUPPORTED. This is genuine process improvement that has not yet been applied to the two claims its own tracking already marks as open.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 50%
Recommendation: Apply the qualifiers `LEGAL-MAP.md` already prescribes to the Air Canada and GDPR Art. 33 claims on `landing.html` directly — the tracking exists; the fix does not yet.

---

Control No.: FE-03
Control Name: User-Facing Security and Privacy
Control Explanation: Do the Impressum and privacy notice meet basic German statutory disclosure duties?
Regulation: LEGAL REQUIREMENT — German DDG; LEGAL REQUIREMENT — GDPR
Reference: § 5 DDG; Art. 13, 14 GDPR
Discovery: Both `frontend/impressum.html` and `frontend/datenschutz.html` remain explicit, self-labelled "TODO — not legally reviewed" placeholders with every field still a `{{TOKEN}}`. The only diff on either file since the previous baseline is a shared CSS-comment update (page count in a code comment); no legal content changed.
Status: NON-COMPLIANT
Compliance Percentage: 0%
Recommendation: Complete both pages with real registration data and legal sign-off before public launch.

---

Control No.: FE-04
Control Name: Output, Report and Claim Integrity
Control Explanation: Does the report/scan output accurately represent what actually happened — the grade, the scan's scope, and the authorization status of the test?
Regulation: LEGAL REQUIREMENT — § 5 UWG; BEST-PRACTICE — internal evidentiary-integrity policy
Reference: § 5 UWG; N/A (internal policy, no external reference number)
Discovery: Grade and attack-library-version display are confirmed accurate and consistent — `backend/scanner.py` returns the real `library_version`/`library_name`, and both `report.html` and `index.html` render it unmodified. `index.html` still has no equivalent of `report.html`'s confidence display (confirmed by a zero-match grep for `confidence` in `index.html`). The more serious defect: `frontend/report.html:823` prints, unconditionally on every report, "Testing was performed with the verified consent of the system's owner" with no code path gating it on any verification flag — and `backend/scanner.py`'s report dict has no `authorized`/`ownership_verified` field for it to check even if it tried. Ownership verification is real (`backend/ownership.py`) but only runs for `mode="api"` scans that are not on the (org-unscoped) waiver list (see BE-05); `mode="prompt"`/`"model"` scans — the common case — never touch that code path at all, and their reports still print the same unconditional consent sentence.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 40%
Recommendation: Make the consent statement conditional on a real per-scan verification flag threaded from `backend/scanner.py` into the report payload, and suppress it entirely for scan modes where no ownership question was ever asked. Bring `index.html`'s confidence display up to `report.html`'s standard.

---

Control No.: FE-05
Control Name: Accessibility, User Understanding and Human Interaction
Control Explanation: Can a non-technical user understand what the AI judge did, what confidence levels mean, and interact with results appropriately?
Regulation: BEST-PRACTICE — WCAG-aligned accessibility conventions; internal clarity policy
Reference: WCAG (general conventions, no specific success criterion independently verified); N/A (internal policy)
Discovery: Substantive, working ARIA is confirmed on the two interactive pages: `index.html` (29 aria-/role attributes, incl. a live-updating progress bar and log region) and `art50check.html` (17, incl. `aria-live="polite"` status). `report.html` explains the two-layer (deterministic vs. LLM-judge) method in plain language. Unchanged from the previous pass: three real backend capabilities — login/auth, DNS-based ownership verification, and API-key issuance/rotation — have zero corresponding frontend page, confirmed by a zero-match grep of all frontend files against each endpoint's path.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 70%
Recommendation: Prioritize a minimal UI for ownership verification and API key management — both currently require a customer to be told the raw endpoint paths.

---

## BACKEND / PLATFORM CONTROLS

Control No.: BE-01
Control Name: AI Component and Provider Governance
Control Explanation: Are the AI models/providers identified, and is their configuration consistent with a stated data-residency policy?
Regulation: LEGAL REQUIREMENT — GDPR (applicability not independently verified); INTERNAL POLICY — `PLAYBOOK.md`
Reference: Art. 44 et seq.; PLAYBOOK.md §1 (EU-only invariant, explicitly withdrawn 18.08)
Discovery: `backend/config.py` still defaults `PROVIDER` to a generic, operator-configured Azure OpenAI-compatible endpoint with no region enforcement; Mistral remains registered as an alternative; Anthropic remains fully absent from `requirements.txt`. No replacement residency policy has been documented since the prior withdrawal. New this pass: `PLAYBOOK.md` and `PROJECT-STATE.md` currently both assert "Mistral is still the only provider `backend/llm.py` registers" — this is factually wrong at the current commit (`llm.py` registers both `mistral` and `azure`, and `azure` is the default), a live drift between the documentation and the exact fact this control checks.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 50%
Recommendation: Document a current data-residency stance. Separately, correct the stale "Mistral only" claim in `PLAYBOOK.md`/`PROJECT-STATE.md` — it misstates which vendor actually governs production today.

---

Control No.: BE-02
Control Name: AI Attack Library Governance
Control Explanation: Is the attack library structured, validated, and unambiguous about which version ran?
Regulation: BEST-PRACTICE — OWASP Top 10 for LLM Applications
Reference: N/A (general framework reference, no specific numbered item cited)
Discovery: `attacks/attacks.yaml` (v2.0, 78 attacks) and `attacks/attacks_short.yaml` (v1.4, 21 attacks, the live default) both remain in use and both pass the same `backend/attacks.py:_validate()` logic (unique id, declared category, valid severity). No automated test exercises this validation — confirmed by a repo-wide search for any test referencing `attacks.py`. Disambiguating which library actually ran still requires checking two fields together.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 70%
Recommendation: Add a prominent "library used" indicator on the report, and a validation test for `_validate()`.

---

Control No.: BE-03
Control Name: AI Risk and Scoring Governance
Control Explanation: Is the scoring/grading formula sound, internally consistent, and correctly displayed?
Regulation: BEST-PRACTICE — internal scoring methodology
Reference: N/A (internal policy, no external reference number)
Discovery: The production path is verified correct: `backend/judge.py` now returns `disclosed_confidential`, `backend/scanner.py` escalates severity to `critical` when it's true, and `backend/scoring.py` caps the grade at B for any high-or-critical finding — together these are the fix the commit history describes (a bot that discloses protected values under a "high"-rated attack no longer scores A), and `frontend/report.html`'s live rendering and `scoring.explain()` text are in sync with it. However, `calibration/scoring_v2.py` — the file the previous assessment described as "confirmed, by direct comparison, to carry identical constants" — was actually diffed this pass and is **not** in sync: its grade-cap logic only checks `severity == "critical"`, with no "high" branch at all. Its own header calls itself the authority's stale twin if they ever disagree, which is an honest disclaimer, but the disagreement is exactly the one the most recent production fix introduced, and nothing tests for it. A stale pre-fix `scoring_explanation` string also remains in `report.html`'s demo/sample fixture (not shown on real reports).
Status: PARTIALLY COMPLIANT
Compliance Percentage: 80%
Recommendation: Update `calibration/scoring_v2.py`'s cap logic to match `backend/scoring.py`, or delete it if it can no longer be kept in sync by hand — a stale "reference" copy that silently reproduces a fixed production bug is worse than no reference copy. Add a test that fails if the two ever diverge again.

---

Control No.: BE-04
Control Name: AI Judge Validation and Calibration
Control Explanation: Has the AI judge's accuracy been measured against human judgment, with limitations disclosed?
Regulation: BEST-PRACTICE — ISO/IEC 42001
Reference: Structuring reference only, not certification
Discovery: `calibration/calibrate.py` still imports and replays the live `backend/judge.py`, and both calibration sets remain fully human-labelled (30/30, 43/43). The recorded results (29/29 stable agreement, deterministic layer 11/11 and 13/13, 95.3% mean agreement) are real and reproducible — but they are dated "measured 18.08" in `PROJECT-STATE.md`, and `backend/judge.py` received two further commits on 19.08: one a documented false-positive fix (an "instructions disclosed" check firing with no instructions to disclose), the other adding the `disclosed_confidential` field that now directly drives the BE-03 severity escalation. Neither change has a recorded post-fix calibration run, and `calibration/calibrate.py` has no mechanism at all — confirmed by a zero-match search — to validate `disclosed_confidential` against any human label, even though that field is now load-bearing for the worst grade a scan can receive.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 55%
Recommendation: Re-run calibration after every `judge.py` change that touches verdict or field-extraction logic, not on a fixed schedule. Add calibration coverage for `disclosed_confidential` specifically, since it now drives severity, not just a display field.

---

Control No.: BE-05
Control Name: Target Authorization and Active Testing Control
Control Explanation: Is an active scan against a live endpoint gated on verified ownership?
Regulation: INTERNAL POLICY — `PLAYBOOK.md`
Reference: Part II §4 (ownership-verification rule)
Discovery: `backend/ownership.py`, `backend/main.py`, and `backend/config.py` are byte-for-byte unchanged since the previous baseline. Real DNS-TXT verification (24-hour challenge window, 90-day re-verification) remains enforced ahead of `Target` construction in `POST /api/scan` for `mode="api"` scans. The `SCAN_UNVERIFIED_DOMAINS` waiver list remains org-unscoped (a flat set of domain strings, no organization binding) — the code's own comment names this explicitly as a gap — and remains empty by default.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 85%
Recommendation: Scope the waiver mechanism per-organization before it is ever populated in production.

---

Control No.: BE-06
Control Name: Authentication and Access Control
Control Explanation: Are login, session, role-based permission, and API-key mechanisms secure?
Regulation: LEGAL REQUIREMENT — GDPR (general); BEST-PRACTICE — OWASP Top 10
Reference: Art. 32; A01, A02, A07
Discovery: `backend/auth.py` and `backend/apikeys.py` are byte-for-byte unchanged since the previous baseline. Bcrypt hashing, a timing-safe dummy-hash comparison on the login-failure path, JWT with `token_version` revocation, and rank-based role checks that fail closed on an unrecognized role are all confirmed present and correct. API keys are SHA-256 hashed at rest with revocation checked on every use. Cross-tenant isolation remains untested (no test suite exercises it, in this pass or the last).
Status: COMPLIANT
Compliance Percentage: 100%
Recommendation: Perform explicit cross-tenant access testing before onboarding multiple real organizations — this is the one dimension neither pass has independently verified.

---

Control No.: BE-07
Control Name: Sensitive Data and Secret Protection
Control Explanation: Are credentials and secrets handled without hardcoding?
Regulation: LEGAL REQUIREMENT — GDPR (general)
Reference: Art. 32
Discovery: A broader pattern scan across every tracked file confirms the same, single hardcoded development database credential in three locations — `backend/config.py`'s `DATABASE_URL` default, `.env.example`, and `docker-compose.yml` — and no new secrets anywhere else. `SECRETS.md`'s own `password = "mypassword123"` line is an explicitly-labelled "BAD — NEVER DO THIS" documentation example, not a real credential. Passwords and API keys remain properly hashed at rest.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 70%
Recommendation: Remove the hardcoded default; require an explicit `DATABASE_URL` with no fallback.

---

Control No.: BE-08
Control Name: Application and Network Security
Control Explanation: Is SSRF protection applied to every outbound-request code path, and is rate limiting effective? Assessed by code path and enforcement, not by feature existence alone.
Regulation: BEST-PRACTICE — OWASP Top 10
Reference: A10 (SSRF), A04 (resource exhaustion)
Discovery: `backend/scanner.py`'s single outbound call to a customer-supplied URL (`httpx.AsyncClient.post(target.api_url, ...)`) still has zero references to `netguard`, `assert_public_host`, or `is_private_url` — confirmed by direct grep. The only SSRF-relevant check on this path is a single, one-time `is_private_url()` call in `backend/main.py` before the scan begins; because a scan then makes multiple independent outbound requests over several seconds, this is an admission-time check, not a per-request guard, and does not defend against DNS rebinding. This is the same, fully open gap the previous assessment named as its highest-priority finding. By contrast, `backend/art50engine.py` (the Art. 50 Check path, which absorbed the deleted `backend/art50check.py`) guards both the initial URL and, via a Playwright request interceptor, every subsequent request the loaded page makes — genuine defense-in-depth that `scanner.py` still lacks. Two mitigating facts, both independently confirmed: first, `PROJECT-STATE.md` already self-discloses this exact gap by name, with an assigned owner and an explicit condition ("fix before the password comes off"), which is the opposite of hiding it; second, the same document states the scan endpoint currently sits behind the site's Basic-Auth, so the gap is not reachable by an anonymous caller today, even though the code path itself remains unguarded. Rate limiting is unchanged and solid — per-IP, per-endpoint `slowapi` limits confirmed across ten decorated routes.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 45%
Recommendation: Apply `netguard`'s per-request guard to `backend/scanner.py`'s outbound call before Basic-Auth comes off the scan endpoint — the project's own tracked deadline for this. Self-disclosure and a temporary compensating control are credited in this score; they are not a substitute for the fix.

---

Control No.: BE-09
Control Name: Evidence, Traceability and Data Integrity
Control Explanation: Does a persisted scan record trace back to the scan, attack-library version, and tested content?
Regulation: LEGAL REQUIREMENT — GDPR (general); BEST-PRACTICE — internal traceability policy
Reference: Art. 32; N/A (internal policy)
Discovery: `backend/main.py` is unchanged since the previous baseline. The real `library_version` and the real submitted `system_prompt` continue to persist correctly. `Target.name` still falls back to the hardcoded literal `"Prompt-based target"` whenever `api_url` is empty — i.e. for every `mode="prompt"`/`"model"` scan, the common case. `backend/models.py` stores `system_prompt` (explicitly commented as a customer trade secret) as a plain `Text` column; no column-level or database-level at-rest encryption exists anywhere in the codebase or deployment configuration — this is not merely unverified, it is confirmed absent by direct inspection.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 70%
Recommendation: Persist the real target display name in the common scan mode. Given `system_prompt` is explicitly treated as a trade secret elsewhere in the project's own documentation, implement or explicitly scope-accept the absence of at-rest encryption for that column — silence on it is no longer a neutral option.

---

Control No.: BE-10
Control Name: Change, Dependency and Configuration Management
Control Explanation: Are changes reviewed, dependencies complete, and deployment configuration hardened?
Regulation: BEST-PRACTICE — standard change-management practice
Reference: N/A (general industry practice, no specific standard cited)
Discovery: Of the 24 commits since the previous baseline (`114ebc9..f301d3e`), zero were merged via a reviewed pull request (2 are local "merge remote-tracking branch" integration merges, not PR reviews) — down from the already-low 11% (19 of 168) measured in the prior period, and no `.github/` or other CI configuration exists to enforce review going forward. `requirements.txt` remains complete and unusually well-documented — every dependency's consumer and, in two cases, its specific CVE rationale, is named inline; cross-checked against every third-party import in `backend/` and `tools/`, nothing is missing. `docker-compose.prod.yml` still passes `--forwarded-allow-ips "*"`, trusting `X-Forwarded-For` from any source; this is a documented, reasoned risk-acceptance (the app service publishes no host port and is reachable only via the internal Docker network) rather than an unexamined default, but it remains a wildcard rather than a scoped trust boundary.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 20%
Recommendation: Require review for changes touching auth, ownership, SSRF, or scoring/judge logic — the exact categories that produced this period's bug-fix commits — even without full CI. Scope `--forwarded-allow-ips` to the Caddy container's address/CIDR rather than a wildcard.

---

Control No.: BE-11
Control Name: Regression Testing and Operational Monitoring
Control Explanation: Do automated tests, CI, and monitoring exist to catch regressions?
Regulation: BEST-PRACTICE — standard QA practice
Reference: N/A (general industry practice, no specific standard cited)
Discovery: No `test_*.py`/`*_test.py` exists anywhere under `backend/`, and no CI configuration exists anywhere in the repository (`.github/`, `.gitlab-ci.yml`, `Jenkinsfile`, and equivalents are all absent). `tools/art50v2/test_fixtures.py` and `tools/voice50/test_fixtures.py` are real, well-constructed fixture-based verification scripts — but both are manually invoked (`python tools/.../test_fixtures.py`), confirmed by a repo-wide search to be referenced in no CI config, `Makefile`, or `package.json` (none of which exist). No monitoring or alerting exists beyond `GET /api/health`, a liveness/config-introspection endpoint with no confirmed external consumer. This is the exact period in which real scoring and judge bugs were found and fixed by hand (BE-03, BE-04) — precisely the class of regression an automated suite exists to catch before it ships.
Status: PARTIALLY COMPLIANT
Compliance Percentage: 15%
Recommendation: Wire the two existing fixture scripts into a CI job as a first, low-cost step — they already exist and already work. Add unit coverage for `backend/scoring.py` and `backend/judge.py` specifically, given this period's history.

---

Control No.: BE-12
Control Name: Security and Governance Logging
Control Explanation: Are security events captured durably, and can administrative actions be reconstructed?
Regulation: LEGAL REQUIREMENT — GDPR (general); BEST-PRACTICE — OWASP Top 10
Reference: Art. 32, Art. 5(2); A09
Discovery: No file under `backend/` imports Python's `logging` module — confirmed across all fifteen backend modules, including the four that changed since the previous baseline (`judge.py`, `netguard.py`, `scanner.py`, `scoring.py`; none of the changes added logging). `backend/models.py` defines nine entities and none is an audit/security-event log. No login, ownership-verification, or API-key event is durably recorded anywhere outside the business-data tables themselves, which carry no actor/action/timestamp-of-action semantics.
Status: NON-COMPLIANT
Compliance Percentage: 0%
Recommendation: Introduce structured logging for auth, ownership-verification, and API-key events, and a dedicated append-only audit-log table.

---

## TOP 5 PRIORITY RECOMMENDATIONS

1. Apply `netguard`'s per-request SSRF guard to `backend/scanner.py` before Basic-Auth is removed from the scan endpoint — the project's own tracked deadline (BE-08).
2. Re-sync or retire `calibration/scoring_v2.py`, and re-run judge calibration after the two uncalibrated `judge.py` changes from 19.08 — both currently give false confidence that the scoring/judging pipeline is validated when a load-bearing part of it (`disclosed_confidential`) has never been checked against a human label (BE-03, BE-04).
3. Make the report's ownership-consent statement conditional on a real per-scan verification flag (FE-04).
4. Introduce structured logging and a dedicated audit-log entity (BE-12), and require review for auth/ownership/SSRF/scoring-touching changes given the 0% reviewed-PR rate this period (BE-10, BE-12).
5. Complete the Impressum and Datenschutz pages (FE-03).

---
*Governance V2 baseline: commit `f301d3e`, superseding the first V2 pass at `114ebc9`. Governance V1 (baseline `f48fdbf`) was removed from the working tree per an earlier team decision; its content remains recoverable via `git show 474b20e:governance/...`.*
