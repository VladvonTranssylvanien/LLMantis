# BE-04 — AI Judge Validation and Calibration — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 85%**

## What was found

- `calibration/calibrate.py:60`: imports and replays the actual production judge (`from backend.judge import deterministic_check, judge`) — not a reimplementation.
- `calibration/set-v1.yaml` (30 items) and `set-v2.yaml` (43 items): human-labelled ground truth, `human_label` field non-null across both files (confirmed by direct inspection), each carrying the human reviewer's reasoning.
- Recorded, reproducible results (`PROJECT-STATE.md`, `GREGOR_WORKLOG.md`): 29/29 stable agreement on the 30-item set across 10 runs on the current engine; deterministic layer 11/11 (set v1) and 13/13 (set v2) with zero disagreements across every run; 95.3% mean agreement on the 43-item set across 5 runs.
- The project's own documentation honestly discloses a limitation: the six criteria newly added in v2 are validated only in the false-positive-catching direction — no calibration item currently tests whether the judge correctly *catches* a violation of these new criteria, only whether it avoids incorrectly flagging one.

## Basis for 85%

This is a real, executed, reproducible measurement program — not a script that merely *could* calibrate. The deduction from 100% reflects the disclosed, real gap: new criteria validated one-directionally only.
