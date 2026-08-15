# GOV-04 — AI Judge Validation — Evidence

## Screenshot captured

**`scan-finding-detail-deterministic-evidence.jpg`**

Captured 2026-08-15 from the same live mock-mode scan run described in
`governance/evidence/GOV-03/EVIDENCE.md`. Shows one expanded finding
(`inj_direct_override`, CRITICAL) with the attack sent, the bot's answer,
and the evidence quote (`SECRET-VIP-2026`) — labelled `deterministic`,
i.e. decided by `backend/judge.py`'s layer-1 string/canary match, not by
the AI judge.

## What this screenshot does NOT show

It does not demonstrate judge *calibration*. Mock mode's fake judge
(`backend/llm.py:_mock_chat`) always returns a fixed PASS/FAIL shape and
never produces a `possible`-confidence verdict, so this environment cannot
produce a screenshot of the AI-judge layer's confidence tiering in action,
or of a calibration/agreement measurement — because neither exists yet.
That gap is the actual GOV-04 finding; see
`governance/reports/GOVERNANCE_REPORT.md`.

## If more evidence is needed

Once a judge calibration set exists (README.md / PROJECT-STATE.md both
record this as not started), a contributor should capture:

- A screenshot of the calibration script's output (agreement rate vs.
  human labels), saved as `governance/evidence/GOV-04/calibration-run.png`.
- A screenshot of at least one real (non-mock) scan showing a `likely` or
  `possible` confidence AI-judge verdict, once `PROVIDER=anthropic` (or the
  Mistral/Aleph Alpha migration referenced in `PROJECT-STATE.md` technical
  debt #1) has actually been exercised — this has never been run per
  README.md's own status table.
