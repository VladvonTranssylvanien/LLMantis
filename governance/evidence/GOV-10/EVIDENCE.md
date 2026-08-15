# GOV-10 — Regression and Monitoring — Evidence

## No screenshot captured

There is nothing to screenshot: no CI/CD configuration exists
(`.github/workflows/` is absent) and no automated test suite exists for the
product's scanning/judging/scoring engine outside of `governance/tests/`
itself (confirmed by `governance/scripts/run_governance.py:check_gov10`).
A screenshot of an empty directory or a "no workflows" GitHub page would not
add verifiable information beyond what the automated check already states.

## Text evidence instead

The governance test suite itself *can* be screenshotted or transcript-captured
as a demonstration of what regression testing looks like once it exists for
the product:

```
$ python -m unittest governance.tests.test_governance -v
...
Ran 24 tests in 0.2s
OK
```

This is evidence that automated, repeatable testing is possible in this
repository's toolchain (stdlib `unittest`, zero extra dependencies) — the
gap is that it has not yet been extended to `backend/`.

## What a contributor should capture once this control improves

1. A screenshot of a green GitHub Actions run once
   `.github/workflows/tests.yml` (or similar) exists, saved as
   `governance/evidence/GOV-10/ci-run-green.png`.
2. A screenshot (or pasted transcript) of the "mutation check" described in
   `PLAYBOOK.md` Part IV §9 — deliberately breaking `backend/judge.py` (e.g.
   making it always return `PASS`) and showing which tests fail as a result.
   Save as `governance/evidence/GOV-10/mutation-check-result.png` or
   `.txt`.
