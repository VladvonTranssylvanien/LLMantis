# LLMantis — Governance V2

## What this is

Governance V2 is LLMantis's technical governance assessment: an evidence-based review of 17 controls across the frontend and backend, each independently verified against the current codebase — not against documentation or commit messages alone.

**Assessment baseline:** commit `f301d3e` (this is the second full re-assessment; every control was independently re-verified against current code, not carried forward from the previous pass at `114ebc9`).

## Scope

**Frontend (FE-01–FE-05):** AI transparency/disclosure, marketing and legal claims, user-facing security/privacy pages, output and report integrity, accessibility.

**Backend / Platform (BE-01–BE-12):** AI provider governance, attack library governance, scoring, judge calibration, target authorization, authentication, secret handling, application/network security (SSRF, rate limiting), evidence/traceability, change management, regression testing, and security logging.

Full control definitions: `controls/frontend-controls.yaml`, `controls/backend-controls.yaml`.
Full assessment: `reports/GOVERNANCE_V2_REPORT.md` — the single official assessment of record.
Per-control evidence: `evidence/<CONTROL-ID>/EVIDENCE.md`.

## Status vocabulary

- **COMPLIANT (100%)** — every sub-requirement of the control's intent is met, with direct evidence, no known gap.
- **PARTIALLY COMPLIANT (1–99%)** — some but not all of the control's intent is met. The percentage reflects countable sub-checks where they exist, or explicit stated reasoning where the control is genuinely continuous — never a bare number with no shown work.
- **NON-COMPLIANT (0%)** — the core thing the control checks for is absent or contradicted by evidence.

## Regulatory reference classification

Every control's `Regulation`/`Reference` fields are labeled as one of:

- **LEGAL REQUIREMENT** — a binding law or article, cited with its specific number.
- **BEST-PRACTICE** — an industry convention (e.g. OWASP), not a legal obligation.
- **INTERNAL POLICY** — an LLMantis decision, not an external requirement.

Where a regulation's direct applicability to a specific control hasn't been independently verified, the report says so explicitly rather than asserting it.

## How to run the checker

```bash
python governance/scripts/run_governance_v2.py
```

This writes a read-only, pattern-matching cross-check to `reports/GOVERNANCE_V2_AUTOMATED_RERUN.md` (untracked — a local cross-check, not a second source of truth). It is a lower bound, not a guarantee: it has caught real gaps but has also taken self-descriptive comments at face value where the manual assessment dug deeper. Discrepancies between it and `GOVERNANCE_V2_REPORT.md` should be investigated, not assumed to be errors in either document.

Run `python -m unittest governance.tests.test_governance_v2 -v` to verify the framework's own structure (all 17 control IDs present, no duplicates, report/YAML baseline consistency).

## Disclaimer

This is a technical governance assessment, not legal advice, a legal opinion, a certification, or proof of regulatory compliance. See `docs/legal/DISCLAIMERS.md`.
