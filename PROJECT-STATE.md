# PROJECT-STATE — LLMantis

> Project memory. Update after every stage.
> Returning in a new chat: *"Continuing LLMantis. Read `~/LLMantis/PROJECT-STATE.md`."*
>
> Last updated: 16.08.2026 · Vlad (session with Claude Code)

---

## 1. Where we are

**Status:** week 1, track A (course submission in 7 days) — **backend/API work for
Vlad's implementation plan is functionally complete** (P0 + P1 + the P2 items
that don't need a registered company), **including authentication**. Remaining
gaps are frontend UI for the newer endpoints (a deliberate choice — Bogdan owns
that next) and the 21→75 attack library.

- ✅ Idea chosen and justified with market data (ECA Mapping 2025)
- ✅ Pitch deck written → Notion page (rename from PromptGuard to LLMantis)
- ✅ Repository with a working backend: FastAPI, 21 attacks, two-layer judging, scoring, HTML frontend, mock mode
- ✅ Playbook and role briefs written
- ✅ Repository renamed to `LLMantis` (Vlad, 15.08). GitHub keeps a redirect from the old name
- ✅ Playbook, role briefs and brand merged into the engine repository
- ✅ LICENSE added (AGPL-3.0)
- ✅ Brand mark drawn (`Brand/`) — wordmark still needs outlining
- ✅ **Judge migrated to Mistral** — no US provider anywhere in the stack (16.08)
- ✅ **Postgres database** — organizations, targets, scans, results, ownership
  verifications, memberships, API keys, branding. Alembic migrations (16.08)
- ✅ **Real DNS ownership verification**, gating active (`mode="api"`) scans (16.08)
- ✅ **Organizations, API keys, white-label branding** — implemented and
  tested via curl; no frontend yet (16.08)
- ✅ **Art.-50-Check** — free passive layer, its own page, SSRF-guarded, tested
  against real sites (16.08)
- ✅ **Rate limiting** (`slowapi`, per IP) on every write endpoint (16.08)
- ✅ **Security pass done** (16.08): no secrets in git history or code, no
  SQL injection, no XSS, SSRF fixed, `requirements.txt` fixed (was missing
  sqlalchemy/alembic/psycopg/dnspython — a fresh clone would not have started)
- ✅ **Authentication** (16.08) — `User` table, bcrypt + JWT, every org-scoped
  endpoint requires membership. The free anonymous scan path is untouched
- ⬜ Hypothesis tested on 24 sites ← **blocks the pitch**
- ⬜ Name cleared at DPMA/EUIPO
- ⬜ Legal map from Kwabena

**Repository:** `github.com/VladvonTranssylvanien/LLMantis` (renamed 15.08; old URL redirects)
**Visibility:** public, deliberately — see decision #11. Assume every word here is world-readable.

---

## 2. Key decisions and their reasoning

| # | Decision | Why | Date |
|---|---|---|---|
| 1 | Niche: AI Security & Integrity | 7 of 828 companies in the European map (0.8%). Emptiest segment | 14.08 |
| 2 | Black box (DAST), not code analysis | Separates us from the Codeargus project (SAST); different buyer, different method | 14.08 |
| 3 | Name: LLMantis | Exact string free. `Mantis` is taken in security — always write as one word | 15.08 |
| 4 | Market: Germany → EU | Lets us reuse the CodeArgus groundwork | 15.08 |
| 5 | **Two product layers** | Passive Art.-50-Check without permission (funnel) + active red team with ownership verification (revenue). Solves the legal problem | 15.08 |
| 6 | **Prüfbericht, not Zertifikat** | AI Act certificates come only from notified bodies, and only for high-risk. "Zertifiziert" = § 5 UWG | 15.08 |
| 7 | **Judge on Mistral, not OpenAI/Anthropic** | The judge processes customer system prompts = trade secrets. US CLOUD Act contradicts what we sell | 15.08 |
| 8 | Three `confidence` levels + mandatory `evidence` | A `possible` finding as fact in a paid report = § 5 UWG | 15.08 |
| 9 | Canary strings in system prompts | Turns a judge's opinion into a deterministic fact. Only `confirmed` may produce an F | 15.08 |
| 10 | **Working language: English** | Code, comments, commits, docs, UI — all English | 15.08 |
| 11 | **Repository stays public** | Research project; openness works for us at this stage. A deliberate decision, **not** tech debt — do not "fix" it | 15.08 |
| 13 | **Brand: the geometric mark is the brand** | Original geometry, ours, vector, favicon-safe. A candidate mark was rejected — derived from licensed stock, not sub-licensable | 15.08 |
| 14 | **Landing copy in German** | The buyer is a German compliance manager; the app and the Prüfbericht stay English. Documented exception to decision #10 | 15.08 |
| 12 | **Licence: AGPL-3.0** | Repo is public and the product is a hosted service. Under AGPL a competitor who hosts our code must publish their changes; under MIT they need not. Agreed with Vlad as repo owner | 15.08 |

---

## 3. Verified facts (with sources)

| Fact | Source | Verified |
|---|---|---|
| AI Security & Integrity — 7 of 828 companies (0.8%) | ECA European Cybersecurity Mapping 2025 | ✅ 15.08 |
| 51.4% of European companies sit in 3 segments (Threat Mgmt 152, Cloud 145, IAM 129) | same | ✅ 15.08 |
| **AI Act Art. 50 in force since 02.08.2026** | Regulation (EU) 2024/1689 | ✅ 15.08 |
| **Digital Omnibus delayed high-risk, but NOT Art. 50** | several law firms | ⚠️ needs a primary source — Kwabena |
| Art. 50 penalty: up to €15M or 3% of worldwide turnover | AI Act Art. 99 | ✅ 15.08 |
| Air Canada — BC tribunal, Feb 2024, company liable for its bot's statements | CBC, Forbes | ✅ 15.08 |
| Conformity certificates come only from notified bodies, and only for high-risk | AI Act Art. 29, 43 | ✅ 15.08 |
| **No legal obligation exists to red-team a chatbot** | absence of a norm | ⚠️ confirm — Kwabena |

---

## 4. Corrected mistakes — do not repeat

| Was | Correct |
|---|---|
| "AI Security — 6 companies" | **7** (6 start-ups + 1 scale-up). 6 is start-ups only |
| "IAM — 130" | **129** |
| "Code Checking — 11" | **12** |
| "The AI Act was delayed" | High-risk was delayed. **Art. 50 was not** |
| "We certify the bot" | We issue a **Prüfbericht**. Certification is legally impossible here |

---

## 5. Technical debt

| # | What | Due | Who |
|---|---|---|---|
| 1 | ✅ **DONE 16.08** ~~Migrate the judge to Mistral~~ — `backend/llm.py` talks only to Mistral. No US provider anywhere; `anthropic` removed from `requirements.txt` too | ~~before the first paying customer~~ | Vlad |
| 2 | ✅ **DONE 16.08** ~~Persistent database instead of in-memory state~~ — Postgres + Alembic, every scan/org/result survives a restart | ~~week 2~~ | Vlad |
| 3 | ✅ **DONE 16.08** ~~Real ownership verification (DNS TXT)~~ — gates every `mode="api"` scan; 90-day re-verification | ~~week 4~~ | Vlad |
| 4 | ✅ **DONE 16.08** ~~Organizations in the data model~~ — plus a `Membership` table (user_id, org_id, role), unused until auth exists | ~~week 3~~ | Vlad |
| 5 | ✅ **DONE 16.08** ~~Attack library versioning~~ — `attacks.yaml` has `version: "1.4"`, shows up in every scan report and the Pruefbericht | ~~week 3~~ | Vlad |
| 6 | Rename the Notion page | this week | Bogdan |
| 8 | **Original illustrated mark** — the geometric mark is the brand and ships as final; an illustrated one may replace it. Owner: Bogdan, no date | open | Bogdan |
| 7 | ✅ **RESOLVED** (verified 16.08) ~~README §Scoring contradicts decision #8~~ — `backend/scoring.py` caps at **C** and applies `CONFIDENCE_WEIGHT` multipliers (confirmed/likely/possible), matching README and decision #8. No contradiction found; this must have been fixed during the P0 confidence-levels work | ~~with P0~~ | Vlad |
| 9 | ✅ **DONE 16.08** ~~No authentication layer~~ — `POST/GET /api/auth/{register,login,me}` (bcrypt + JWT bearer tokens), every org-scoped endpoint now calls `require_membership()`. `mode="prompt"` scans with no `org_id` and no `X-API-Key` stay fully anonymous on purpose — that's the free demo path and it never touches a live third-party system. Anything that acts *as* an organization (creating one, minting a key, reading scan history, verifying ownership, `mode="api"` or `mode="prompt"` with an `org_id`) now requires a valid token and membership | ~~before any non-localhost deployment~~ | Vlad |
| 10 | Frontend for organizations, API keys, branding and ownership verification — all four work today via curl only. `index.html` and `art50check.html` are the only pages with a UI | after auth (building a UI for endpoints anyone can call as anyone else is wasted work) | Frontend |
| 11 | 21 → 75 attacks in `attacks/attacks.yaml` (5 categories × 15) | with Gregor | Attack Engineer |

---

## 6. Deferred, with triggers

| What | Trigger to revisit |
|---|---|
| Business registration (Gewerbe) | before the first invoice |
| Gründungszuschuss | 🔴 **check NOW** if anyone is registered with the Agentur für Arbeit — the application goes in BEFORE Gewerbeanmeldung |
| Mollie, payments | when the Gewerbe is registered — team decided 16.08 not to build even the schema until then |
| ~~PDF export~~ | ✅ **done 16.08** — client-side print via `frontend/report.html`, no backend needed |
| Badge | after 10 customers |
| CI/CD integration | when there is a Hetzner server to deploy to |
| Voice AI agents | year 2 |

---

## 7. Key numbers

| Metric | Value | State |
|---|---|---|
| Sites checked for the hypothesis | 0 of 24 | 🔴 blocks the pitch |
| Attacks in the library | 21 of 75 | 🟠 |
| Test bots | 3 of 3 | ✅ `demo/targets.yaml` — unprotected, hardened, MediClinic |
| Calibration set | 0 of 30 | 🔴 |
| Judge agreement with human labels | not measured | 🔴 |
| Paid reports per month (**north star**) | 0 | — |

---

## 8. Log

**14.08.2026** — Analysed the ECA Mapping. Chose the AI Security niche. Three
ideas generated, PromptGuard selected. Pitch deck written into Notion.

**15.08.2026** — Resolved the Codeargus overlap (DAST vs SAST). Corrected the
segment numbers. Name → LLMantis. Wrote the PLAYBOOK and three role briefs.
Found the key fact: AI Act Art. 50 has been in force since 02.08.2026 and was
not postponed. Decided: Prüfbericht instead of Zertifikat; Mistral instead of a
US model; two product layers. Switched the project's working language to English.

**15.08.2026 (later)** — Merged the coordination documents, role briefs and the
brand into the engine repository; one repo from here. Added AGPL-3.0. Decided
the repository stays public on purpose (#11). Drew the mantis-head mark from
scratch — the supplied reference was watermarked stock art and was not traced.
Confirmed tech debt #1 against the source rather than the note: the judge model
defaults to a US provider at `backend/config.py:33`.

**Open, needs a decision:** the wordmark is still a live `<text>` element in the
lockup SVGs and renders in a fallback face on any machine without Inter. It must
be converted to outlines before anything goes in front of a customer.

**15.08.2026 (frontend)** — Redesigned all three pages on the geometric mark.
Self-hosted Inter and JetBrains Mono; the pages now make zero external requests,
verified by rendering with every non-localhost host blackholed. Contrast on the
Prüfbericht raised to AA. Landing rebuilt in German with navigation, a labelled
illustration of the scan pipeline, the GRC section and pricing. Impressum and
Datenschutz exist as structural placeholders with `{{TOKEN}}` fields — Kwabena
owns the wording.

**16.08.2026** — Full backend session (Vlad, with Claude Code). Completed the
rest of Vlad's implementation plan and closed out P1/P2 up to what the team
decided to defer:

- Migrated the judge fully to Mistral (removed all Anthropic code and the
  `anthropic` dependency — tech debt #1, closed)
- Postgres + Alembic: organizations, targets, scans, results, ownership
  verifications, `Membership` (schema-only, unused until auth), `ApiKey`,
  `Branding` — tech debt #2 and #4, closed
- Real DNS TXT ownership verification, wired as a hard gate in front of every
  `mode="api"` scan — tech debt #3, closed
- Attack library versioning (`attacks.yaml` → `version: "1.4"`), now shown
  correctly in the Prüfbericht — tech debt #5, closed; also fixed the report
  page reading the wrong field name (`attack_library_version` vs the API's
  actual `library_version`) and a missing `target_name`, both of which made
  every printed report show placeholders instead of the real scan
- API keys (`POST/GET/DELETE /api/keys`) for CI/CD-style programmatic access,
  and white-label branding (`PUT/GET /api/organizations/{id}/branding`) for
  the agency tier — both P2 items, both tested
- Free Art.-50-Check got its own page (`frontend/art50check.html`), wired to
  the pricing card that used to link nowhere; verified against real sites
  (otto.de missing AI disclosure, zendesk.com clean, wikipedia.org no widget)
- **Security pass:** git history and current code clean of secrets; no SQL
  injection (ORM everywhere) or XSS (escaped consistently on all 3 frontend
  pages); found and fixed a real SSRF hole in Art.-50-Check (it fetched any
  caller-supplied URL server-side with no guard — blocked private/loopback/
  link-local/metadata-endpoint addresses, re-checked on every redirect hop);
  found and fixed `requirements.txt` missing sqlalchemy/alembic/psycopg/
  dnspython (a fresh clone would not have started) and a stale `anthropic`
  entry; added per-IP rate limiting (`slowapi`) since `/api/scan` makes ~21
  real Mistral calls and had zero cost protection
- **Found, not fixed (team decision pending):** no authentication anywhere —
  any caller can create organizations, mint API keys for any `org_id`, and
  read any scan's results, including the confidential `evidence` quotes a
  scan captured. Fine for a localhost PoC, not fine for anything else. See
  technical debt #9. Do not deploy this server beyond localhost until the
  team has decided an approach and it is built.
- Rewrote the stale parts of `README.md` (Status/Project structure/API table/
  Who-does-what all predated the database entirely) and `SECRETS.md` (still
  told people to get an Anthropic key)

**What's left of Vlad's plan:** frontend for organizations/API keys/branding/
ownership (tech debt #10, Bogdan's), 21→75 attacks (#11, Gregor's side), then
Mollie billing and CI/CD — both intentionally deferred until the Gewerbe is
registered.

**16.08.2026 (later) — Authentication.** Team decided to build it rather than
wait, and to leave the frontend for it to Bogdan. Closed technical debt #9:

- New `User` table (email, password_hash, bcrypt) and `backend/auth.py`:
  `POST /api/auth/register`, `POST /api/auth/login` (both rate-limited),
  `GET /api/auth/me`. Sessions are JWT bearer tokens (`Authorization: Bearer
  <token>`), not cookies — the frontend is fetch()-based already, and a
  bearer token sidesteps CSRF entirely since the browser never sends it
  automatically. `JWT_SECRET` in `.env`; if unset the app generates a random
  one at startup and logs everyone out on every restart, on purpose — a
  deliberately annoying default so a real secret gets set before this is
  mistaken for production-ready.
- `Membership` (built earlier today, unused until now) is the authorization
  source of truth: `require_membership(db, user, org_id)` raises 403 if the
  caller isn't a member. Wired into every org-scoped endpoint — creating an
  org (creator becomes owner automatically), listing/reading orgs, branding,
  ownership challenge/verify, and — the one that mattered most — issuing,
  listing and revoking API keys. **This closes the exact hole found in this
  morning's security pass:** anyone could mint a working API key for any
  `org_id` with zero proof of ownership. Verified live with two accounts: an
  "attacker" cannot create a key for the "victim" org (403), the real owner
  can (200) for their own.
- `GET /api/scans` and `/api/scans/{id}` now scope to the caller's orgs
  instead of returning every scan in the system (including the confidential
  `evidence` a scan captured). A scan belonging to someone else's org 404s,
  not 403s, so probing scan ids can't distinguish "not yours" from "doesn't
  exist".
- **The free demo path is untouched on purpose:** `POST /api/scan` with
  `mode="prompt"` and no `org_id` and no `X-API-Key` still needs no login at
  all — that's the course-pitch demo, and it only ever replays text the
  caller submitted themselves, never a live third-party system. `org_id` in
  the body is now honoured only for a logged-in member of that org; an
  `X-API-Key` still works exactly as before (the key itself is already proof
  of the org, no separate login needed on top of it) — verified both paths
  still work end to end after the change.
- Verified with 13 separate checks (register/login/me, org creation with and
  without login, the API-key mint attack across two accounts, anonymous scan,
  scan with org_id unauthenticated/non-member/owner, scan history scoping,
  the API-key scan path) before calling this done.

**Frontend for all of this — organizations, API keys, branding, ownership,
login/register — is Bogdan's, not built here.** The API is ready for it.
