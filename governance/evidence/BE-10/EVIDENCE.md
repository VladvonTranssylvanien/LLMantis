# BE-10 — Change, Dependency and Configuration Management — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 25%**

## What was found

- `git log --oneline f48fdbf..114ebc9 | grep -c "Merge pull request"` = 19; total commits in the same range = 168. Only **11%** of commits were merged via reviewed pull requests, despite this range including authentication, ownership verification, SSRF handling, and deployment configuration.
- `requirements.txt`: now complete — `sqlalchemy==2.0.52`, `psycopg[binary]==3.3.4`, `alembic==1.13.1`, `slowapi==0.1.10`, `bcrypt==5.0.0`, `PyJWT==2.13.0`, `playwright==1.62.0` all present (a prior gap where these were missing entirely, despite being required by `backend/database.py`/`models.py`, has been resolved).
- `docker-compose.prod.yml:52`: passes `--forwarded-allow-ips "*"` to uvicorn, trusting `X-Forwarded-For` from any source for rate-limit keying — safe only under an unenforced network-topology assumption (no port published directly), documented in an adjacent comment but not technically enforced.

## Basis for 25%

Of three sub-areas assessed (change review, dependency completeness, deployment hardening), only one (dependency completeness) is solid. Change review is weak (11% PR rate) and deployment configuration has a real, if bounded, permissive default. 1 of 3 fully met, with the two unmet areas being significant given the security-sensitivity of what shipped.
