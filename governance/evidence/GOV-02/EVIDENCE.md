# GOV-02 — Attack Governance — Evidence

## Screenshot captured

**`api-attacks-library.jpg`**

Captured 2026-08-15 from the running local app (mock mode, see GOV-01 for
setup) via `GET /api/attacks`.

Shows all 21 attacks with their `id`, `category` and `severity` fields, and
the 5 declared categories with per-category counts — confirming the library
structure that `backend/attacks.py:_validate()` enforces at load time.

## Status

Supplementary only. The authoritative evidence remains
`attacks/attacks.yaml` and `backend/attacks.py` — this screenshot shows the
validated library as served, not the validation logic itself.

## If re-capturing

Start the local app per GOV-01's instructions, then visit
`http://127.0.0.1:8123/api/attacks` and screenshot the response. Re-run
`python governance/scripts/run_governance.py` afterward — it independently
recounts attacks and categories by parsing `attacks/attacks.yaml` directly.
