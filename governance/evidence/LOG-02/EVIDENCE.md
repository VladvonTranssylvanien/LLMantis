# LOG-02 — Governance Audit Logging — Evidence

## No screenshot captured

No dedicated `AuditLog` entity exists in `backend/models.py` (confirmed by
`governance/scripts/run_governance.py:check_log02`), and the NDJSON events
`POST /api/scan` emits (`start`/`result`/`complete`/`error`) are streamed
directly to the requesting browser and never persisted. There is no audit
log, audit table, or audit viewer anywhere in this repository to
screenshot.

`PLAYBOOK.md`'s own data-model sketch (Part II §4) lists an `AuditLog[]`
entity on `Organization` that has not been implemented — this control's gap
is an acknowledged, pre-existing design intent, not a newly discovered one.

## What a contributor should capture once this control improves

1. Implement an append-only audit-log table (e.g. `AuditLog` in
   `backend/models.py`) recording at minimum: scan started/completed/failed,
   target authorization decisions, and critical findings, each with a
   timestamp.
2. Run a scan and query the resulting audit-log rows (e.g. via a database
   client or an admin view).
3. Screenshot the query result showing at least one governance-relevant
   event with its timestamp, and save as
   `governance/evidence/LOG-02/audit-log-entries.png`.
