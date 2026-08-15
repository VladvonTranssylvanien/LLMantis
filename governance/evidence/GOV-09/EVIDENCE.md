# GOV-09 — Evidence and Traceability — Evidence

## Screenshot captured

**`scan-finding-attack-id-evidence-fix.jpg`**

Captured 2026-08-15 from the live mock-mode scan described in
`governance/evidence/GOV-03/EVIDENCE.md`. Shows one finding's full detail:
attack id (`inj_direct_override`), severity (`CRITICAL`), method
(`deterministic`), the exact attack text sent, the bot's answer, the
evidence quote (`SECRET-VIP-2026`), and the suggested fix — i.e. the
traceable chain from a specific attack to a specific, quoted result that
`backend/scanner.py` and `backend/judge.py` are designed to produce.

## What this screenshot does NOT show

It does not show `scan_id`, timestamp, or attack-library version — those
are not rendered in the current `frontend/index.html` results view, even
though `scan_id` and timestamps exist in `backend/scanner.py`'s return value
and `backend/models.py`'s persisted `Scan`/`Result` rows. This is consistent
with the GOV-09 gap already recorded in
`governance/reports/GOVERNANCE_REPORT.md`: traceability fields exist in the
backend but the attack-library/model version is not persisted per scan, and
several already-computed fields (scan_id, timestamp) are not surfaced to the
person reading the report in the browser.

## If more evidence is needed

Capture a screenshot of a persisted `Scan`/`Result` row (e.g. via a database
inspection tool once PostgreSQL is wired up per `dab179b feat: PostgreSQL
database integration complete`), showing `scan_id`, `created_at`, and the
foreign-key chain to `Target`/`Organization`, and save it as
`governance/evidence/GOV-09/persisted-scan-record.png`.
