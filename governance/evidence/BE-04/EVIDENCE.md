# BE-04 — AI Judge Validation and Calibration — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 55%**

## What was found

- `calibration/calibrate.py:60`: imports and replays the actual production judge (`from backend.judge import deterministic_check, judge`) — not a reimplementation.
- `calibration/set-v1.yaml` (30 items) and `set-v2.yaml` (43 items): human-labelled ground truth, `human_label` field non-null across both files (confirmed by direct inspection), each carrying the human reviewer's reasoning.
- Recorded, reproducible results (`PROJECT-STATE.md`, `GREGOR_WORKLOG.md`): 29/29 stable agreement on the 30-item set across 10 runs on the current engine; deterministic layer 11/11 (set v1) and 13/13 (set v2) with zero disagreements across every run; 95.3% mean agreement on the 43-item set across 5 runs.
- The project's own documentation honestly discloses a limitation: the six criteria newly added in v2 are validated only in the false-positive-catching direction — no calibration item currently tests whether the judge correctly *catches* a violation of these new criteria, only whether it avoids incorrectly flagging one.

## Basis for 85% (previous pass) — superseded below

## Re-verified at commit f301d3e — the recorded numbers now predate the judge they claim to describe

`calibration/calibrate.py` still imports and replays the live `backend/judge.py`; both calibration sets remain fully human-labelled. But `PROJECT-STATE.md` dates the 29/29 / 11/11 / 13/13 / 95.3% figures "measured 18.08 on the current engine," and `git log` shows two further commits to `backend/judge.py` on 19.08:

- `218b0c6` — a real, documented false-positive fix (the judge asked "did it reveal its instructions" with no instructions present; measured 9/20 false-fail before, 0/20 after, on one bot).
- `453798e` — added `disclosed_confidential`, the field now driving BE-03's severity escalation to `critical`.

No calibration re-run is recorded after either commit, and `calibration/calibrate.py` has **no comparison logic at all** for `disclosed_confidential` — confirmed by a zero-match search across the harness and both calibration YAML files. A field that now directly decides whether a scan can receive the worst grade has never been checked against a human label.

## Basis for 55%

The structural strengths are real and unchanged: the harness replays the live judge, both sets are fully labelled, and the false-positive-only limitation on newer criteria is honestly disclosed. The score is lowered from 85% because the specific quantitative claims that justified most of that figure no longer describe the judge that ships today, and the one behavior change most relevant to scoring severity has no calibration coverage in any direction, not just an incomplete one.
