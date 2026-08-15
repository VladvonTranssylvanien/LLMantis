# PromptGuard Governance Implementation Task

## Objective

Implement an independent Governance, Risk and Compliance framework inside this PromptGuard repository.

Do not modify or delete the existing root README.md unless a small link to the governance documentation is specifically required.

Do not commit or push any changes.

---

## Required Structure

Ensure the following structure exists:

governance/
├── README.md
├── controls/
│   └── controls.yaml
├── evidence/
│   └── .gitkeep
├── reports/
│   └── GOVERNANCE_REPORT.md
├── scripts/
│   └── run_governance.py
└── tests/
    └── test_governance.py

Also ensure the following structure exists:

docs/
└── legal/
    ├── LEGAL-MAP.md
    ├── HOOKS.md
    ├── DISCLAIMERS.md
    └── FORBIDDEN-WORDS.md

---

## Step 1 — Inspect the Repository First

Before implementing any governance checks:

1. Read PLAYBOOK.md first.
2. Read the root README.md.
3. Inspect PROJECT-STATE.md.
4. Inspect SETUP.md.
5. Inspect the repository structure.
6. Inspect backend/.
7. Inspect frontend/.
8. Inspect attacks/.
9. Inspect tools/.
10. Inspect docs/.
11. Inspect configuration files.
12. Inspect test directories.
13. Inspect CI/CD configuration.

Identify how PromptGuard is actually built, including:

- Programming languages
- Frameworks
- AI providers
- LLM models
- AI judges or evaluators
- Attack definitions
- Risk and scoring mechanisms
- Target validation
- Logging mechanisms
- Test frameworks
- CI/CD configuration
- Secret handling
- Data storage
- Existing security controls

Do not assume that a governance control exists simply because a keyword appears in the repository.

Inspect the actual implementation.

---

## Step 2 — Implement the 10 Governance Controls

### GOV-01 — AI Component Inventory

Inspect and identify:

- AI models
- AI providers
- LLM components
- AI judges
- Relevant AI configuration
- Version information where available

Reference standards:

- ISO/IEC 42001

Expected evidence:

- Source files
- Configuration
- Dependency definitions
- Documentation

---

### GOV-02 — Attack Governance

Inspect:

- The attacks/ directory
- Attack definitions
- Attack IDs
- Attack categories
- Duplicate attacks
- Attack structure
- Attack traceability
- Attack execution mechanisms

Reference standards:

- ISO/IEC 42001
- ISO/IEC 23894

Expected evidence:

- Attack files
- Attack metadata
- Attack IDs
- Test results

---

### GOV-03 — AI Risk and Scoring

Inspect:

- Risk scoring logic
- Severity definitions
- Finding classifications
- Critical severity handling
- Scoring consistency
- Scoring tests

Reference standards:

- ISO/IEC 23894
- ISO 31000

Expected evidence:

- Scoring implementation
- Severity definitions
- Tests
- Documentation

---

### GOV-04 — AI Judge Validation

Inspect:

- AI judge implementation
- Evaluation logic
- Model and provider configuration
- Validation tests
- Confidence handling
- Fallback handling
- Known limitations

Reference standards:

- ISO/IEC 42001

Do not mark this control PASS simply because an AI judge exists.

A PASS requires evidence that the evaluation approach has meaningful validation.

---

### GOV-05 — Target Authorization

Inspect whether the system prevents testing of unauthorized targets.

Check:

- Target validation
- Authorization mechanisms
- Allowlists
- Restrictions
- Invalid target rejection
- Tests for authorization controls

Reference standards:

- ISO/IEC 42001
- ISO/IEC 27001

---

### GOV-06 — Sensitive Data Protection

Check for:

- Exposed API keys
- Passwords
- Access tokens
- Private keys
- Secrets
- Committed environment files
- Unsafe logging of sensitive information

Do not expose secret values in governance reports.

Reference standards:

- ISO/IEC 27001

---

### GOV-07 — Change Management

Inspect:

- Git repository
- Branch structure
- Commit history
- Contribution process
- Pull request or review configuration
- Change documentation

Reference standards:

- ISO/IEC 42001
- ISO/IEC 27001

---

### GOV-08 — Human Oversight

Inspect whether:

- Critical findings can receive human review
- Uncertain findings can be escalated
- Humans can override or review important decisions
- Responsibilities are documented
- Manual approval mechanisms exist

Reference standards:

- ISO/IEC 42001

---

### GOV-09 — Evidence and Traceability

Inspect whether findings can be connected to:

- Scan ID
- Attack ID
- Target
- Timestamp
- Result
- Model or version where applicable
- Supporting evidence

Reference standards:

- ISO/IEC 42001
- ISO/IEC 27001

---

### GOV-10 — Regression and Monitoring

Inspect:

- Automated tests
- Regression tests
- Test frameworks
- CI/CD
- Repeatable test execution
- Monitoring mechanisms where applicable

Reference standards:

- ISO/IEC 42001
- ISO/IEC 23894

---

## Step 3 — Implement the 2 Logging Controls

### LOG-01 — Security and Application Logging

Inspect:

- Application logging
- Error logging
- Security-relevant events
- Severity levels
- Timestamps
- Logging configuration

Also identify whether sensitive information could be exposed in logs.

Reference standards:

- ISO/IEC 27001

---

### LOG-02 — Governance Audit Logging

Inspect whether governance-relevant events can be traced.

Examples include:

- Scan started
- Scan completed
- Scan failed
- Target authorization decision
- Critical finding
- Configuration change
- Review or approval decision

Reference standards:

- ISO/IEC 42001

---

## Step 4 — Assessment Rules

Each control must receive one of the following statuses:

- PASS
- PARTIAL
- FAIL
- N/A
- UNCLEAR

Definitions:

PASS:
The control is implemented and sufficient evidence exists.

PARTIAL:
Some implementation or evidence exists, but there are gaps.

FAIL:
The control is missing or materially insufficient.

N/A:
The control is not applicable to the current repository scope.

UNCLEAR:
The available evidence is insufficient to make a reliable assessment.

Do not inflate results.

Do not mark PASS based only on keyword searches.

Every result must reference actual evidence from the repository.

---

## Step 5 — Implement Automated Governance Checks

Create:

governance/scripts/run_governance.py

The script should:

1. Identify the repository root.
2. Inspect the actual repository structure.
3. Run safe repository-level checks.
4. Inspect relevant source files.
5. Detect implementation of governance controls.
6. Run appropriate existing tests where safe.
7. Avoid modifying production code.
8. Avoid exposing secrets.
9. Generate a governance assessment.
10. Write the result to:

governance/reports/GOVERNANCE_REPORT.md

The assessment must be executable using:

python governance/scripts/run_governance.py

Use repository-native dependencies where possible.

Do not introduce unnecessary dependencies.

---

## Step 6 — Implement Governance Tests

Create:

governance/tests/test_governance.py

The tests should verify:

- Governance directory structure
- Control definition availability
- Governance script functionality
- Required governance documentation
- Required legal documentation

Where practical, test the governance checker using repository-safe and non-destructive checks.

Run the relevant tests.

---

## Step 7 — Control Definitions

Create:

governance/controls/controls.yaml

For each of the 12 controls include:

- Control ID
- Control name
- Description
- Reference standard
- Automated checks
- Manual checks
- Expected evidence
- Assessment criteria

The standards are governance references.

Do not claim that implementation of these controls equals ISO certification.

---

## Step 8 — Legal and Claims Governance

Create:

docs/legal/LEGAL-MAP.md

docs/legal/HOOKS.md

docs/legal/DISCLAIMERS.md

docs/legal/FORBIDDEN-WORDS.md

Important rules:

Do not invent legal claims.

Do not state that chatbot testing is legally mandatory unless a verified primary legal source explicitly supports that exact claim.

Separate:

1. Legal requirement.
2. Applicability.
3. Technical testability.
4. What PromptGuard actually tests.
5. What PromptGuard may accurately claim.

Clearly distinguish between:

- Technical testing
- Legal compliance
- Certification

Do not describe PromptGuard as a certification body.

Do not automatically describe a technical PASS as legal compliance.

Use the principle:

No source, no claim.

For legal statements use:

- VERIFIED
- UNDER REVIEW
- UNCLEAR
- NOT APPLICABLE

---

## Step 9 — Controlled Wording

Create a controlled wording list including at minimum:

- zertifiziert
- Zertifikat
- AI-Act-konform
- DSGVO-konform
- gesetzlich vorgeschrieben
- Pflichtprüfung
- garantiert
- 100 % sicher
- als Einzige
- niemand sonst

The documentation must require evidence and review before these claims are published.

---

## Step 10 — Generate the Initial Governance Report

After implementing the framework:

1. Run the governance checker.
2. Run the governance tests.
3. Inspect the generated results.
4. Correct obvious false positives.
5. Perform manual review where required.
6. Generate:

governance/reports/GOVERNANCE_REPORT.md

The report must contain:

- Assessment date
- Repository commit
- Repository scope
- Assessment methodology
- All 12 controls
- Status
- Repository evidence
- Identified gaps
- Limitations
- Recommendations
- Manual review requirements

Include this summary table:

| ID | Control | Reference | Status | Evidence | Gap |
|----|---------|-----------|--------|----------|-----|

---

## Step 11 — Update Governance README

Ensure governance/README.md explains:

- Purpose
- Scope
- The 10 governance controls
- The 2 logging controls
- Assessment statuses
- Assessment methodology
- Evidence requirements
- Legal and claims governance
- Distinction between testing, compliance and certification
- How to run the governance checker
- How to run tests
- Continuous improvement

Do not replace or delete the existing root README.md.

---

## Step 12 — Final Validation

Before completing:

Run:

python governance/scripts/run_governance.py

Run the relevant tests.

Then provide a final summary containing:

1. Files created.
2. Files modified.
3. Tests executed.
4. Governance results.
5. PASS controls.
6. PARTIAL controls.
7. FAIL controls.
8. UNCLEAR controls.
9. Manual actions required.

Do not commit or push any changes.

Stop after implementation and validation and wait for human review.

