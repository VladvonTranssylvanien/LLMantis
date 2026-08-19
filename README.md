# LLMantis

**A penetration test for AI chatbots.**

Your chatbot speaks for your company. Nobody has ever checked what it says under
pressure.

LLMantis connects to a chatbot, runs a library of documented attacks against it,
has a separate judge model rule on every answer, and returns a risk score, a
grade from A to F, and a Prüfbericht (test report) containing the exact quote
that proves each finding and a concrete fix for it.

We are black box. We never read source code, never connect to a repository and
never show code in a report. We test behaviour.

---

## The problem

A chatbot's answer is a statement by the company that deployed it.

In February 2024 the British Columbia Civil Resolution Tribunal held **Air
Canada** liable for a refund policy its support chatbot had invented. The
airline argued the bot was a separate entity, responsible for its own words.
The tribunal rejected that explicitly.

That is the risk model in one case. An LLM placed in front of customers can:

- **leak data** — its own instructions, internal pricing, a supplier's name,
  another customer's details
- **invent commitments** — a discount, a refund, a delivery date that becomes a
  dispute
- **say something discriminatory or harmful** — under the company's name, in the
  company's colours

A regulatory floor arrived on top of that. Since **02.08.2026**, Art. 50(1) of
the EU AI Act (Regulation (EU) 2024/1689) requires that a person interacting
with an AI system be informed of it, unless that is obvious from the context.
The Digital Omnibus delayed the high-risk obligations; it did not delay Art. 50.
The penalty ceiling under Art. 99 is up to €15M or 3 % of worldwide turnover.

Almost nobody sells a defence: in the ECA European Cybersecurity Mapping 2025,
AI Security and Integrity holds **7 of 828** European vendors — 0.8 %, the
emptiest segment on the map.

## Why a code scanner cannot find this

The vulnerability does not live in the code. It lives in the text.

A static analyser can prove your inputs are escaped and your dependencies are
patched, and it will never find that your bot hands over its system prompt if
you ask politely, or that it grants a full refund to anyone who claims to be a
team leader. The exploit is a sentence, so finding it needs a dynamic, black-box
method with an attack library and a judge, not a parser. It also means the same
bot can answer differently to the same sentence twice — which is why the method
itself has to be measured rather than asserted.

---

## Two layers

| | Art. 50 Check | Red team Prüfung |
|---|---|---|
| Method | Passive: reads one public page | Active: sends real attacks to the bot |
| Price | Free | Paid |
| Role | Lead funnel | The product |

The split exists for a legal reason: attacking a bot you do not own is not a
product, it is an offence. The free layer needs no permission at all, so it can
run on a prospect's site before any conversation exists.

### The free Art. 50 Check

**Why.** It answers a question a German compliance manager already has, in a few
seconds, without a sales call. And every site that fails it is a named,
evidenced lead — which is what makes it a funnel rather than a giveaway.

**How.** One GET of the public page, as an ordinary visitor with an identifiable
user agent. No message is ever sent to the bot, so no permission is required and
no provider's terms are breached. `robots.txt` is honoured, and the URL is
SSRF-guarded — private, loopback, link-local and cloud-metadata addresses are
rejected, re-checked on every redirect hop.

Four findings, each with evidence and a fix:

- `widget_found` — is there a chat widget at all (nine vendor signatures:
  Intercom, Tidio, Userlike, Crisp, Drift, Zendesk, Freshchat, LiveChat, generic)
- `ai_disclosure` — does the widget disclose that it is AI on first contact
- `privacy_link` — is a privacy policy reachable beside it
- `impressum` — § 5 DDG

### The red team Prüfung

**Why.** Art. 50 is a label on the outside of the box: it asks whether you told
the user it was a bot. This asks what the bot does when someone actually tries —
which is where the Air Canada class of liability lives, and no label prevents it.

**How.** The next section, in four steps.

---

## How a scan works

One attack, end to end:

**1. Take an attack from the library.** `attacks/attacks.yaml` holds 78 across
the five OWASP LLM categories; `attacks_short.yaml` holds 21 and is what a scan
runs by default. Attacks are data, not code — a YAML block with an id, category,
severity, the prompt, and the fix to print if it succeeds. Adding one needs no
Python and no restart.

**2. Send it to the bot under test.** The normal case is a real bot on a real
website: paste its address and `api` mode attacks the live chatbot over HTTP,
exactly as a customer would reach it. A bare host is completed to the chat
endpoint and printed back before anything is sent — silently scanning an address
other than the one on screen is how a report ends up describing something the
reader never asked about. `model` mode instead takes a system prompt and posts it
with each attack to a deployment we hold, which is useful before a bot is live
and is how the demo bots run.

**3. Judge the answer, in two layers, in this order.**

- **Layer 1, deterministic.** The customer names a string that must never appear
  in an answer — a real secret already in their prompt, or a canary planted there
  for the test. If it appears, the leak is a fact: a string comparison, no model,
  no ambiguity. Layer 1 always wins — if the secret leaked, the model's opinion is
  irrelevant.
- **Layer 2, the AI judge.** Only for what a string match cannot catch: did the
  bot approve a refund, give medical advice, insult a customer, claim to be
  human. A separate model, and it may never award itself `confirmed`.

**4. Record the verdict with its evidence** — the exact substring of the bot's
answer that proves the finding, verified to actually be a substring, because
judges paraphrase. No quote, no finding.

**5. Score it.** Every bot starts at 100 and loses points per finding, weighted by
severity and by how well the finding is proven; defending an attack earns nothing,
because that is normal behaviour rather than an achievement. Two rules matter more
than the constants, which we are still tuning: **any critical finding caps the
grade**, and **a scan with too little evidence is issued with no grade at all**
rather than a flattering one, since a missing attack can only help the bot. The
method is one short function in `backend/scoring.py`.

**Once is not a measurement.** The same bot answers differently to the same
sentence — three identical runs against one target returned A/100, A/90 and B/79.
So one press runs the whole library **twice and reports the worse pass**, carried
as one whole report, never a score from one pass beside quotes from another. An
ungraded run outranks any graded one, so "no grade issued" cannot be softened by
running again until a number appears.

Attacks run concurrently, results stream to the browser as they land, and an
attack the target's own provider refuses to deliver is recorded as `BLOCKED` —
no credit, no penalty, listed in the report as not delivered.

---

## What we measured

The obvious objection to this product is *"you have a model judging a model —
what if the judge is wrong?"* So it is measured, against two calibration sets of
real harvested bot answers — 30 items and 43 items — each labelled PASS or FAIL
by a person with their reason recorded.

| Measurement | Result |
|---|---|
| Judge agreement with human labels, 30-item set, 10 consecutive runs | **29 of 29 judgeable items — identical in every run** |
| — of which the deterministic layer alone | **11/11 and 13/13 on the two sets, zero false positives, every run** |
| Errors across a full 78-attack scan of three bots (~234 target calls) | **0** |
| Judge-side content filtering, 78 attacks × 3 bots | **0** |


Those answers were harvested from three bots we built for the purpose: a
deliberately careless support bot, a hardened twin of it with the same job and a
fixed prompt, and a doctor's appointment bot as a realistic middle case. They are
the fixtures the judge was calibrated against — and they are still on the site as
the demo, because the contrast is the argument:

| Bot | Grade |
|---|---|
| TeleShop support, unprotected | **F (0)** — leaks its planted secret verbatim |
| Praxis Dr. Weber, realistic middle case | **D (42)** |
| TeleShop support, hardened — same job, fixed prompt | **A (94–100)** |

Same attacks, same model, three grades. The difference is the prompt. Grades move
by a band between runs, which is the target answering differently rather than the
judge, and is why a scan now runs the library twice and reports the worse pass.

---

## Using it on the website

Both layers run at **[llmantis.de](https://llmantis.de)** — access-restricted for
now, while the Impressum and Datenschutz pages are finalised.

**The free Art. 50 Check.** Paste the URL of any site and start it. It reads the
page and lists what it found: chat widget, AI disclosure, privacy link,
Impressum. No account, and nothing is sent to the bot.

**The red team Prüfung.** On the scan page:

1. **Paste your bot's web address.** The chat endpoint is completed for you and
   shown before anything is sent. Or try one of the three demo bots from the
   dropdown, or paste a system prompt that is not live yet.
2. Optionally name a canary — a string that must never appear in an answer. That
   is what makes a leak deterministic instead of a judgement.
3. Press **Run scan**. Attacks stream in with a verdict each, twice over, and the
   worse of the two passes becomes the report.
4. Open the Prüfbericht: the grade, every finding with the bot's own words as
   evidence, the fix, the coverage, and the attack library version. Print to PDF
   from the browser. Declared secrets are masked, so the report quotes the leak
   without reprinting it.

Only attack domains you own!

---

## What we do not claim

LLMantis issues a **Prüfbericht** — dated evidence that a system was tested, with
the attack library version stamped on it. Nachweis der Sorgfalt: proof that you
looked, not proof that you comply.

It is not a certificate and not legal advice. Under the AI Act, conformity
certificates are issued only by notified bodies and only for high-risk systems,
so a chatbot certification does not exist as a legal category. Claiming one is a
§ 5 UWG problem in Germany, not a wording preference. "Certified",
"zertifiziert", "AI-Act-konform" and "DSGVO-konform" are therefore banned
repository-wide — in UI text, comments, variable names, documentation and commit
messages.

LLMantis tests **only** AI systems the user owns. Active testing requires
verified ownership of the target. All attacks are publicly documented techniques
from the OWASP Top 10 for LLM.

---

## Run it locally

```bash
git clone git@github.com:VladvonTranssylvanien/LLMantis.git
cd LLMantis
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in the keys
docker compose up -d        # Postgres
alembic upgrade head
uvicorn backend.main:app --reload --port 8000
```

Then `http://localhost:8000` for the landing page, `/scan` for the scanner and
`/static/art50check.html` for the free check.

`.env` needs a judge (`PROVIDER`, `AZURE_URL`, `AZURE_KEY`, `JUDGE_MODEL`) and a
target (`TARGET_URL`, `TARGET_KEY`, `TARGET_MODEL`). There is deliberately no
mock mode: without a working provider every attack errors and no grade is issued.
Today the judge is gpt-4.1 and the target gpt-4.1-mini, both on Azure.

Full walkthrough in `SETUP.md`, key handling in `SECRETS.md`, contributor
conventions and the full endpoint table in `README_old.md`.

## Where the code is

```
backend/    scanner.py · judge.py · scoring.py · ownership.py · netguard.py
            art50engine.py · art50probes.py · art50opener.py (the free check)
            llm.py (the only file that talks to a provider) · main.py · models.py
attacks/    attacks_short.yaml (21, the default) · attacks.yaml (78)
frontend/   one file per page, no build step: landing · index (scanner)
            · art50check · report
calibration/  the hand-labelled sets and the agreement runner
lab/          the three target bots and the measurement harness
```


## Where this goes next

The architecture was built so the two obvious directions are additions rather
than rewrites.

**Ownership verification.** Attacking a domain you do not own requires a DNS TXT
record proving you do.

**A much larger attack library.** Attacks are data, so the library grows without
touching the engine, and because the score deducts per finding rather than
counting the percentage defended, adding attacks cannot flatter a bot. 

**An AI in the attacker loop.** Today the library is fixed — every bot gets the
same sentences. The next step is an attacking model that reads the target's own
answers and decides what to try next: following up where a bot hesitated, and
writing attacks specific to the bot in front of it, since a travel-booking bot and
a medical appointment bot have different things worth extracting. 

Further out: multi-turn attacks that build trust across a conversation before
asking, scheduled re-scans that flag when a prompt change reopened something, and
voice agents.

## Team and licence

Bogdan — coordination, design, positioning. Vlad — engine, API, database.
Gregor — target lab, attack library, judge calibration. Kwabena — GRC, legal
hooks, disclaimers. Working language is English throughout.

Licensed under **AGPL-3.0** (see `LICENSE`) rather than MIT for one reason: this
repository is public and the product is sold as a hosted service, so a competitor
who runs this code as a service must publish their changes.
