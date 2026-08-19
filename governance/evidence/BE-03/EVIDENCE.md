# BE-03 — AI Risk and Scoring Governance — Evidence

**Compliance Status: COMPLIANT**

**Compliance Percentage: 100%**

## What was found

- `backend/scoring.py`: deduction-based formula — every scan starts at 100, loses points per finding (critical 35, high 15, medium 8, low 4), each multiplied by confidence (confirmed 1.0/likely 0.7/possible 0.4); six-band grading (A–F); critical-fail grade cap at B; `MIN_COMPLETED`/`MIN_CRITICAL_COVERAGE` completeness thresholds.
- `calibration/scoring_v2.py`: confirmed, by direct comparison, to carry identical constants to `backend/scoring.py` — a deliberately retained, in-sync reference copy for offline experimentation, not a diverged fork.
- `frontend/report.html`'s displayed `scoring_explanation` text matches `backend/scoring.py:explain()`'s actual output verbatim.

## Why COMPLIANT

All three sub-checks (implementation soundness, sync with the offline reference copy, consistency with frontend display) are met with direct evidence. The absence of an automated test for this formula is tracked under BE-11 (Regression Testing) and is not double-counted as a deduction here — this control assesses correctness/consistency, not test coverage.
