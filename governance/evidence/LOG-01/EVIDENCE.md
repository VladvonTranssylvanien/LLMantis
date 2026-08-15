# LOG-01 — Security and Application Logging — Evidence

## No screenshot captured

`backend/*.py` contains no `import logging` or structured logger (confirmed
by `governance/scripts/run_governance.py:check_log01`), and
`frontend/index.html` exposes only "prompt" mode, not the "api" mode most
likely to surface a network-level error worth logging. There is no log
output, log file, or log viewer in this repository to screenshot — a
screenshot of "nothing" would not be verifiable evidence.

What does exist and was confirmed directly (not screenshotted): scan/judge
errors are captured **in-band** as an `ERROR` verdict dict in
`backend/scanner.py:_run_one`'s exception handlers, so a failure is visible
to the calling client, but nowhere durably logged with a severity level or
timestamp.

## What a contributor should capture once this control improves

1. Add structured logging (e.g. Python's `logging` module, JSON-formatted)
   to `backend/scanner.py` and `backend/main.py` for scan/judge/provider
   errors.
2. Trigger a real error (e.g. run the app in `api` mode against an
   unreachable URL, or `PROVIDER=anthropic` with no API key).
3. Screenshot the resulting log line, showing severity and timestamp, with
   no sensitive value (system prompt, canary, customer answer) visible in
   the log text.
4. Save as `governance/evidence/LOG-01/error-log-entry.png`.
