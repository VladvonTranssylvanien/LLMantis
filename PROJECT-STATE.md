# PROJECT-STATE — LLMantis

> Project memory. Update after every stage.
> Returning in a new chat: *"Continuing LLMantis. Read `~/LLMantis/PROJECT-STATE.md`."*
>
> Last updated: 15.08.2026 · Bogdan

---

## 1. Where we are

**Status:** week 1, track A (course submission in 7 days).

- ✅ Idea chosen and justified with market data (ECA Mapping 2025)
- ✅ Pitch deck written → Notion page (rename from PromptGuard to LLMantis)
- ✅ Repository with a working backend: FastAPI, 21 attacks, two-layer judging, scoring, HTML frontend, mock mode
- ✅ Playbook and role briefs written
- ✅ Repository renamed to `LLMantis` (Vlad, 15.08). GitHub keeps a redirect from the old name
- ✅ Playbook, role briefs and brand merged into the engine repository
- ✅ LICENSE added (AGPL-3.0)
- ✅ Brand mark drawn (`Brand/`) — wordmark still needs outlining
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
| 1 | 🔴 **Migrate the judge to Mistral** — confirmed in code: `backend/config.py:33` sets `JUDGE_MODEL` default to `claude-sonnet-4-5` (US provider). `TARGET_MODEL` on line 30 is the same, but that one only simulates a customer bot, so it is far less urgent. **Public repo, so this is publicly readable** | before the first paying customer | Vlad |
| 2 | Persistent database instead of in-memory state | week 2 | Vlad |
| 3 | Real ownership verification (DNS TXT) | week 4 | Vlad |
| 4 | Organizations in the data model | week 3 | Vlad |
| 5 | Attack library versioning | week 3 | Vlad |
| 6 | Rename the Notion page | this week | Bogdan |
| 8 | **Original illustrated mark** — the geometric mark is the brand and ships as final; an illustrated one may replace it. Owner: Bogdan, no date | open | Bogdan |
| 7 | **README §Scoring contradicts decision #8.** README documents the shipped behaviour — flat severity weights, critical cap at **D**. Prompt 3 / P0 specifies BASE + CONF_K multipliers and a cap at **C**. Update the README in the same commit as P0, or the repo documents two different scoring rules | with P0 | Vlad |

---

## 6. Deferred, with triggers

| What | Trigger to revisit |
|---|---|
| Business registration (Gewerbe) | before the first invoice |
| Gründungszuschuss | 🔴 **check NOW** if anyone is registered with the Agentur für Arbeit — the application goes in BEFORE Gewerbeanmeldung |
| Mollie, payments | when a customer is ready to pay |
| PDF export | after the course submission |
| Badge | after 10 customers |
| CI/CD integration | when a customer asks |
| Voice AI agents | year 2 |

---

## 7. Key numbers

| Metric | Value | State |
|---|---|---|
| Sites checked for the hypothesis | 0 of 24 | 🔴 blocks the pitch |
| Attacks in the library | 21 of 75 | 🟠 |
| Test bots | 0 of 3 | 🔴 |
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

**Open API request (not implemented — frontend must not add backend fields):**
the Prüfbericht wants an **attack-library version** on page 1. The report shows
"not reported by the backend" until `report.attack_library_version` exists.
