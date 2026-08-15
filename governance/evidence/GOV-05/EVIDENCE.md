# GOV-05 — Target Authorization — Evidence

## Screenshot captured

**`scan-form-no-ownership-check.jpg`**

Captured 2026-08-15 from the running local app (mock mode, see GOV-01 for
setup). Shows the entire scan submission form: `Demo bot` selector,
`Canary string`, `System prompt under test`, and `Run scan` — with **no**
ownership-verification step, login, domain-proof or authorization gate
anywhere in the flow before a scan executes.

This is evidence of absence: it visually confirms
`governance/reports/GOVERNANCE_REPORT.md`'s GOV-05 finding that
`POST /api/scan` does not check `OwnershipVerification` (defined in
`backend/models.py`) before running a scan. Note this screenshot was taken
in the shipped "prompt" mode, which tests a copy of the customer's own bot
supplied in the browser, not a third party's live endpoint — the higher-risk
"api" mode (attacking someone else's live endpoint) is not exposed in
`frontend/index.html` at all, which is itself part of why this gap has not
caused a real-world incident yet.

## Status

Supplementary only. Do not treat the absence of a visible authorization
step as proof no such step could exist server-side — the automated check
in `governance/scripts/run_governance.py` (`check_gov05`) confirms this
directly by inspecting `backend/main.py` and `backend/scanner.py`.

## If re-capturing after a fix ships

Once ownership verification is enforced (see recommendation in
`governance/reports/GOVERNANCE_REPORT.md`), capture:

- A screenshot of the scan form now requiring/showing ownership status.
- A screenshot of a rejected scan attempt against an unverified target
  (e.g. an error banner), saved as
  `governance/evidence/GOV-05/scan-rejected-unverified-target.png`.
