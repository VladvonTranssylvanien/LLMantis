# GOV-01 — AI Component Inventory — Evidence

## Screenshot captured

**`api-health-model-config.jpg`**

Captured 2026-08-15 by running the app locally in `PROVIDER=mock` mode
(`uvicorn backend.main:app --host 127.0.0.1 --port 8123`, isolated
`.governance-venv`, no `.env` file, no real API key) and navigating to
`GET /api/health`.

Shows: `provider=mock`, `target=claude-sonnet-4-5`, `judge=claude-sonnet-4-5`,
`concurrency=5`, `api_key=not set`, `attacks_loaded=21` — i.e. the running
process's actual AI component configuration, matching
`backend/config.py`'s `summary()` output referenced in
`governance/reports/GOVERNANCE_REPORT.md`.

## Status

Supplementary only. This screenshot confirms the configuration summary
renders as expected at runtime; it does not replace the source-file evidence
(`backend/config.py`, `backend/llm.py`, `requirements.txt`) already cited in
the control's automated check.

## If re-capturing

1. `python3 -m venv .governance-venv && source .governance-venv/bin/activate`
2. `pip install fastapi==0.115.6 "uvicorn[standard]==0.34.0" pyyaml==6.0.2 python-dotenv==1.2.2 httpx==0.28.1`
3. `PROVIDER=mock uvicorn backend.main:app --host 127.0.0.1 --port 8123`
4. Visit `http://127.0.0.1:8123/api/health` and screenshot the JSON response.
5. Confirm no real API key value is visible (only `set`/`not set`) before saving.
