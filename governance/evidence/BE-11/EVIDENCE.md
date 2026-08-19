# BE-11 — Regression Testing and Operational Monitoring — Evidence

**Compliance Status: NON-COMPLIANT**

**Compliance Percentage: 0%**

## What was found

- Direct search (`find . -iname "test_*.py" -o -iname "*_test.py"`) found **zero** test files anywhere in `backend/`. The only test file outside `governance/` in the entire repository is `tools/art50v2/test_fixtures.py`, unrelated to the scan/judge/scoring/auth/ownership engine.
- No `.github/workflows/` directory or any other CI configuration exists anywhere in the repository.
- No monitoring or alerting infrastructure was found beyond the basic `GET /api/health` endpoint (which reports static configuration, not runtime health metrics or alerts).

## Why NON-COMPLIANT

All three elements this control checks for (automated tests, CI, monitoring) are absent. This is a live, current, easily-reproduced check (a directory search and a git-history lookup), not an inference — the gap is unambiguous.

## Consequence made concrete this session

This same absence of testing is why the earlier-observed default-provider regression (`PROVIDER=mock` producing 100% scan errors under a prior configuration) was able to ship and persist across several commits before being noticed — a live illustration of exactly what this control exists to prevent.
