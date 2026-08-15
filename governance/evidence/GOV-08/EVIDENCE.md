# GOV-08 — Human Oversight — Evidence

## Screenshot captured

**`report-view-no-confidence-filter.jpg`**

Captured 2026-08-15 from the same live mock-mode scan described in
`governance/evidence/GOV-03/EVIDENCE.md`. Shows the "11 vulnerabilities
found" report view, with each finding labelled by severity and method
(e.g. `deterministic`), and the scoring explanation text visible above it.

This screenshot is evidence of a gap, not a capability: README.md states
that `possible`-confidence findings are omitted from customer-facing
reports, but nothing in this view filters, groups, or otherwise distinguishes
findings by confidence level for a human reviewer to act on — every finding
in this mock run happened to be `deterministic` (mock mode's fake judge never
produces a `possible` verdict; see `governance/evidence/GOV-04/EVIDENCE.md`),
so this run could not show what a `possible`-confidence finding looks like
in this UI, filtered or not.

## Status

Supplementary only. The underlying finding — that
`frontend/report.html` was not found to enforce the stated
confidence-based filtering policy — comes from a direct source-file check
in `governance/scripts/run_governance.py:check_gov08`, not from this
screenshot.

## If more evidence is needed

Once `PROVIDER=anthropic` (or a Mistral/Aleph Alpha judge, per
`PROJECT-STATE.md` technical debt #1) has actually been run and produces a
genuine `possible`-confidence AI-judge verdict, capture a screenshot showing
whether that finding is surfaced, filtered, or flagged for review, and save
it as `governance/evidence/GOV-08/possible-confidence-finding.png`.
