# BE-05 — Target Authorization and Active Testing Control — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 85%**

## What was found

- `backend/ownership.py`: `create_challenge()` generates a token via `secrets.token_hex(12)` (cryptographically secure), persists a `pending` row with a 24-hour `expires_at`. `verify_ownership()` checks challenge expiry, then resolves `_llmantis.{domain}` TXT records and requires an exact string match. On success, sets a 90-day re-verification expiry. `is_domain_verified()` requires a non-expired `verified` row scoped to the exact `org_id + domain`.
- `backend/main.py`: `POST /api/scan` in `mode="api"` returns 403 if `effective_org_id is None and not waived`, then checks `is_domain_verified()` before proceeding — a real, blocking, pre-scan check, not a warn-only log.
- `backend/config.py`: a `SCAN_UNVERIFIED_DOMAINS` waiver list exists, empty by default, explicitly commented as **not** scoped per-organization — any registered user can use a domain on this list if populated.

## Basis for 85%

The core mechanism (DNS-TXT challenge, expiry enforcement, per-org+domain binding) is sound and genuinely enforced — comparable in design to standard ACME-style domain-ownership proof. The deduction reflects the one architectural gap: the waiver mechanism, while empty by default, is not org-scoped by design.
