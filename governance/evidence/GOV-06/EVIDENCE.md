# GOV-06 — Sensitive Data Protection — Evidence

## Screenshot captured

**`api-health-key-redacted.jpg`**

Captured 2026-08-15 from the running local app (mock mode, see GOV-01 for
setup) via `GET /api/health`. Shows `"api_key":"not set"` in the config
summary string — confirming `backend/config.py:summary()` reports presence
only (`set`/`not set`), never the key value itself, matching the automated
check in `governance/scripts/run_governance.py:check_gov06`.

No `.env` file was created or used to capture this evidence — the app was
run with `PROVIDER=mock` passed as an environment variable directly, and
`ANTHROPIC_API_KEY` was left unset, which is why the screenshot legitimately
shows `not set` rather than a redacted-but-present key.

## Status

Supplementary only. Sensitive-data-protection evidence is primarily the
pattern-based repository scan in `governance/scripts/run_governance.py`
(`check_gov06`), which is not a screenshot and covers all git-tracked files,
not just this one endpoint.

## Explicit reminder

Do not capture or store a screenshot showing a real, populated
`ANTHROPIC_API_KEY` value, even partially. If this evidence is ever
re-captured against a real configured environment, verify the image shows
`"set"` only, never the key's characters, before saving it here.
