# FE-04 — Output, Report and Claim Integrity — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 40%**

## What was found — working correctly

- `frontend/report.html`'s grade/score display matches `backend/scoring.py`'s live formula (deduction-based, confidence-weighted, B-grade critical cap).
- `frontend/report.html` correctly displays the real `attack_library_version`/`library_name` returned by the API (resolves a prior known gap).
- `frontend/report.html` correctly downgrades unquotable judge-flagged failures to a disclosed PASS with explanation, rather than silently withholding or fabricating evidence.

## What was found — not compliant

- `frontend/index.html`'s live scan-results view has **zero** references to `confidence` or `possible` (confirmed by direct grep) — no equivalent to `report.html`'s confidence display or unquotable-finding handling exists there.
- `frontend/report.html`'s disclaimer block contains, unconditionally, on every generated report:
  > "Testing was performed with the verified consent of the system's owner."
  This sentence is printed regardless of whether ownership verification actually occurred for the specific scan being reported — there is no conditional check against any verification flag in the rendering code.

## Basis for 40%

Grade/score/version display remains solid. The unconditional consent claim is a serious defect on a document whose entire purpose is to serve as evidence — re-verification at commit f301d3e traced the exact code paths where it is affirmatively false, not merely incomplete: `backend/scanner.py`'s report dict carries no `authorized`/`ownership_verified` field at all (confirmed by grep), and ownership verification is only ever asked for `mode="api"` scans that aren't on the (org-unscoped) waiver list — `mode="prompt"`/`"model"` scans, the common case, never ask the question, yet still print "verified consent of the system's owner" on every report. Because this is a false statement of fact on a subset of real, reachable traffic (not a hypothetical), the score is lowered from the previous pass's 50% to 40%, weighted down from grade/version consistency (solid) and the confidence-display gap (real but moderate) by this one severe, concretely-demonstrated defect.
