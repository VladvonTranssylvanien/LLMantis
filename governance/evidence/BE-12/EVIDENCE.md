# BE-12 — Security and Governance Logging — Evidence

**Compliance Status: NON-COMPLIANT**

**Compliance Percentage: 0%**

## What was found

- `grep -rn "import logging\|getLogger\|logger\." backend/*.py` returns **zero matches** across the entire backend.
- Errors are still handled via bare `print()` statements — confirmed examples: `backend/config.py:205` (`print("WARNING: JWT_SECRET not set in .env...")`), `backend/main.py:201` (`print(f"ERROR: Failed to save scan to database: {e}")`, inside an `except Exception as e: db.rollback()` block whose own comment says "Log the error" but performs a `print`, not a logger call).
- `grep -n "class AuditLog" backend/models.py` returns no matches — no dedicated audit-log entity exists anywhere in the data model, despite new, security-relevant event categories now existing (login attempts and lockouts, logout/token revocation, API key issuance/revocation, role/branding changes, DNS ownership-verification challenges) that didn't exist at the prior governance baseline.

## Why NON-COMPLIANT

Both elements this control checks for (structured application/security logging, and a governance/administrative audit trail) are completely absent, confirmed by direct, reproducible search across the entire current codebase.
