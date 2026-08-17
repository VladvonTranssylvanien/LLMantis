# Deploying LLMantis

One Hetzner box, three containers: Caddy in front, the app, Postgres behind.
Only Caddy publishes a port.

Everything below was run against the real images before it was written down.
Where a step is untested on the server itself, it says so.

> ## 🔴 Read this first: our box is not the box this describes
>
> Everything after this box assumes an **empty server**, which is how it was
> written and how it was tested. The machine LLMantis actually runs on is not
> empty, so **sections 1, 2 and 4 do not apply to it.** For that machine, read
> [the section at the bottom](#how-llmantisde-is-actually-deployed) instead.
>
> The generic instructions are kept because they are correct for a fresh box,
> and because the day this moves to its own server they are what you want.

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

**Since 17.08 this is out of date in one direction and still true in another.**
The certificate did issue, and the stack does run on the real box — see the
last section for what was measured there. What nobody has done yet:

- opened the site in a real browser and met the Basic-Auth prompt. Every check
  so far was `curl`
- run this on an **empty** server, which is what sections 1-4 describe. Our box
  was not empty, so those sections have never been executed as written
- checked the ports from another machine. The compose file publishes none for
  the database and `docker ps` agrees, but that is a config file describing an
  intention, not evidence about the network

---

## How llmantis.de is actually deployed

Written 17.08 immediately after doing it, because none of it is derivable from
this repository.

### The box was already occupied

`llmantis.de` runs on a Hetzner box that **already hosted another project**:
a Caddy container in `/srv` that also serves `phishing.workshop.bogdanorel.de`.
It holds ports 80 and 443.

That single fact invalidates section 4 above. Starting our own Caddy from
`docker-compose.prod.yml` would have fought for those ports and taken the
workshop site down with it. So on this machine:

- **only `postgres` and `app` are started** from our compose file
- the **existing** Caddy in `/srv` is the front, and gets one extra site block
- our `app` joins that Caddy's network so it can be proxied to

```
/srv/docker-compose.yml       the pre-existing Caddy (not ours, do not replace)
/srv/caddy/Caddyfile          its config — our site block was appended
/srv/homepage/                the coming-soon page and the workshop site
/srv/llmantis/                this repository, cloned
/srv/secrets/                 credentials, deliberately OUTSIDE the git tree
```

### What makes it work

`/srv/llmantis/docker-compose.override.yml` — server-local, and ignored by
`.gitignore` on purpose:

```yaml
services:
  app:
    networks: [default, web]
networks:
  web:
    external: true
    name: srv_default        # the network the existing Caddy stack owns
```

Started with both files, and **naming the two services explicitly** so the
caddy service in `docker-compose.prod.yml` never starts:

```bash
cd /srv/llmantis
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml \
  --env-file deploy/.env up -d --build postgres app
```

The block appended to `/srv/caddy/Caddyfile`:

```
llmantis.de, www.llmantis.de {
	basic_auth {
		orel <bcrypt hash>
	}
	header {
		X-Robots-Tag "noindex, nofollow, noarchive"
		-Server
	}
	reverse_proxy llmantis-app-1:8000
}
```

`llmantis-app-1` is the container name Compose derives from the directory
(`/srv/llmantis`) plus the service name. If the directory is ever renamed, this
proxy target breaks.

### Deploying a change

```bash
ssh orel@37.27.250.224
cd /srv/llmantis && git pull --ff-only
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml \
  --env-file deploy/.env up -d --build app
# only when a migration landed:
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml \
  --env-file deploy/.env exec app alembic upgrade head
```

Touching the Caddyfile needs a validate first and a reload after — a reload
does not interrupt the workshop site, a restart would:

```bash
docker exec srv-caddy-1 caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker exec srv-caddy-1 caddy reload  --config /etc/caddy/Caddyfile --adapter caddyfile
```

### Credentials

All of it was generated **on the server** and never left it. The site login is
in `/srv/secrets/llmantis-basic-auth.txt`, mode 600.

`/srv/secrets/` is outside the git work tree deliberately. The first attempt
put those files in `/srv/llmantis/deploy/`, inside a clone of a **public**
repository, where `git status` listed them as untracked and one `git add -A`
away from being published. Untracked is not ignored.

### After any deploy, check the neighbour

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://phishing.workshop.bogdanorel.de/
```

Our changes share a web server with someone else's live site. A 200 there is
part of "the deploy worked", not a separate concern.

### Verified on the live domain, 17.08

```
https://llmantis.de/            401 without credentials, 200 with
http://llmantis.de/             308 to https
X-Robots-Tag                    noindex, nofollow, noarchive; no Server header
container ports                 app 8000/tcp, postgres 5432/tcp — no host binding
migrations                      9 on an empty database, alembic check clean
a real scan through the domain  C/81, library 2.0, grade issued, 131s
workshop site                   still 200
```
