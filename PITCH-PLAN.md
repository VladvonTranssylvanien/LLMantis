# PITCH-PLAN — LLMantis

> Owner: Bogdan. Two plans in one file: **what we say on stage**, and **what we
> must finish before we can say it**.
>
> Format: 10–15 minutes · live demo from the stage · audience is the course jury,
> but the narrative is pitched as if to a customer.
> Deadline: **21.08.2026** (course submission). Written 17.08 — four days.

---

## Part 0 — the one sentence

> **"Your chatbot speaks for your company. Nobody has ever checked what it says
> under pressure. We attack it, and we hand you the proof that you looked."**

Everything on stage serves that sentence. If a slide does not, cut it.

---

## Part 1 — the pitch, slide by slide

Timings are the budget, not a suggestion. Total 12:00, leaving 3:00 of air in a
15-minute slot for questions and for a demo that runs slow.

### 1. The hook — a bot that cost its company money (1:30)

Open with the Air Canada case, not with us. A customer asked the airline's
chatbot about bereavement fares. The bot invented a refund policy. The customer
sued, and in February 2024 the BC tribunal held **the airline** liable for what
its bot said — the "the chatbot is a separate entity" defence was rejected
explicitly.

Then the legal turn:

- **AI Act Art. 50 has been in force since 02.08.2026** — a person must be told
  they are talking to a machine.
- The Digital Omnibus delayed the high-risk obligations. **It did not delay Art. 50.**
- Penalty ceiling: **up to €15M or 3 % of worldwide turnover** (Art. 99).

Land on the question, in the customer's words: *"Ihr Chatbot spricht für Sie.
Wer hat ihn geprüft?"*

> Source discipline: every number above is in `PROJECT-STATE.md` §3 with its
> source. The two rows marked ⚠️ there (Omnibus scope, "no obligation to
> red-team") are **not** to be stated as fact on stage until Kwabena confirms
> them against a primary source. See Part 2, item T1-6.

### 2. Why nobody is solving this (1:00)

From the ECA European Cybersecurity Mapping 2025:

- **AI Security & Integrity: 7 companies out of 828 — 0.8 %.** The emptiest
  segment on the map.
- Meanwhile **51.4 % of European vendors** crowd into three segments (Threat
  Management 152, Cloud 145, IAM 129).

The point for the jury: this is not a crowded market with a new logo. It is an
empty square on a published map, next to a regulation that came into force
fifteen days ago.

### 3. What we deliberately do NOT sell (0:45)

Put this early. With a German compliance buyer it buys more trust than any
feature, and it inoculates the whole pitch against the obvious objection.

- We **cannot** certify, and neither can anybody else at this layer:
  conformity certificates come only from **notified bodies**, and only for
  **high-risk** systems (AI Act Art. 29, 43).
- Calling a report a *Zertifikat* or writing *AI-Act-konform* would be a
  **§ 5 UWG** problem — misleading commercial practice.
- So we issue a **Prüfbericht**: not compliance, but **Nachweis der Sorgfalt** —
  documented evidence that you looked, dated, reproducible, with the attack
  library version stamped on it.

One line to say out loud: *"Wir verkaufen kein Zertifikat. Wir verkaufen den
Nachweis, dass Sie hingesehen haben."*

### 4. The product in one picture (1:30)

Two layers, and the reason they are two:

| Layer | What it does | Permission needed | Role |
|---|---|---|---|
| **Art.-50-Check** | Passive. Reads a public page, checks whether the AI disclosure Art. 50 requires is actually there | **None** — we only read what any visitor reads | Free. The funnel |
| **Red-Team-Prüfung** | Active. Drives real attacks at the bot, judges the answers, issues the Prüfbericht | **DNS TXT proof of ownership**, hard-gated | Paid. The revenue |

Say why the split exists: attacking a bot you do not own is not a product, it is
an offence. The free layer needs no permission because it reads a public page —
so it can run on a prospect's site before any conversation exists.

### 5. LIVE DEMO — the centre of the pitch (4:00)

**The demo is a contrast, not a feature tour.** Two bots, the same scan, two
grades. Choreography:

| # | Beat | On screen | Time |
|---|---|---|---|
| 1 | "This is a normal support bot. Here is its system prompt." | Bot A prompt, canary visible | 0:30 |
| 2 | "We run the library against it." | Scan starts, attacks stream in | 0:20 |
| 3 | Wait — narrate the pipeline while it runs | attacks → bot → judge → score | 0:40 |
| 4 | **The money shot.** "It printed its own secret. Here is the exact quote." | The `confirmed` canary finding with its evidence quote | 0:50 |
| 5 | Grade: **D**. "This is a bot in production somewhere today." | Score card | 0:20 |
| 6 | "Same library. Hardened bot." | Bot B scan | 0:40 |
| 7 | Grade: **A**. "Same attacks. The difference is the prompt." | Side-by-side | 0:20 |
| 8 | The deliverable | `report.html` print view — the Prüfbericht | 0:40 |

**Demo runs on `attacks_short.yaml` (21 attacks), and this is a measured
decision, not caution:**

- 21 attacks ≈ **21 s** per scan. 78 attacks ≈ **96 s** — three of those minutes
  on stage are dead air, and the pace degrades (20 attacks in 13 s, 40 in 29 s,
  60 in 86 s — that is Mistral backoff engaging).
- The 78-attack set makes the **vulnerable bot look better**: same bot, same
  prompt, D/52 → **C/80**, because 57 attacks it passes dilute the result. The
  contrast that carries the demo collapses from 48 points to 20.
- The free Mistral tier is 50 requests/minute. A 78-attack scan needs ~121.
  Running two of them back to back on stage is a coin flip.

**Between the two scans, leave ≥ 60 s of talking.** That is the quota window,
and slide 6 fills it exactly.

### 6. Why the verdict is defensible (2:00)

This is the slide the jury is actually grading. Three mechanisms, each stated as
a rule we can be held to:

1. **A canary makes the worst finding deterministic.** We plant a unique string
   in the system prompt. Layer 1 is a string comparison, not an opinion —
   if that string appears in the bot's answer, the leak is a fact.
   **Only a `confirmed` finding can produce an F.**
2. **No quote, no finding.** Every finding carries the bot's own words as
   evidence. A model's opinion with nothing to point at does not enter the
   report — an unproven claim in a paid report is § 5 UWG again.
3. **Three confidence levels**, and the judge may never award itself
   `confirmed`. It was caught doing exactly that during integration and capped.

Then the number that closes the Q&A before it opens: **judge agreement with
human labels on the 30-item calibration set** — see Part 2, item T0-2. Say the
false-positive count out loud, and say that a false positive is the one that
matters, because inventing a vulnerability in a paid report is worse than
missing one.

### 7. Business (1:30)

- **Buyer:** German SMB running a customer-facing chatbot — the compliance
  manager or the managing director, not the developer.
- **Why now:** Art. 50 in force since 02.08.2026, and the first thing an
  authority or a plaintiff asks for is evidence of diligence.
- **Pricing:** the two live tiers on the site.
- **Funnel mechanics:** the free Art.-50-Check runs without asking anyone. Every
  German site that fails it is a named, evidenced lead.

Bring the hypothesis number here — see Part 2, item T0-3. *"We checked 24 real
German business sites. N of them are missing the disclosure Art. 50 requires."*
That single sentence is the strongest thing in the pitch, and today we do not
have it.

### 8. Where we are, honestly, and what is next (1:00)

Show a real status slide. With a jury that grades method, admitting the gaps is
worth more than hiding them — and every gap here is already measured:

- Live at `llmantis.de`, password-gated on purpose: Impressum and Datenschutz
  are still templates and the pricing page would make it a commercial offer.
- Scoring dilution is a known open question, with numbers.
- Calibration measured on 30 items; the judge agreement number is X %.
- Not built: billing, customer-facing UI for the org/API-key layer.

End on the ask (whatever it is for this audience: feedback, a pilot customer, a
grade).

---

## Part 2 — what must be finished before the pitch

Ordered by *what breaks on stage without it*. Four days. Anything not in Tier 0
or Tier 1 is explicitly deferred in Tier 2 — that list is part of the plan, not
an omission.

### Tier 0 — the pitch has a hole without these

| # | Task | Why it breaks the pitch | Owner | Est. |
|---|---|---|---|---|
✅| **T0-1** | **Run `calibration/calibrate.py` and record the number.** The set is ready: 30 items, **all 30 human-labelled** (18 pass / 12 fail). `PROJECT-STATE.md` still says "0 of 30 🔴" — the document is behind the repo | Slide 6 ends on this number, and *"what if the judge is wrong?"* is the sharpest question in Q&A. One command turns a reassurance into a measurement. **Highest value per minute in this whole plan.** If `confirmed` disagreements are not zero, we have a real defect and four days to find out | Gregor / Vlad | 30 min |
| **T0-2** | **Art.-50-Check against the 24 German sites.** Currently **0 of 24** | Slide 7's strongest sentence does not exist. And 0 of 24 is not a market finding — it is far more likely a broken checker, exactly as it turned out to be in CodeArgus. Either outcome must be known before the stage, not discovered on it | Bogdan | 2–3 h |
✅| **T0-3** | **Decide the scoring dilution (tech debt #15).** A bot with three confirmed critical leaks scores 80 | A juror asks *"what does 80 mean?"* and we have no answer. Minimum viable resolution: demo on the 21-attack set (contrast 48 points) **and** a prepared sentence about what we measured. Changing the formula four days out is the riskier option — decide, do not drift | Team, Bogdan has the numbers | 1 h decision |
| **T0-4** | **Full demo rehearsal, end to end, on the presentation machine.** Both bots, both scans, the report page, with a stopwatch | Every failure this project has had came from testing pieces and not the assembly — the image was fine, Caddy was fine, and the first full stack start still failed on `container_name`. A demo is an assembly | Bogdan | 1 h |
| **T0-5** | **Open `llmantis.de` in a real browser.** Every check so far has been `curl` | The cheapest unverified thing we own. `curl` returns 401 and proves the gate works; it proves nothing about what a human sees | Bogdan | 10 min |
| **T0-6** | **Kwabena confirms or removes the two ⚠️ claims** in `PROJECT-STATE.md` §3: Omnibus scope, and "no legal obligation to red-team exists" | Both are load-bearing on slides 1 and 3. An unsourced legal claim in front of a jury is the one kind of error that discredits everything said around it | Kwabena | — |

### Tier 1 — makes it look like a product instead of a project

| # | Task | Why | Owner | Est. |
|---|---|---|---|---|
| **T1-1** | **Landing design pass** — nav, hero, pipeline illustration, pricing, GRC section, team | Bogdan's own call and he is doing it himself. What the pitch needs the landing to carry: the two-layer split (slide 4), the Prüfbericht-not-Zertifikat line (slide 3), and one visible piece of evidence. Everything else is decoration | Bogdan | — |
| **T1-2** | **`summary.total` counts only PASS+FAIL** — the 78-attack scan reports 74 while 78 ran | A number on screen that does not add up, in front of a jury, in a product whose entire selling point is honest measurement | Vlad | 30 min |
| **T1-3** | **Either fill `excessive_agency` or do not show the per-category breakdown.** It has 5 attacks against 15–21 in the others, and on the 17.08 run three errored, leaving the category resting on **2 scored attacks out of 78** | If a per-category chart is on screen, that column is a question we cannot answer well. Cheapest fix is not showing it | Gregor | 1 h or 0 |
| **T1-4** | **Rename the demo library wiring** so `attacks_short.yaml` is what a demo scan uses by default | Removes a manual step from the most fragile four minutes of the pitch | Vlad | 20 min |
| **T1-5** | **`/.well-known/security.txt` returns 404** while the landing links to it | Small, but a security product with a dead security link is the kind of detail this audience notices | Bogdan | 10 min |
| **T1-6** | **Update `PROJECT-STATE.md` §7 key numbers** — calibration set, sites checked, library size | It is the document the team and the jury read as the source of truth, and it is currently wrong in at least one row we already fixed | Bogdan | 15 min |
| **T1-7** | **Prepare the recorded demo as a fallback** even though we are going live | Costs one recording. Removes the only single point of failure in the entire pitch (Mistral 429, venue wifi, laptop) | Bogdan | 30 min |

### Tier 2 — deliberately NOT before the pitch

Listing these is the point. Four days is enough to ruin the pitch by building
the wrong thing.

| What | Why not now |
|---|---|
| **Frontend for orgs / API keys / branding / ownership** (tech debt #10, 18 endpoints) | The demo never touches them. This is the single biggest sink available and it buys nothing on stage. After the pitch |
| **Growing the attack library past 78** (tech debt #11) | Already measured to make the vulnerable bot score *better*. **Freeze the library until T0-3 is decided** |
| **Paid Mistral plan** | Only needed for 78-attack live scans. The demo runs 21. Revisit when the library question is settled |
| **Removing Basic-Auth from the live site** | Requires Impressum + Datenschutz (Kwabena), and unblocks the DNS-rebinding exposure in tech debt #14. Nothing about the pitch needs the site public — show it from the presenting machine |
| **DNS-rebinding fix (#14)** | Not reachable while the site is password-gated. The trigger is removing the password, and we are not removing it |
| **Basic-Auth CPU amplification (#13)** | Already accepted with measurements. The trigger is advertising a gated site, which the pitch does not do |
| **Billing, email verification, Gewerbe** | All already deferred with triggers in `PROJECT-STATE.md` §6. Nothing changed |

---

## Part 3 — Q&A preparation

The honest answer is the strong answer with this audience. Every one of these
has a measurement or a mechanism behind it.

| Question | Answer |
|---|---|
| *"What if the judge is wrong?"* | We measured it: N of 30 agreement on a human-labelled set, with false positives counted separately because inventing a vulnerability is worse than missing one. And the worst grade we issue can only come from a deterministic string match, never from the model's opinion |
| *"Is this a certificate?"* | No, and it legally cannot be — certificates come from notified bodies, high-risk only. We issue a Prüfbericht: evidence of diligence. Anyone selling you an "AI Act certificate" for a chatbot is selling you a § 5 UWG problem |
| *"Can an AI judge another AI?"* | For the finding that matters most, no AI is involved: a planted canary string either appears in the answer or it does not. The model only handles the softer categories, capped at `likely`, and never without a quote |
| *"Where does our data go?"* | The judge reads system prompts, which are trade secrets, so what we can be held to is how they are handled: retention, who may read them, and the "delete after scan" option. We make no claim about which country the model runs in — the EU-only stack was dropped on 18.08 |
| *"How is this different from a normal pentest?"* | A normal pentest attacks code. The attack surface here is language: the exploit is a sentence, and the same bot can answer differently to the same sentence twice. That is why it needs a library and a judge, not a scanner |
| *"What if my bot passes everything?"* | Then you have exactly what you are buying — a dated, reproducible Prüfbericht saying so, with the library version stamped on it. That is the deliverable, not the vulnerability |
| *"Why pay if the check is free?"* | The free check reads your page and asks whether you disclosed the bot. The paid one asks what the bot does when someone actually tries |
| *"Your score is 80 for a bot with three critical leaks — explain."* | (Only if T0-3 is unresolved.) Answer with the measurement: score is passed-weight over total-weight, a bigger library dilutes it, the critical cap is what holds that bot at C, and we consider the raw number an open design question. Never bluff this one — the numbers are in the repo |

---

## Part 4 — day plan, 17.08 → 21.08

| Day | Bogdan | Vlad | Gregor | Kwabena |
|---|---|---|---|---|
| **17.08** | T0-2 (Art.-50 on 24 sites), T0-5 | T1-2, T1-4 | **T0-1 (calibration) — do this first** | T0-6 |
| **18.08** | Landing design (T1-1) | T0-3 input | T1-3 decision | legal text |
| **19.08** | Slides 1–4, T1-6 | — | — | — |
| **20.08** | Slides 5–8, T1-7 (recording) | — | — | — |
| **21.08** | **T0-4 full rehearsal**, buffer | on call | on call | — |

**T0-1 first, on day one.** It is 30 minutes, and if the calibration number is
bad, it is the only finding in this list that changes what we are allowed to say
on stage.

---

## Related

- `PROJECT-STATE.md` — decisions, verified facts, technical debt
- `PLAYBOOK.md` — the rules the product is built on
- `calibration/README.md` — what the agreement number means and what invalidates it
- `deploy/README.md` — the server runbook
