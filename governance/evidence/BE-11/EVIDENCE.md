# BE-11 — Regression Testing and Operational Monitoring — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 15%**

## What was found

- Direct search (`find . -iname "test_*.py" -o -iname "*_test.py"`) still finds **zero** test files anywhere in `backend/`.
- `tools/art50v2/test_fixtures.py` and `tools/voice50/test_fixtures.py` (the latter new since the previous baseline) are real, working, fixture-based verification scripts — each spins up a local fixture (an HTTP server or recorded audio) with a known-correct verdict and checks the relevant engine against it. Both are confirmed manually-invoked only: a repo-wide search finds no `.github/`, `Makefile`, `package.json`, or `Dockerfile` reference to either script, and no other CI configuration exists anywhere in the repository.
- No monitoring or alerting infrastructure exists beyond `GET /api/health`, a static-configuration liveness endpoint with no confirmed external consumer.

## Why PARTIALLY COMPLIANT rather than NON-COMPLIANT

The core gap is unchanged and serious: nothing automated protects `backend/` — the exact place this period's real scoring and judge bugs (BE-03, BE-04) were found and fixed by hand, only after the fact. That alone would be NON-COMPLIANT. The two fixture scripts are given partial credit because they are genuine, functioning verification tools for two real subsystems (not stubs, not aspirational) — the gap is that they never run automatically, not that they don't exist or don't work.

## Consequence made concrete this session

This same absence of backend testing is why the scoring/judge divergence (BE-03) and the calibration staleness (BE-04) were only found by this governance re-assessment rather than by anything that runs on every change — a live illustration of exactly what this control exists to prevent.
