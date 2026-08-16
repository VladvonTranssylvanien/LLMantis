# Deploying LLMantis

One Hetzner box, three containers: Caddy in front, the app, Postgres behind.
Only Caddy publishes a port.

Everything below was run against the real images before it was written down.
Where a step is untested on the server itself, it says so.

---

## Before you touch the server

**Point the DNS A record at the box and let it resolve.** Caddy asks Let's
Encrypt for a certificate on its first start; if the name does not resolve to
this machine yet, that request fails and there is a rate limit on retrying it.

```bash
dig +short llmantis.example.de      # must return the server's IP
```

---

## 1. Server prerequisites

```bash
ssh root@<server>
apt update && apt install -y docker.io docker-compose-v2 git
```

## 2. Clone

```bash
git clone https://github.com/VladvonTranssylvanien/LLMantis.git /opt/llmantis
cd /opt/llmantis
```

## 3. Fill in deploy/.env

```bash
cp deploy/.env.example deploy/.env
git check-ignore -v deploy/.env      # must print .gitignore:6:.env
```

Three values have to be generated, not invented:

```bash
# the site password, hashed. Paste ONLY the hash, and double every $ in it -
# compose reads a single $ as a variable reference.
docker run --rm caddy:2.10-alpine caddy hash-password --plaintext 'the-password'

# JWT signing key. Leave it empty and config.py invents a random one at every
# start, which logs everyone out on every deploy.
python3 -c "import secrets; print(secrets.token_hex(32))"

# the database password. Not the development one.
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

Read the file once more before starting anything. `POSTGRES_PASSWORD` and the
password inside `DATABASE_URL` are two places holding the same secret, and
nothing checks that they match — the app simply fails to connect.

## 4. Start

```bash
docker compose -f docker-compose.prod.yml --env-file deploy/.env up -d --build
docker compose -f docker-compose.prod.yml --env-file deploy/.env ps
```

## 5. Build the schema

The app does not create tables on start. Run the migrations once:

```bash
docker compose -f docker-compose.prod.yml --env-file deploy/.env \
  exec app alembic upgrade head

docker compose -f docker-compose.prod.yml --env-file deploy/.env \
  exec app alembic check      # "No new upgrade operations detected."
```

`alembic check` comparing clean is the useful signal here: it means the schema
the migrations built matches `backend/models.py`, not merely that some tables
appeared.

## 6. Prove it works, with a scan

A 200 from `/api/health` says the server answers. It does not say the product
works — in one day that exact reasoning hid three defects. Open the site, log
in with the Basic-Auth password, pick a demo bot, run a scan.

**A grade with zero errors is the pass.** Anything else, start with:

```bash
docker compose -f docker-compose.prod.yml --env-file deploy/.env logs -f app
```

---

## What to verify after the first deploy

| Check | Expected |
|---|---|
| `curl -sI https://<domain>` | `401` without credentials |
| `curl -sI -u user:pass https://<domain>` | `200`, and `X-Robots-Tag: noindex` present |
| `curl -sI http://<domain>` | `308` redirect to https |
| `nmap -Pn <server-ip>` from elsewhere | 80 and 443 only. **5432 must not be open** |
| a scan from the browser | a grade, `errors: 0` |

The port check is the one worth doing from another machine. The compose file
publishes no database port, but a firewall rule or another project on the same
box can still expose one, and a config file describing an intention is not
evidence about the network.

---

## Updating

```bash
cd /opt/llmantis
git pull
docker compose -f docker-compose.prod.yml --env-file deploy/.env up -d --build
docker compose -f docker-compose.prod.yml --env-file deploy/.env exec app alembic upgrade head
```

Run the migration step every time. Someone else's merged commit may carry one.

---

## Why the site is behind a password

`frontend/impressum.html` and `frontend/datenschutz.html` are still structural
placeholders — 14 and 15 unfilled `{{TOKEN}}`s, and each page says so in its
own first paragraph. The site also carries a Preise page with 29 EUR and
199 EUR on it, which makes it a commercial offering and pulls in the Impressum
duty (§ 5 DDG) and the Art. 13 GDPR information duties.

Behind a password it is not a public offering and those duties do not bite.
This is also the defect our own product sells finding, so shipping it publicly
would be a poor look as well as a legal risk.

**Removing the password is one edit** — delete the `basic_auth` block in
`deploy/Caddyfile` — but do it only after Kwabena has filled both pages.

Read this before making that edit, because it is a larger change than it
looks. The password is currently the only thing standing in front of two
endpoints that authenticate nobody:

- `/api/art50check` (`backend/main.py:379`) fetches a caller-supplied URL
  server-side. No login, limited to 20 requests a minute per IP.
  `backend/netguard.py` refuses loopback, private, link-local and cloud
  metadata addresses — checked under glibc, which is what this image runs —
  but a guard is a narrower thing than not being reachable at all.
- `/api/scan` in `prompt` mode (`backend/main.py:865`) is anonymous on
  purpose; that is the free demo path. Each call makes roughly 21 real Mistral
  requests, and the limit is 5 a minute per IP. That is about 105 judge calls
  a minute spendable by anyone with a list of addresses, against a key whose
  free tier is 50 requests a minute in total.

Neither is a reason to keep the site private forever. Both are a reason to
decide what happens to them in the same change, instead of finding out after.

---

## What has not been tested

Everything above was exercised locally: the image builds, runs as uid 10001
with no `.env` inside it, serves every page, runs the migrations, and refuses a
loopback scan target with `ALLOW_PRIVATE_SCAN_TARGETS=false` (403, where the
development setting gives 200). `deploy/Caddyfile` passes `caddy validate` on
caddy:2.10-alpine.

**Not tested by anyone yet:** the certificate issue, the Basic-Auth prompt in a
real browser, and the whole thing on the actual Hetzner box. Those only happen
once, on the server, with the real domain.
