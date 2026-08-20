# FE-05 — Accessibility, User Understanding and Human Interaction — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 70%**

## What was found

- `frontend/index.html` and `frontend/report.html` use ARIA semantics: `role="status"`, `role="alert"`, `role="progressbar"`, `aria-live="polite"`, `aria-expanded`, `aria-valuenow`/`aria-valuemax` on the live feed and findings accordion.
- `frontend/report.html` includes a plain-language "How this was judged" section explaining the two-layer method (deterministic string match vs. AI judge) to a non-technical reader.
- Real backend capabilities have **no** corresponding frontend workflow: authentication/registration (`backend/auth.py`), ownership verification (`backend/ownership.py`), API key management (`backend/apikeys.py`), and organization/branding management all exist only as API endpoints. `grep -rl "ownership" frontend/` returns no matches; no login/register form exists anywhere in `frontend/`.

## Basis for 70%

Accessibility semantics and the judging-method explanation are both genuinely present and well-implemented — the control's core intent (can a user understand and interact with results) is substantially met for the features that do have a UI. The score is not higher because a meaningful portion of the platform's actual capability is invisible to the people it affects (they cannot see or manage their own ownership-verification or API-key state).
