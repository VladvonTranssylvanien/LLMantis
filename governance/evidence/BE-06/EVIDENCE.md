# BE-06 — Authentication and Access Control — Evidence

**Compliance Status: COMPLIANT**

**Compliance Percentage: 100%**

## What was found

- `backend/auth.py`: passwords hashed with bcrypt; JWT bearer tokens carry `sub` (user id) and `tv` (token_version); `get_current_user` re-checks `token_version` against the DB row so logout invalidates old tokens.
- Timing side-channel fix confirmed: a module-level `DUMMY_HASH` is precomputed at import; `verify_password` runs unconditionally against `user.password_hash if user else DUMMY_HASH` — bcrypt executes the same cost path whether or not the email exists, with no early return before it runs.
- `require_membership(db, user, org_id, min_role)`: role checks use `ROLE_RANK = {"member":0,"admin":1,"owner":2}` comparison, enforced at every checked route (branding PUT requires admin; API key create/delete require admin; adding a member requires owner), raising 403 on rank failure. Unrecognized role strings rank as `-1` via `.get(role, -1)` — fails closed, not open.
- `backend/apikeys.py`: keys generated via `secrets.token_urlsafe(24)`; only `sha256(key)` stored (`key_hash`), plaintext returned once at creation; revocation is a soft-delete (`revoked_at`) checked on every use.

## Why COMPLIANT

Every sub-check (password hashing, timing-safety, session revocation, role enforcement with fail-closed default, API key hashing/revocation) was verified with direct code citations, not inferred from feature presence.

## Explicitly not counted against this control

Cross-tenant data isolation (can an Org A user reach Org B's data through any endpoint) was **not independently tested** this session. This is noted as a recommendation, not treated as a compliance deduction, since the code reviewed does correctly scope by `org_id` — the untested dimension is adversarial verification, not a known gap.
