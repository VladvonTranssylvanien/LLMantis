# FE-04 — Output, Report and Claim Integrity — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 50%**

## What was found — working correctly

- `frontend/report.html`'s grade/score display matches `backend/scoring.py`'s live formula (deduction-based, confidence-weighted, B-grade critical cap).
- `frontend/report.html` correctly displays the real `attack_library_version`/`library_name` returned by the API (resolves a prior known gap).
- `frontend/report.html` correctly downgrades unquotable judge-flagged failures to a disclosed PASS with explanation, rather than silently withholding or fabricating evidence.

## What was found — not compliant

- `frontend/index.html`'s live scan-results view has **zero** references to `confidence` or `possible` (confirmed by direct grep) — no equivalent to `report.html`'s confidence display or unquotable-finding handling exists there.
- `frontend/report.html`'s disclaimer block contains, unconditionally, on every generated report:
  > "Testing was performed with the verified consent of the system's owner."
  This sentence is printed regardless of whether ownership verification actually occurred for the specific scan being reported — there is no conditional check against any verification flag in the rendering code.

## Basis for 50%

Grade/score/version display is solid (a genuine improvement over the prior baseline). The unconditional false consent claim is a serious, disqualifying defect on a document whose entire purpose is to serve as evidence — this alone caps the score at the midpoint of the Partially Compliant band despite the other improvements.
