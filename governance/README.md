# PromptGuard Governance, Risk and Compliance Framework

## Overview

This directory contains the Governance, Risk and Compliance (GRC)
framework for PromptGuard.

The framework provides a structured and evidence-based approach for
assessing the current state of the PromptGuard repository and identifying
governance, security, AI risk, logging, traceability and compliance-related
improvements.

The framework covers:

- AI governance
- AI risk management
- Attack governance
- AI evaluation and validation
- Target authorization
- Sensitive data protection
- Change management
- Human oversight
- Evidence and traceability
- Regression and monitoring
- Security and application logging
- Governance audit logging
- Legal and claims governance

The purpose is to establish a measurable governance baseline and track
improvement as PromptGuard develops.

---

## Core Principles

### Evidence-Based

Every governance assessment should be supported by available evidence.

Evidence may include:

- source code
- configuration files
- tests
- test results
- documentation
- Git history
- logs
- runtime output
- official legal sources

### No Source, No Claim

Legal, regulatory, certification or compliance claims should not be made
without an appropriate supporting source.

Primary sources should be preferred.

### Technical Testing Is Not Legal Compliance

A successful technical test does not automatically establish that a system
is legally compliant.

PromptGuard may test technical controls and document the results, but legal
compliance depends on factors outside the scope of automated testing.

### Test Report, Not Certification

PromptGuard should describe its output as a technical assessment, test result,
evidence or report unless there is a valid basis for a certification claim.

### Record Uncertainty

Where evidence is insufficient, the correct result may be:

**UNCLEAR**

It is better to document uncertainty than to make unsupported conclusions.

---

# Governance Controls

The initial framework contains ten governance controls.

## GOV-01 — AI Component Inventory

Verify that relevant AI components can be identified.

Checks may include:

- AI models
- AI providers
- AI judges
- model configuration
- AI-related dependencies
- component purpose
- version information

Reference guidance:

- ISO/IEC 42001

---

## GOV-02 — Attack Governance

Verify that attack definitions are structured and traceable.

Checks may include:

- attack files exist
- attack identifiers exist
- attack categories exist
- attack descriptions exist
- duplicate attacks are identified
- attack tests can be executed

Reference guidance:

- ISO/IEC 42001
- ISO/IEC 23894

---

## GOV-03 — AI Risk and Scoring

Verify that findings and risks are assessed consistently.

Checks may include:

- risk scoring logic exists
- severity levels are defined
- scoring logic can be tested
- critical findings can be identified
- scoring documentation exists

Reference guidance:

- ISO/IEC 23894
- ISO 31000

---

## GOV-04 — AI Judge Validation

Verify that AI-based judging or evaluation can be identified and assessed.

Checks may include:

- judge implementation exists
- model or provider can be identified
- evaluation logic is documented
- tests exist where practical
- limitations can be documented

Reference guidance:

- ISO/IEC 42001

---

## GOV-05 — Target Authorization

Verify whether controls exist to prevent unauthorized targets from being tested.

Checks may include:

- target validation
- allow lists
- authorization mechanisms
- rejection of invalid targets
- tests for target restrictions

Reference guidance:

- ISO/IEC 42001
- ISO/IEC 27001

---

## GOV-06 — Sensitive Data Protection

Verify that the repository does not contain obvious exposed secrets.

Checks may include:

- API keys
- passwords
- access tokens
- private keys
- environment files
- sensitive data handling
- secret scanning

Reference guidance:

- ISO/IEC 27001

---

## GOV-07 — Change Management

Verify that significant changes can be traced.

Checks may include:

- Git repository exists
- branch information
- commit history
- change review process
- documentation of significant changes

Reference guidance:

- ISO/IEC 42001
- ISO/IEC 27001

---

## GOV-08 — Human Oversight

Assess whether significant findings or uncertain decisions can receive human review.

Checks may include:

- escalation mechanisms
- manual review
- critical finding review
- low-confidence decision review
- documented responsibility

Reference guidance:

- ISO/IEC 42001

---

## GOV-09 — Evidence and Traceability

Verify whether important findings can be traced.

Checks may include:

- scan identifiers
- attack identifiers
- target identifiers
- timestamps
- result records
- version information
- supporting evidence

Reference guidance:

- ISO/IEC 42001
- ISO/IEC 27001

---

## GOV-10 — Regression and Monitoring

Verify whether changes can be tested for unintended regressions.

Checks may include:

- automated tests
- test directories
- regression testing
- continuous integration
- repeatable test execution

Reference guidance:

- ISO/IEC 42001
- ISO/IEC 23894

---

# Logging Controls

## LOG-01 — Security and Application Logging

Verify whether significant application and security events are logged.

Checks may include:

- application logging
- errors
- security failures
- scan failures
- timestamps
- severity levels

Reference guidance:

- ISO/IEC 27001

---

## LOG-02 — Governance Audit Logging

Verify whether governance-relevant activities can be traced.

Checks may include:

- scan start
- scan completion
- authorization decisions
- critical findings
- governance failures
- configuration changes
- review decisions

Reference guidance:

- ISO/IEC 42001

---

# Assessment Status

Each control receives one of the following results:

- PASS — implemented and evidence is available
- PARTIAL — partly implemented or evidence is incomplete
- FAIL — missing or insufficient
- N/A — not applicable
- UNCLEAR — insufficient evidence to make a reliable decision

---

# Assessment Process

```text
DEFINE CONTROL
      ↓
INSPECT REPOSITORY
      ↓
RUN AUTOMATED CHECKS
      ↓
COLLECT EVIDENCE
      ↓
MANUAL REVIEW WHERE REQUIRED
      ↓
PASS / PARTIAL / FAIL / N/A / UNCLEAR
      ↓
DOCUMENT FINDING
      ↓
RECOMMEND IMPROVEMENT
      ↓
RE-ASSESS
```

---

# Legal and Claims Governance

PromptGuard's product is itself a legal/compliance-adjacent claim (a
"Prüfbericht" documenting that a chatbot was tested). That means the
governance framework must also govern what PromptGuard is allowed to *say*
about itself and its results, not only what it technically does.

This is implemented in `docs/legal/`:

| File | Purpose |
|---|---|
| `docs/legal/LEGAL-MAP.md` | Every legal source relevant to the product, split into: requirement, applicability, technical testability, what PromptGuard actually tests, and what PromptGuard may claim — each with a status of `VERIFIED`, `UNDER REVIEW`, `UNCLEAR`, or `NOT APPLICABLE`. |
| `docs/legal/HOOKS.md` | Marketing/compliance hooks, each with citation and status. Hooks without a citation are marked as not drafted rather than invented. |
| `docs/legal/DISCLAIMERS.md` | Required disclaimer wording and where it must appear. |
| `docs/legal/FORBIDDEN-WORDS.md` | Controlled wording list (`zertifiziert`, `certified`, `garantiert`, `guaranteed`, etc.) that requires evidence and sign-off before use. |

## Distinction: testing vs. compliance vs. certification

This distinction is load-bearing for the whole framework and for the product
itself:

- **Testing** — PromptGuard runs documented attack patterns against a
  chatbot and records PASS/FAIL/ERROR per attack, with evidence. This is the
  only thing PromptGuard actually does.
- **Compliance** — a legal determination that a system meets a specific
  statute's requirements. PromptGuard's technical PASS does **not**
  establish this. See `docs/legal/LEGAL-MAP.md`, "Technical Testing Is Not
  Legal Compliance."
- **Certification** — issuance of a conformity certificate by an accredited,
  officially notified body, and only for high-risk AI systems (AI Act Art.
  29, 43). PromptGuard is not a notified body, does not issue certificates,
  and this framework's own control implementation must never be described as
  ISO/IEC certification — the standards referenced in
  `governance/controls/controls.yaml` are structuring references, not
  certification claims.

A governance control marked `PASS` in this framework means: *evidence was
found in the repository that the described technical or process control
exists and functions.* It does not mean the product is legally compliant,
and it does not mean PromptGuard holds any certification.

---

# Running the Framework

## How to run the governance checker

From the repository root:

```bash
python governance/scripts/run_governance.py
```

This inspects the repository (read-only), runs safe checks against actual
source files, attempts to execute any existing automated tests it can find,
and writes the result to `governance/reports/GOVERNANCE_REPORT.md`. It does
not modify production code, does not require network access, and does not
require a working `PROVIDER=anthropic` API key. If optional dependencies
(e.g. PyYAML) are not installed in the environment running the script, it
degrades to text-based inspection rather than failing.

## How to run the governance tests

```bash
python -m unittest governance/tests/test_governance.py -v
```

Or, if `pytest` is available in the environment:

```bash
pytest governance/tests/test_governance.py -v
```

The tests use only the Python standard library, so they run without
installing project dependencies. They verify the governance directory
structure, that `controls.yaml` defines all 12 controls, that the governance
script runs and produces a report, and that the required legal documentation
exists.

## Continuous improvement

This framework is a baseline, not a finished state. As PromptGuard's code
changes:

- Re-run `governance/scripts/run_governance.py` after any change to
  `backend/`, `attacks/`, or authorization/logging logic, and compare the new
  report against the previous one in `governance/reports/`.
- Treat every `FAIL` or `PARTIAL` result as a backlog item, not a permanent
  state — `governance/reports/GOVERNANCE_REPORT.md` lists concrete
  recommendations per control.
- Update `governance/controls/controls.yaml` when a control's automated or
  manual checks change, so the checker and its documentation do not drift
  apart.
- Update `docs/legal/LEGAL-MAP.md` whenever a claim moves from `UNDER REVIEW`
  or `UNCLEAR` to a primary-sourced `VERIFIED` status, or the reverse.
- This framework does not self-certify its own completeness. A human
  reviewer should periodically re-read `governance/reports/GOVERNANCE_REPORT.md`
  against the live repository, not just trust the last automated run.