# GOV-07 — Change Management — Evidence

## No screenshot captured automatically

This governance framework was implemented in a headless CLI environment
with no authenticated GitHub browser session. Capturing genuine evidence of
pull-request review and branch-protection settings requires being signed
in to `github.com/VladvonTranssylvanien/promptguard` (or its LLMantis
rename) as a repository member — which this environment does not have, and
should not attempt to obtain automatically, since that would mean acting on
someone's real authenticated session outside the scope of this task.

Text-based evidence (not a screenshot) already exists in
`governance/reports/GOVERNANCE_REPORT.md`, generated from real `git log`
and `git branch -a` output: commit history containing 6 "Merge pull
request" commits and 10 branch references at the time of assessment.

## What a contributor should capture

1. Sign in to GitHub as a repository member.
2. Navigate to the repository's **Pull requests** tab (filter: closed/merged)
   and screenshot a list showing at least one reviewed-and-merged PR.
   Save as `governance/evidence/GOV-07/pull-requests-merged.png`.
3. Navigate to **Settings → Branches** and screenshot the branch protection
   rule for `main` (if any exists). Save as
   `governance/evidence/GOV-07/branch-protection-main.png`.
   If no rule exists, take the screenshot anyway — it is valid evidence of
   the current (unprotected) state, which is itself a governance finding.
4. If a `CONTRIBUTING.md` is later added, note its path here instead of a
   screenshot.

## Status

Until the above is captured, GOV-07 relies solely on the git-history-based
automated evidence already in `governance/reports/GOVERNANCE_REPORT.md`.
