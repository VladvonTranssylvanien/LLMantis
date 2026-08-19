# BE-07 — Sensitive Data and Secret Protection — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 70%**

## What was found

- `backend/apikeys.py`, `backend/auth.py`: API keys and passwords are correctly hashed at rest (SHA-256 and bcrypt respectively) — no plaintext secret storage found.
- `backend/config.py:184`: `DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://llmantis:llmantis_dev_password@localhost:5432/llmantis")` — a development database credential hardcoded directly in application source.
- The identical credential string is duplicated in `.env.example` and `docker-compose.yml:9` (`POSTGRES_PASSWORD: llmantis_dev_password`) — present in three files, not one.
- `backend/config.py:202`: by contrast, `JWT_SECRET` defaults safely — empty string falls back to `secrets.token_hex(32)` with a printed warning, not a fixed value. This is a positive pattern, cited for contrast.

## Basis for 70%

2 of 3 sub-checks met (proper hashing of API keys/passwords; safe JWT secret fallback pattern). 1 of 3 not met (hardcoded database credential, tripled across files). This is very likely an intentional, labeled, localhost-only dev default rather than a leaked production credential — but it is still a hardcoded credential-shaped value in source, contradicting the project's own `SECRETS.md` guidance ("never hardcode secrets in code").
