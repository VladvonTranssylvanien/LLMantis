# BE-10 — Change, Dependency and Configuration Management — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 20%**

## What was found (previous period, `f48fdbf..114ebc9`)

`git log --oneline f48fdbf..114ebc9 | grep -c "Merge pull request"` = 19 of 168 commits (11%) — already the weakest of the three sub-areas.

## Re-verified at commit f301d3e — the current period is worse, not better

`git log --oneline 114ebc9..f301d3e` = 24 commits since the previous governance baseline. Of those, **zero** match "Merge pull request" (2 are local "merge remote-tracking branch" integration merges from a plain fetch, not reviewed PR merges). The reviewed-change rate fell from an already-low 11% to 0% in the period that produced this report's two most consequential findings (the BE-03 scoring divergence and the BE-04 calibration staleness) — exactly the outcome unreviewed changes to scoring/judge logic predict.

- `requirements.txt`: remains complete and unusually well-documented — `sqlalchemy==2.0.52`, `psycopg[binary]==3.3.4`, `alembic==1.13.1`, `slowapi==0.1.10`, `bcrypt==5.0.0`, `PyJWT==2.13.0`, `playwright==1.62.0` all present, each with an inline comment naming its consumer.
- `docker-compose.prod.yml`: still passes `--forwarded-allow-ips "*"` to uvicorn. This remains a documented risk-acceptance (the app service publishes no host port and is reachable only via the internal Docker network, per an adjacent code comment) rather than an unexamined default — real reasoning exists, even though the setting itself is still a wildcard.
- No `.github/` or other CI configuration exists to enforce review going forward.

## Basis for 20%

Of three sub-areas, dependency completeness remains solid and the proxy-trust setting is a reasoned (if still permissive) risk-acceptance rather than an oversight — both given partial credit. Change review is the weakest leg and got measurably worse (11% → 0%) in the exact period covered by this report, with no CI to backstop it. The percentage is lowered from the previous pass's 25% to reflect that regression.
