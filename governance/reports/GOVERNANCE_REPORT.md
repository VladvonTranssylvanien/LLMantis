# PromptGuard Governance Report

- **Assessment date:** 2026-08-15 20:03 UTC
- **Repository commit:** `f48fdbf` (`f48fdbfb8216b1ed5822c9b6d196d81fb4294809`)
- **Branch:** `feature/governance-framework`
- **Repository scope:** entire PromptGuard/LLMantis repository at the commit above — `backend/`, `attacks/`, `frontend/`, `tools/`, `docs/`, configuration files, and git history.
- **Assessment methodology:** automated, read-only inspection of source files, configuration, git history and documentation by `governance/scripts/run_governance.py`, cross-checked manually against `governance/controls/controls.yaml`. Every status below is backed by evidence quoted or referenced inline — no status is inferred from a keyword match alone. This report supersedes no human legal or security review; see `docs/legal/DISCLAIMERS.md`.

This report describes the technical state of controls in this repository. It is **not** a certification and does not establish legal compliance with any statute or standard referenced below. See `governance/README.md`, "Legal and Claims Governance".

Some controls below also list supplementary screenshot evidence stored under `governance/evidence/<control-id>/`. Screenshots are illustrative only — they never replace the repository paths, automated check results, or other verifiable evidence cited for a control, and no screenshot in this repository may contain an API key, token, password, or other sensitive or personal data.

## Summary

PASS: 1 · PARTIAL: 10 · FAIL: 1 · N/A: 0 · UNCLEAR: 0 · Total controls: 12

| ID | Control | Reference | Status | Evidence | Gap |
|----|---------|-----------|--------|----------|-----|
| GOV-01 | AI Component Inventory | ISO/IEC 42001 | **PARTIAL** | backend/config.py: TARGET_MODEL default = 'claude-sonnet-4-5', JUDGE_MODEL default = 'claude-sonnet-4-5'<br>backend/llm.py: provider registry declares ['mock', 'anthropic']<br>requirements.txt: anthropic pinned at ==0.42.0 | PLAYBOOK.md's EU-only-stack invariant forbids Anthropic/OpenAI/Google as the judge provider, but backend/config.py's JUDGE_MODEL default ('claude-sonnet-4-5') is an Anthropic model. Tracked as technical debt #1 in PROJECT-STATE.md. |
| GOV-02 | Attack Governance | ISO/IEC 42001, ISO/IEC 23894 | **PARTIAL** | attacks/attacks.yaml: 21 attack(s) declared, 5 categor(y/ies) declared<br>no duplicate attack ids found by static scan<br>backend/attacks.py:_validate() enforces unique id, declared category, valid severity at load time<br>README.md's stated attack count (21) matches attacks.yaml (21) | no automated test exercises attacks.yaml validation (no test_*.py found outside governance/) |
| GOV-03 | AI Risk and Scoring | ISO/IEC 23894, ISO 31000 | **PARTIAL** | backend/scoring.py: SEVERITY_WEIGHT defines all four severities<br>backend/scoring.py: critical-failure grade cap = 'C'<br>README.md's documented cap ('C') matches the implementation<br>PROJECT-STATE.md records prior scoring/README drift as tracked technical debt (#7) | no automated test exists for backend/scoring.py's compute()/grade logic |
| GOV-04 | AI Judge Validation | ISO/IEC 42001 | **PARTIAL** | backend/judge.py: deterministic_check() decides FAIL by string/canary match, independent of the AI judge<br>backend/judge.py: verdicts are tagged with confidence in {confirmed, likely, possible}<br>backend/judge.py:_extract_json falls back to an ERROR verdict on unparsable judge output, instead of raising | no judge calibration set exists and judge/human agreement has not been measured (README.md 'Status' table and PROJECT-STATE.md §7 both record this as not done) |
| GOV-05 | Target Authorization | ISO/IEC 42001, ISO/IEC 27001 | **PARTIAL** | backend/models.py: OwnershipVerification entity exists (domain, method, status, verified_at)<br>PLAYBOOK.md documents a policy requirement: active red-team testing requires verified ownership, no exceptions | POST /api/scan in backend/main.py does not check OwnershipVerification (or any authorization state) before executing an 'api'-mode (active) scan against a target |
| GOV-06 | Sensitive Data Protection | ISO/IEC 27001 | **PASS** | .gitignore excludes .env<br>.gitignore excludes customer scan output (results/, scans/, *.scan.json)<br>no .env file is tracked by git<br>pattern-based secret scan across 53 tracked file(s) found no matches<br>backend/config.py:summary() reports key presence ('set'/'not set') without printing the value | — |
| GOV-07 | Change Management | ISO/IEC 42001, ISO/IEC 27001 | **PARTIAL** | git log: 26 commit(s) inspected, 6 are 'Merge pull request' commits<br>git branch -a: 10 branch ref(s) found | no CONTRIBUTING.md documenting the change/review process<br>branch protection / required-review settings cannot be confirmed from a local clone (hosting-platform setting) |
| GOV-08 | Human Oversight | ISO/IEC 42001 | **PARTIAL** | backend/judge.py tags every verdict with a confidence level, which a review policy could key off<br>PLAYBOOK.md documents an external review cycle and per-role responsibility for legal wording and design decisions | README.md states 'possible' confidence findings are omitted from reports, but frontend/report.html was not found to enforce this filter — it displays the confidence value without excluding low-confidence rows<br>no in-product mechanism found for escalating a specific disputed or low-confidence finding for manual override |
| GOV-09 | Evidence and Traceability | ISO/IEC 42001, ISO/IEC 27001 | **PARTIAL** | backend/scanner.py: every scan is assigned a scan_id<br>backend/scanner.py: each result carries ['attack_id', 'category', 'severity', 'evidence', 'method', 'duration_ms']<br>backend/models.py: Scan and Result are persisted with created_at timestamps and a foreign-key chain to Target/Organization | no attack-library or model-version field is persisted per Scan row (PROJECT-STATE.md records report.attack_library_version as a requested, unimplemented field) |
| GOV-10 | Regression and Monitoring | ISO/IEC 42001, ISO/IEC 23894 | **FAIL** | PLAYBOOK.md documents a mutation-testing rule ('break the judge deliberately, see what fails') as project method | no automated test file was found anywhere in the repository outside governance/ for the scanning/judging/scoring engine<br>no .github/workflows CI configuration found<br>no evidence found in the repository that this mutation check has actually been performed and recorded |
| LOG-01 | Security and Application Logging | ISO/IEC 27001 | **PARTIAL** | backend/scanner.py:_run_one captures target/judge exceptions in-band as an ERROR verdict (not silently dropped) | no backend/*.py file imports Python's logging module or an equivalent structured logger |
| LOG-02 | Governance Audit Logging | ISO/IEC 42001 | **PARTIAL** | backend/models.py: Scan/Result rows persist scan lifecycle outcomes with timestamps<br>POST /api/scan emits start/result/complete/error events over NDJSON, but only to the requesting browser, not to a durable store | no dedicated audit-log entity exists in backend/models.py<br>PLAYBOOK.md's data-model sketch (Part II §4) lists an AuditLog[] entity that has not been implemented<br>NDJSON stream events (scan started/completed/failed) are not persisted anywhere; they exist only for the lifetime of the HTTP response |

## Control Detail

### GOV-01 — AI Component Inventory

**Status:** PARTIAL  
**Reference standard(s):** ISO/IEC 42001

**Evidence:**
- backend/config.py: TARGET_MODEL default = 'claude-sonnet-4-5', JUDGE_MODEL default = 'claude-sonnet-4-5'
- backend/llm.py: provider registry declares ['mock', 'anthropic']
- requirements.txt: anthropic pinned at ==0.42.0

**Identified gap(s):**
- PLAYBOOK.md's EU-only-stack invariant forbids Anthropic/OpenAI/Google as the judge provider, but backend/config.py's JUDGE_MODEL default ('claude-sonnet-4-5') is an Anthropic model. Tracked as technical debt #1 in PROJECT-STATE.md.

**Notes:**
- Inventory is identifiable and version-pinned; the open gap is a policy/configuration mismatch already tracked by the project itself, not a missing inventory.

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- `governance/evidence/GOV-01/api-health-model-config.jpg`
- see [`governance/evidence/GOV-01/EVIDENCE.md`](governance/evidence/GOV-01/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

### GOV-02 — Attack Governance

**Status:** PARTIAL  
**Reference standard(s):** ISO/IEC 42001, ISO/IEC 23894

**Evidence:**
- attacks/attacks.yaml: 21 attack(s) declared, 5 categor(y/ies) declared
- no duplicate attack ids found by static scan
- backend/attacks.py:_validate() enforces unique id, declared category, valid severity at load time
- README.md's stated attack count (21) matches attacks.yaml (21)

**Identified gap(s):**
- no automated test exercises attacks.yaml validation (no test_*.py found outside governance/)

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- `governance/evidence/GOV-02/api-attacks-library.jpg`
- see [`governance/evidence/GOV-02/EVIDENCE.md`](governance/evidence/GOV-02/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

### GOV-03 — AI Risk and Scoring

**Status:** PARTIAL  
**Reference standard(s):** ISO/IEC 23894, ISO 31000

**Evidence:**
- backend/scoring.py: SEVERITY_WEIGHT defines all four severities
- backend/scoring.py: critical-failure grade cap = 'C'
- README.md's documented cap ('C') matches the implementation
- PROJECT-STATE.md records prior scoring/README drift as tracked technical debt (#7)

**Identified gap(s):**
- no automated test exists for backend/scoring.py's compute()/grade logic

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- `governance/evidence/GOV-03/scan-grade-score-critical-cap.jpg`
- see [`governance/evidence/GOV-03/EVIDENCE.md`](governance/evidence/GOV-03/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

### GOV-04 — AI Judge Validation

**Status:** PARTIAL  
**Reference standard(s):** ISO/IEC 42001

**Evidence:**
- backend/judge.py: deterministic_check() decides FAIL by string/canary match, independent of the AI judge
- backend/judge.py: verdicts are tagged with confidence in {confirmed, likely, possible}
- backend/judge.py:_extract_json falls back to an ERROR verdict on unparsable judge output, instead of raising

**Identified gap(s):**
- no judge calibration set exists and judge/human agreement has not been measured (README.md 'Status' table and PROJECT-STATE.md §7 both record this as not done)

**Notes:**
- Per governance policy, existence of a judge implementation alone is never sufficient for PASS. This status reflects structural safeguards (deterministic layer, confidence tiering, malformed-output fallback) against the explicit lack of calibration evidence.

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- `governance/evidence/GOV-04/scan-finding-detail-deterministic-evidence.jpg`
- see [`governance/evidence/GOV-04/EVIDENCE.md`](governance/evidence/GOV-04/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

### GOV-05 — Target Authorization

**Status:** PARTIAL  
**Reference standard(s):** ISO/IEC 42001, ISO/IEC 27001

**Evidence:**
- backend/models.py: OwnershipVerification entity exists (domain, method, status, verified_at)
- PLAYBOOK.md documents a policy requirement: active red-team testing requires verified ownership, no exceptions

**Identified gap(s):**
- POST /api/scan in backend/main.py does not check OwnershipVerification (or any authorization state) before executing an 'api'-mode (active) scan against a target

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- `governance/evidence/GOV-05/scan-form-no-ownership-check.jpg`
- see [`governance/evidence/GOV-05/EVIDENCE.md`](governance/evidence/GOV-05/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

### GOV-06 — Sensitive Data Protection

**Status:** PASS  
**Reference standard(s):** ISO/IEC 27001

**Evidence:**
- .gitignore excludes .env
- .gitignore excludes customer scan output (results/, scans/, *.scan.json)
- no .env file is tracked by git
- pattern-based secret scan across 53 tracked file(s) found no matches
- backend/config.py:summary() reports key presence ('set'/'not set') without printing the value

**Identified gap(s):**
- none identified by this automated pass

**Notes:**
- Pattern-based scanning is a lower bound, not a guarantee — see governance/controls/controls.yaml.

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- `governance/evidence/GOV-06/api-health-key-redacted.jpg`
- see [`governance/evidence/GOV-06/EVIDENCE.md`](governance/evidence/GOV-06/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

### GOV-07 — Change Management

**Status:** PARTIAL  
**Reference standard(s):** ISO/IEC 42001, ISO/IEC 27001

**Evidence:**
- git log: 26 commit(s) inspected, 6 are 'Merge pull request' commits
- git branch -a: 10 branch ref(s) found

**Identified gap(s):**
- no CONTRIBUTING.md documenting the change/review process
- branch protection / required-review settings cannot be confirmed from a local clone (hosting-platform setting)

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- none currently captured
- see [`governance/evidence/GOV-07/EVIDENCE.md`](governance/evidence/GOV-07/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

### GOV-08 — Human Oversight

**Status:** PARTIAL  
**Reference standard(s):** ISO/IEC 42001

**Evidence:**
- backend/judge.py tags every verdict with a confidence level, which a review policy could key off
- PLAYBOOK.md documents an external review cycle and per-role responsibility for legal wording and design decisions

**Identified gap(s):**
- README.md states 'possible' confidence findings are omitted from reports, but frontend/report.html was not found to enforce this filter — it displays the confidence value without excluding low-confidence rows
- no in-product mechanism found for escalating a specific disputed or low-confidence finding for manual override

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- `governance/evidence/GOV-08/report-view-no-confidence-filter.jpg`
- see [`governance/evidence/GOV-08/EVIDENCE.md`](governance/evidence/GOV-08/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

### GOV-09 — Evidence and Traceability

**Status:** PARTIAL  
**Reference standard(s):** ISO/IEC 42001, ISO/IEC 27001

**Evidence:**
- backend/scanner.py: every scan is assigned a scan_id
- backend/scanner.py: each result carries ['attack_id', 'category', 'severity', 'evidence', 'method', 'duration_ms']
- backend/models.py: Scan and Result are persisted with created_at timestamps and a foreign-key chain to Target/Organization

**Identified gap(s):**
- no attack-library or model-version field is persisted per Scan row (PROJECT-STATE.md records report.attack_library_version as a requested, unimplemented field)

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- `governance/evidence/GOV-09/scan-finding-attack-id-evidence-fix.jpg`
- see [`governance/evidence/GOV-09/EVIDENCE.md`](governance/evidence/GOV-09/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

### GOV-10 — Regression and Monitoring

**Status:** FAIL  
**Reference standard(s):** ISO/IEC 42001, ISO/IEC 23894

**Evidence:**
- PLAYBOOK.md documents a mutation-testing rule ('break the judge deliberately, see what fails') as project method

**Identified gap(s):**
- no automated test file was found anywhere in the repository outside governance/ for the scanning/judging/scoring engine
- no .github/workflows CI configuration found
- no evidence found in the repository that this mutation check has actually been performed and recorded

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- none currently captured
- see [`governance/evidence/GOV-10/EVIDENCE.md`](governance/evidence/GOV-10/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

### LOG-01 — Security and Application Logging

**Status:** PARTIAL  
**Reference standard(s):** ISO/IEC 27001

**Evidence:**
- backend/scanner.py:_run_one captures target/judge exceptions in-band as an ERROR verdict (not silently dropped)

**Identified gap(s):**
- no backend/*.py file imports Python's logging module or an equivalent structured logger

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- none currently captured
- see [`governance/evidence/LOG-01/EVIDENCE.md`](governance/evidence/LOG-01/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

### LOG-02 — Governance Audit Logging

**Status:** PARTIAL  
**Reference standard(s):** ISO/IEC 42001

**Evidence:**
- backend/models.py: Scan/Result rows persist scan lifecycle outcomes with timestamps
- POST /api/scan emits start/result/complete/error events over NDJSON, but only to the requesting browser, not to a durable store

**Identified gap(s):**
- no dedicated audit-log entity exists in backend/models.py
- PLAYBOOK.md's data-model sketch (Part II §4) lists an AuditLog[] entity that has not been implemented
- NDJSON stream events (scan started/completed/failed) are not persisted anywhere; they exist only for the lifetime of the HTTP response

**Supplementary screenshot evidence** (does not replace the repository/automated evidence above):
- none currently captured
- see [`governance/evidence/LOG-02/EVIDENCE.md`](governance/evidence/LOG-02/EVIDENCE.md) for what this evidence shows or, if absent, exactly what to capture and where to store it

## Limitations of this assessment

- This is a static, text/pattern-based inspection. It cannot observe runtime behaviour (e.g. whether `PROVIDER=anthropic` mode has ever actually been exercised — see README.md's own 'Tested against a real model: never run outside mock mode' entry).
- Secret scanning (GOV-06) is pattern-based and is a lower bound, not a guarantee that no sensitive value is committed.
- Change-management review enforcement (GOV-07) and branch protection cannot be confirmed from a local clone; they are GitHub-hosted settings outside this repository's file contents.
- Legal claims are assessed only for internal consistency against this repository's own research notes (`docs/KWABENA-GRC-BRIEF.md`, `PROJECT-STATE.md`) — this script performs no new legal research. See `docs/legal/LEGAL-MAP.md`.

## Recommendations

- **GOV-01:** PLAYBOOK.md's EU-only-stack invariant forbids Anthropic/OpenAI/Google as the judge provider, but backend/config.py's JUDGE_MODEL default ('claude-sonnet-4-5') is an Anthropic model. Tracked as technical debt #1 in PROJECT-STATE.md.
- **GOV-02:** no automated test exercises attacks.yaml validation (no test_*.py found outside governance/)
- **GOV-03:** no automated test exists for backend/scoring.py's compute()/grade logic
- **GOV-04:** no judge calibration set exists and judge/human agreement has not been measured (README.md 'Status' table and PROJECT-STATE.md §7 both record this as not done)
- **GOV-05:** POST /api/scan in backend/main.py does not check OwnershipVerification (or any authorization state) before executing an 'api'-mode (active) scan against a target
- **GOV-07:** no CONTRIBUTING.md documenting the change/review process
- **GOV-07:** branch protection / required-review settings cannot be confirmed from a local clone (hosting-platform setting)
- **GOV-08:** README.md states 'possible' confidence findings are omitted from reports, but frontend/report.html was not found to enforce this filter — it displays the confidence value without excluding low-confidence rows
- **GOV-08:** no in-product mechanism found for escalating a specific disputed or low-confidence finding for manual override
- **GOV-09:** no attack-library or model-version field is persisted per Scan row (PROJECT-STATE.md records report.attack_library_version as a requested, unimplemented field)
- **GOV-10:** no automated test file was found anywhere in the repository outside governance/ for the scanning/judging/scoring engine
- **GOV-10:** no .github/workflows CI configuration found
- **GOV-10:** no evidence found in the repository that this mutation check has actually been performed and recorded
- **LOG-01:** no backend/*.py file imports Python's logging module or an equivalent structured logger
- **LOG-02:** no dedicated audit-log entity exists in backend/models.py
- **LOG-02:** PLAYBOOK.md's data-model sketch (Part II §4) lists an AuditLog[] entity that has not been implemented
- **LOG-02:** NDJSON stream events (scan started/completed/failed) are not persisted anywhere; they exist only for the lifetime of the HTTP response

## Manual review requirements

The following cannot be settled by automated inspection and require a human reviewer:
- GOV-04: whether the AI judge's actual accuracy (once a calibration set exists) is acceptable for customer-facing use.
- GOV-05: whether the product's active-scan feature should ship at all before ownership verification is enforced in code.
- GOV-07: GitHub branch protection and required-review settings for `main`.
- Legal/claims governance: every `UNDER REVIEW` and `UNCLEAR` row in `docs/legal/LEGAL-MAP.md` requires a primary-source legal citation before any related claim is published.

---
*Generated by `governance/scripts/run_governance.py` — 2026-08-15 20:03 UTC.*
