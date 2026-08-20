# FE-01 — AI Transparency and User Disclosure — Evidence

**Compliance Status: COMPLIANT**

**Compliance Percentage: 100%**

## What was found

- `backend/art50engine.py`, `art50probes.py`, `art50opener.py` implement real, browser-automated (Playwright) disclosure detection — 12 probes across desktop/mobile viewports.
- A documented, verified fix exists for a prior false positive: a widget merely *named* "KI-Assistent" no longer counts as a disclosure (`art50probes.py`'s `NAMED` regex and `navAway()` signpost-demotion logic).
- `frontend/art50check.html` posts to a real backend route (`POST /api/art50check`, `backend/main.py`), not a disconnected script.
- No LLMantis-owned interface (`index.html`, `report.html`) was found to impersonate a human or obscure that judging/scanning is automated.

## Why this is COMPLIANT, not just "feature exists"

Per the Governance V2 principle of assessing feature + code path + enforcement: the disclosure-detection logic was traced end-to-end (URL submission → Playwright render → probe execution → NDJSON stream → UI display), and the specific historical false-positive bug was confirmed fixed by reading the actual detection regex, not by trusting a commit message.

## Residual note

Whether EU AI Act Art. 50(1) applies *directly* to LLMantis's own architecture (a form-based tool, not a conversational persona) has not been independently established — this affects the regulatory-relevance classification, not the technical discovery above.

## Re-verified at commit f301d3e — two new additions, neither changes the status

- `frontend/art50report.html` (new): a print/PDF sibling of `report.html`, populated only from `sessionStorage` data the backend already returned. No new endpoint, no new disclosure claim.
- `tools/voice50/` (new): phone-based Art. 50 disclosure checking. Confirmed **not shipped** — zero references to it exist in `backend/`, `frontend/`, or `Dockerfile`; its own README states the shipped product is untouched by it. One of its test fixtures (`twilio_call.py`) scripts a simulated bot that impersonates a human, but only as the deliberately non-compliant *target* the checker validates itself against, dialed only with the operator's own recorded consent — not an LLMantis-owned customer-facing interface.
- `backend/art50engine.py` itself is byte-for-byte unchanged since the previous baseline.
