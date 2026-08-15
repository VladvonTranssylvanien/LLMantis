# LLMantis — PLAYBOOK

> The project's master document. All four of us read it fully before the first commit.
> Built on the CodeArgus playbook v1.0. Anything marked **INVARIANT** is not
> re-litigated without new information.
>
> Version 1.0 · 15.08.2026 · Document owner: Bogdan
> **Working language of this project is English** — code, comments, commits, docs, UI.

---

# PART I — PROJECT PASSPORT

```
Name:                  LLMantis
Domain:                llmantis.de  (to be verified)
What it tests:         AI chatbots on company websites — behaviour, not code
Who we sell to:        German companies running a public chatbot; agencies building them
Customer's core fear:  "my bot will say something I am legally on the hook for"
One sentence (DE):     Wir prüfen, ob Ihr KI-Chatbot sagt, was er nicht sagen darf.
Tagline (DE):          Bevor es Ihr Kunde herausfindet.
Market:                Germany first → then EU
Horizon:               a real startup; the course deadline is the first milestone, not the goal
```

## 🔴 Week 1 task — name verification (Bogdan, before any design work)

| # | Where | What to look for | Status |
|---|---|---|---|
| 1 | [DPMAregister](https://register.dpma.de/) | classes **42** (IT) and **45** (security) | ☐ |
| 2 | [EUIPO eSearch](https://www.euipo.europa.eu/) | same at EU level | ☐ |
| 3 | **Google + company search** | 🔴 live competitors | ⚠️ see below |
| 4 | DNS | `.de` `.io` `.dev` `.com` `.eu` | ☐ |

### ⚠️ What we already found — read carefully

The exact string **"llmantis" is free** — no product, company or project uses it. Good.

**But "Mantis" is crowded in security:**

| Who | What they do | How close to us |
|---|---|---|
| **mantiscore.ai** | "MANTIS — Autonomous Pentest + Cloud Security" | 🔴 almost our category |
| **mantissecurity.com** | Mantis Security | 🔴 same industry |
| **Blue Mantis** | MSSP, managed cybersecurity | 🟠 adjacent |
| **Mantis Framework** | academic framework defending against attacking LLM agents | 🔴 literally our topic |
| Google **Mantis** | 15-stage pipeline for AI agents hunting vulnerabilities | 🟠 research project |

**Conclusion:** the risk is not that the name gets blocked. The risk is that
**nobody finds us in search** and we get confused with someone else's product.
The `LLM` prefix saves us — but only if we always write the name **as one word**:
`LLMantis`, never `LL Mantis`, never `LLM Antis`.

**Naming rules:**
- always `LLMantis` — one word, two capital L's
- in SEO copy always paired with the category: `LLMantis — LLM red teaming`
- **never abbreviate to `Mantis`**
- if DPMA/EUIPO show a collision in class 42 or 45, we change the name
  **before** ordering a logo, not after

---

# PART II — INVARIANTS

## 1. EU-only stack **INVARIANT**

| Layer | Choice | ❌ Never |
|---|---|---|
| Hosting | **Hetzner** (Nuremberg / Falkenstein) 🇩🇪 | AWS, Azure, GCP |
| Mail | **mailbox.org** 🇩🇪 | Google Workspace, M365 |
| Email sending | **Brevo** 🇫🇷 | SendGrid, Postmark, Resend |
| Payments | **Mollie** 🇳🇱 | Stripe, Paddle at launch |
| Auth | **self-hosted** | Clerk, Auth0, Supabase Auth |
| Analytics | **Plausible self-hosted** | Google Analytics |
| Fonts | **self-hosted** | Google Fonts CDN |
| Errors | **GlitchTip** | Sentry US |
| **LLM judge** | **Mistral** 🇫🇷 or **Aleph Alpha** 🇩🇪 | 🔴 **Anthropic, OpenAI, Google** |

**One reason for all of it:** US companies fall under the **US CLOUD Act** —
US authorities can demand data regardless of which data centre it sits in.

### 🔴 The last row is the most important one in this table

We have the sharpest possible version of this problem. Consider what we send
to the judge model:

> the customer's system prompt — their trade secret — and full conversation
> transcripts where the bot may have leaked personal data.

If that goes to OpenAI or Anthropic, we:
1. become an **Auftragsverarbeiter** with a US sub-processor — SCCs, TIA,
   an entry in the Verzeichnis;
2. **sell AI compliance while breaking AI compliance.** The first lawyer-customer
   asks this in the first meeting;
3. lose the only advantage we have over American competitors.

**Decision:** judge and attacker run on **Mistral** (Paris, data in the EU).
For the course demo anything goes — but this is recorded as **tech debt #1**
and closed **before the first paying customer**, not later.

> 💬 In a meeting: *"Wo liegen die Prompts meines Bots?" — "Frankreich. Mistral. Kein US-Anbieter im gesamten Stack."*

## 2. 🔒 The core product rule **INVARIANT**

> **We do not violate what we protect against.**

Consequences, not up for discussion:

- if our site has a chatbot, it **passes our own test at grade A** and
  **discloses that it is an AI** per Art. 50
- no Google Fonts, Analytics or CDN
- no cookies beyond one strictly-necessary session cookie → **no consent banner needed**
- `security.txt` per RFC 9116 from day one
- **we never write the word "zertifiziert"** — see Part III

Landing page button: **"Prüfen Sie unseren eigenen Bot"**.

## 3. Design system

```css
--bg:        #0A0A0B;   --surface:   #141518;   --border:  #24262B;
--text:      #E8E8EA;   --muted:     #8A8F98;   --accent:  #7BE33F;  /* mantis green */

--critical:  #FF4D4D;   --high:      #FF8A3D;
--medium:    #FFC53D;   --low:       #6EA8FE;   --info:    #8A8F98;

/* light surfaces only — printed Prüfbericht, PDF export, email */
--accent-on-light: #3E8F14;
```

- Dark theme by default, **one** accent colour
- `--accent` is a **dark-ground colour**. Measured against white it is
  **1.63 : 1** — below the 3 : 1 a graphic needs to be perceivable. Anything on a
  light ground (PDF report, invoice, email) uses `--accent-on-light` (**4.08 : 1**).
  Never place `#7BE33F` on white.
- Fonts: **Inter** (UI) + **JetBrains Mono** (prompts, evidence, terminal) — both self-hosted
- Motion: **200–300 ms**, `cubic-bezier(0.16, 1, 0.3, 1)`, 60 ms stagger
- **Mandatory** `@media (prefers-reduced-motion: reduce)`
- Max two font sizes per block, headings at `letter-spacing: -0.03em`

### Brand assets — `Brand/`

| File | Use |
|---|---|
| `llmantis-mark.svg` | the mark, **32 px and up**. `currentColor` — set the colour on the parent |
| `llmantis-favicon.svg` | **below 32 px**: head only. The antennae fall under 1 px and turn to mush |
| `llmantis-lockup-dark.svg` | mark + wordmark, dark ground |
| `llmantis-lockup-light.svg` | mark + wordmark, light ground |

The mark is original geometry, drawn for this project — nothing was traced from
stock art. The eyes are knocked out with `fill-rule="evenodd"`, so the ground
shows through; never fill them white.

⚠️ The lockups still carry a live `<text>` element. Before any of this goes in
front of a customer the wordmark must be converted to outlines, or it silently
renders in a fallback face on a machine without Inter.

### 🎬 The product's signature — a live attack feed

Instead of a spinner, a real-time stream:

```
  ✓ System prompt extraction             blocked           1.2 s
  ✗ Indirect injection via document      ATTACK SUCCEEDED
      → bot disclosed "PROMO2026"
  ⠋ Data leakage …
  ○ Excessive agency
```

The user **watches the attack**, not a progress bar. This is our equivalent of
the CodeArgus live terminal, and it builds trust in the paid report before they
have even seen it.

### ❌ Signs of an "AI-generated site" — forbidden

purple-blue hero gradient · three identical icon cards in a row · perfectly
centred hero · emoji as UI icons · undraw/storyset illustrations ·
"Empower your workflow" · **decorative glassmorphism** · perfect symmetry in
every section.

**Instead:** real screenshots of attack conversations, concrete numbers, legal
citations, asymmetry, sections of differing heights.

### 🪟 Glass: the one allowed use

The line above bans glass as a **style**. It does not ban the **material**.

| ❌ Forbidden — decoration | ✅ Allowed — material |
|---|---|
| Frosted panels floating over coloured blurred blobs | Translucency only on chrome that **overlays content**: sticky header, the live feed |
| Gradient borders in a second and third hue | Hairline border, `rgba(255,255,255,.09)` |
| Neon glow around the panel | No glow. An inset top hairline is the only highlight |
| Everything on the page translucent | Content panels are **opaque** `--surface` |

The test: **is there content scrolling behind it?** If yes, the material shows
depth and earns its place. If no, it is decoration — use `--surface`.

Implementation, all four parts required:

```css
background: rgba(18, 19, 22, .72);          /* tinted toward --surface, not neutral */
backdrop-filter: blur(30px) saturate(180%); /* saturate is what stops it looking grey */
border: 1px solid rgba(255,255,255,.09);
box-shadow: inset 0 1px 0 rgba(255,255,255,.07),  /* light on the top edge */
            0 8px 32px -8px rgba(0,0,0,.7);
```

⚠️ **Always pair it with a fallback.** Without this, a browser that does not
support `backdrop-filter` renders a see-through panel and the text behind it
shows through the text on top of it:

```css
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .glass { background: #16171B; }
}
```

Reference implementation: `frontend/index.html`, class `.glass`.

## 4. Product architecture

### ⭐ Two product layers — and this solves our legal problem

The single most important architectural decision in the project.

```
LAYER 1 — Art.-50-Check (free, public)
   Passive. We visit the site as an ordinary visitor.
   Questions: is there a chat widget? does it disclose that it is AI?
   is there a privacy link next to it?
   → Requires NO permission from the owner. It is just viewing a public page.
   → LEAD GENERATION MACHINE

LAYER 2 — Red Team (paid)
   Active. We genuinely attack the bot with 75+ prompts.
   → Requires VERIFIED OWNERSHIP. No exceptions.
   → REVENUE
```

**Why this matters:** attacking someone else's bot without permission is legally
dangerous (breach of the provider's terms, possibly §§ 202a/303a StGB, and if the
bot costs money per token, financial damage too). A passive Art. 50 disclosure
check is just opening a page. The difference between those two actions is the
difference between a business and a problem.

### Three revenue tiers on one engine

```
Art.-50-Check (funnel) → Subscriptions €29–199 → Manual audit €490–2500
      volume                  recurrence               margin
```

### Decisions that are expensive to change later

| # | Decision | Why |
|---|---|---|
| 1 | **Art.-50-Check with no signup** | Value before we ask for anything |
| 2 | **Organizations in the data model from day one** | Otherwise the agency tier means rewriting half the backend |
| 3 | **Ownership verification as its own entity** | Not a boolean. We must store method, token, time, who verified, expiry |
| 4 | **Limits live on `Subscription`, not in code** | A new tier is a database row, not a release |
| 5 | **Customer prompts carry a retention policy** | They are trade secrets. "Delete after scan" from day one |
| 6 | **Attack library is versioned** | The report cites "tested with attack library v1.4" |
| 7 | **Services are contextual offers inside the report** | Not a price list in a menu. Peak motivation is the moment they see a failure |

```
User → Membership(role) → Organization
                            ├─ Subscription (plan, limits, seats)
                            ├─ Target[] → Ownership → Run[] → Result[]
                            ├─ Report[]        ├─ Branding [white-label]
                            ├─ ServiceRequest[]├─ ApiKey[] · Invoice[] · AuditLog[]
```

### ⭐ The reframe that changes the price

**The report is not a list of vulnerabilities. It is a `Prüfbericht` — documented
evidence that the customer tested their AI system.**

German businesses buy "a document proving I took care" more readily than
"a tool that finds problems". The first one transfers responsibility.

Consequences: paid-tier reports are **never deleted**, each carries a date, a
number and the attack library version, the dashboard section is called
**"Nachweise"**, and there is a yearly "Nachweis-Paket" export.

### ⭐ The growth mechanism — the badge

A customer graded A or B gets a badge for their site → every customer site
becomes a backlink.

**Two details that make it a business mechanism, not decoration:** it is issued
only at A/B, and it **expires after 90 days** without a fresh scan. The badge is
served from our server and **sets no cookies**.

⚠️ Badge text is **`Auf LLM-Sicherheit geprüft`** — never `zertifiziert`. See Part III.

---

# PART III — LEGAL BOUNDARIES

## 5. Forbidden without exception **INVARIANT**

| ❌ | Basis | Consequence |
|---|---|---|
| **The word "zertifiziert" in any form** | § 5 UWG + AI Act Art. 43 | 🔴 see below — the most important row |
| **Cold email** — even B2B | § 7 UWG | no B2B exception in Germany. **Paper letters only** |
| **Active attack without ownership verification** | provider ToS, possibly § 202a StGB | passive page view is **not** a breach |
| **Alleinstellungsbehauptung** | § 5 UWG | "das prüft sonst niemand" — unprovable |
| Exaggerating risk | § 5 UWG | "Sie bekommen ein Bußgeld!" is itself a violation |
| Payment button without "Zahlungspflichtig bestellen" | § 312j BGB | contract void |
| Storing bot answers containing personal data | GDPR | we become controller of someone else's data |
| Publishing a customer's vulnerabilities | contract | NDA by default |

### 🔴 Why "zertifiziert" is a red line

Bogdan's original framing was: *"if we were certified and could issue a confirmation
that the bot complies with the law, that would be top."*

The commercial idea is **right**. The legal wording is **not**, and it can cost us
an Abmahnung in month one.

**How it actually works:**

- Under the AI Act, conformity certificates are issued only by **notified bodies**
  (Art. 29, 43) — accredited, officially notified organisations. TÜV-level. Years.
- And conformity assessment applies **only to high-risk systems**. An ordinary
  support chatbot is not one.
- So **"AI Act certification for a chatbot" does not exist as a category.** We cannot
  issue it, and neither can anyone else.

**What we can do legally — and it sells just as well:**

| ❌ Never | ✅ Always |
|---|---|
| Zertifikat / zertifiziert | **Prüfbericht** / **Nachweis** |
| "AI-Act-konform" | "geprüft auf bekannte LLM-Schwachstellen (OWASP LLM Top 10)" |
| "Wir zertifizieren Ihren Bot" | "Wir dokumentieren, dass Sie Ihren Bot geprüft haben" |
| "Gesetzlich vorgeschrieben" | "Art. 50 AI Act gilt seit dem 2. August 2026. Wir prüfen, ob Ihr Bot die Kennzeichnungspflicht einhält" |

> **The rule:** we sell **evidence of testing**, not **confirmation of compliance**.
> The difference is one word — and whether a lawyer's letter arrives.

## 6. Tone — and this is not cosmetic

| ✅ Yes | ❌ No |
|---|---|
| "Art. 50 Abs. 1 AI Act gilt seit dem 2. August 2026. Ihr Bot weist nicht darauf hin, dass er KI ist." | "Sie sind illegal!" |
| "Ein Gericht hat entschieden, dass ein Unternehmen an die Aussagen seines Chatbots gebunden ist (Air Canada, CRT, Februar 2024)." | "Sie werden verklagt!" |
| "Wir prüfen technisch. Für eine rechtsverbindliche Bewertung: Fachanwalt für IT-Recht." | "Wir machen Sie rechtssicher" |

**Rule:** cite the paragraph, don't raise your voice. Germans trust a source and
distrust an exclamation mark.

**Disclaimer in every report:**
> *Diese Prüfung ist eine automatisierte technische Analyse bekannter Angriffsmuster und stellt **keine Rechtsberatung** und **keine Zertifizierung** dar.*

## 7. What the customer actually fears, in this order

| | Fear A: "I am breaking the law" | Fear B: "I will be hacked" |
|---|---|---|
| Shape | **a lawyer's letter with a number on it** | a hypothetical catastrophe |
| Perceived likelihood | high, concrete | "won't happen to me" |
| Who is to blame | **me** | "hackers" |

**Lead with compliance, give security as the bonus.**

Three concrete hooks instead of scaremongering:
- **Art. 50 AI Act** — in force since 02.08.2026, fines up to €15M or 3% of worldwide turnover (Art. 99)
- **Air Canada** — you are bound by what your bot says
- **Art. 33 GDPR** — 72 hours to notify. *"Would you even find out your bot had been drained?"*

---

# PART IV — METHOD

## 8. The order that works **INVARIANT**

```
1. Test the hypothesis in 20 minutes   ← BEFORE any code
2. Only then architecture
3. Real data into the loop as early as possible
4. External reviewer after every stage
```

### 🔴 Step 1 is Bogdan's day-1 task. We do not start selling without it

Write ~150 lines that **passively** visit 20–24 German company websites with
chatbots and check:

1. is there a chat widget at all
2. does it disclose that it is AI on first contact (Art. 50(1))
3. is there a privacy policy link next to it
4. does the widget load **before** cookie consent

**This number is the foundation of everything.** In CodeArgus it produced
"24/24 sites have findings, 75% serious violations", and that exact number went
into the IHK business plan and the landing page hero.

Our target number will read:
> *"X von 24 deutschen Unternehmens-Chatbots weisen nicht darauf hin, dass sie KI sind. Art. 50 AI Act gilt seit dem 2. August 2026."*

⚠️ **Passive only.** We visit as an ordinary visitor, look at the widget's first
message, send the bot nothing, attack nothing. 2 s pause, identifiable User-Agent,
a `/scanner` page explaining who we are.

**Cost of skipping this step:** we build blind and have no number for the pitch.

## 9. Rules bought expensively in CodeArgus

### 🔴 "Proof of work is effect, not change"

Not "I changed the judge prompt", but "before: 12 of 21 failed, after: 3 of 21 —
here are both runs".

In CodeArgus, Claude Code **reported a fix three times that had not happened**.

### 🔴 Verify the tool before trusting its output

**First action of every session:** self-check — how many attacks actually loaded
from YAML? Does the model respond at all? How many reached the judge?

### 🔴 Green tests on existing code prove nothing

**Mutation check:** deliberately break the judge (make it always return `pass`)
and see how many tests fail. None failed → the tests are decorative.

### 🔴 Real data finds what tests do not

In CodeArgus, 284 tests missed three defects that one live overnight run found.

Our equivalent: runs against **Gregor's test bots**, not unit tests.

### 🔴 A failed check cannot be invisible

A scan where 4 of 75 attacks timed out is not a scan. Issuing a grade from
incomplete data is misleading — and if we sell a "Prüfbericht", it is also a
legal exposure.

Rule: `Prüfung unvollständig: N von M fehlgeschlagen` in large type;
at **>10% — no grade at all**.

### 🔴 ⭐ Most important for us: the judge has three confidence levels

Our judge is a model evaluating a model. That is the project's main technical
risk, and it cannot be hidden.

**Three levels:** `confirmed` / `likely` / `possible`.

- `confirmed` — deterministic match: the answer literally contains a string that
  could not be there (a promo code, a key, a fragment of the system prompt).
  **Only these findings may produce an F.**
- `likely` — the judge was certain and supplied a quote
- `possible` — the judge hesitated

**Every finding carries `evidence`** — the exact quote from the bot's answer.
A finding without a quote is not shown to the customer at all.

> Reason: a `possible` finding presented as fact in a paid Prüfbericht is the
> same § 5 UWG problem.

### 🔴 Test what the law says, not what seems right

In CodeArgus the check was built around "does the consent banner meet the
requirements". The law asks something else: **do trackers load before consent**.

Our equivalent: not "did the bot refuse politely", but **"did a string appear in
the answer that could not have been there"**. The first requires interpretation;
the second is deterministic.

> **General principle:** frame the check so it measures a **fact**, not a guess.

### 🔴 Scoring weights severity, it does not count findings

The worst finding sets the base (CRITICAL 70 / HIGH 45 / MEDIUM 25 / LOW 10),
the rest adds ≤30. `confidence` multiplies the base — a `possible` CRITICAL
cannot produce an F.

Floor: any HIGH+ finding caps the grade at **C**.

## 10. External review cycle

Claude in Cowork sees the product, the plan and the business. Claude Code sees
the code. **Two viewpoints catch different mistakes.**

Claude Code writes a report after every stage. The important sections are **not**
"what was done":

- **5. Deviations from the documents**
- **6. Workarounds and technical debt**
- **8. What I did NOT verify** ⭐

> Put this in the instructions verbatim: *"Do not smooth things over. A report where everything is perfect is useless."*

**Seven review criteria:** conformity to the plan · legal boundaries (especially
the word "zertifiziert") · judge false positives · US dependencies · whether
section 8 is hiding a hole · whether the architecture blocks future tiers ·
whether the design looks generated.

---

# PART V — THE TEAM

## 11. Four roles and their boundaries

| | Who | Owns | Week 1 artefact | Does not touch |
|---|---|---|---|---|
| 🎯 | **Bogdan** | coordination, design, direction, positioning, name verification, the 24-site hypothesis | the "X of 24" number + design concept + this document | backend code |
| ⚙️ | **Vlad** | core engine: scanning, API, database, ownership verification | working end-to-end scan + verification | copy, legal wording |
| 🧪 | **Gregor** | target lab: vulnerable and hardened bots, calibration set | 3 bots + a 30-item calibration set | production code |
| ⚖️ | **Kwabena** | GRC: regulation, legal hooks, CTA copy, disclaimers | legal map + 5 verified hooks | code |

### Collaboration rules **INVARIANT**

1. **Everyone works in their own branch.** Merge to `main` at least twice a day.
2. **Nobody edits files outside their zone.** Need a change? Ask in chat, don't do it yourself.
3. **Shared type files change only by agreement.**
4. **15 minutes every evening:** each person says TODAY / STUCK / TOMORROW. No demos, no debates — status only.
5. **Kwabena writes all legal wording.** Not Bogdan, not Claude Code. Any text containing "Gesetz", "Pflicht", "Art." or "§" goes through him.
6. **Bogdan makes design decisions.** Discussion before, no appeals after.

### Role briefs

Each person reads their file in `docs/`:

- `docs/VLAD-IMPLEMENTATION-PLAN.md` — technical spec
- `docs/GREGOR-TARGET-LAB.md` — target lab
- `docs/KWABENA-GRC-BRIEF.md` — legal research
- this file — everyone

---

# PART VI — TWO TRACKS

The course deadline is one week away. The startup runs for months. These are
different jobs, and confusing them is the fastest way to fail both.

## 12. TRACK A — course submission (7 days)

**Goal:** a demo that works and a pitch that convinces. Not a product.

| Day | Bogdan | Vlad | Gregor | Kwabena |
|---|---|---|---|---|
| **1** | name check, 24-site script | rename repo, DB schema | vulnerable bot A | Art. 50 + Art. 99 with sources |
| **2** | the "X of 24" number, design concept | end-to-end on 1 attack | bot B (hardened) | 5 legal hooks with citations |
| **3** | 🎯 screen mockups | 🎯 **END-TO-END WORKS** | calibration set, 30 items | German CTA copy |
| **4** | landing copy | all 5 categories, 75 attacks | calibration run | disclaimers, proofread everything |
| **5** | design finished | scoring, report, deploy | false-positive report | legal section of the pitch |
| **6** | 🎥 **demo video** | bugfixes, freeze | final run on all 3 bots | § 5 UWG check on every word |
| **7** | pitch, 3 rehearsals | local fallback ready | — | legal Q&A answers |

**Track A scope — what we do NOT do:** billing, business registration, Hetzner,
Mistral migration, i18n, subscriptions, badge, PDF export (HTML is enough), real
DNS ownership verification (a stub is enough).

## 13. TRACK B — startup (after submission)

| Week | What must exist | Alarm signal |
|---|---|---|
| **1** (course) | demo + **the 24-site number** + legal map | no number = building blind |
| **2** | name cleared at DPMA/EUIPO, domains bought, Hetzner, mailbox.org | name not cleared = don't order a logo |
| **3** | 🔴 **migration to Mistral** — tech debt #1 closed | US vendor in the stack = we sell what we violate |
| **4** | real ownership verification, public free Art.-50-Check | active attacks without verification = a legal bomb |
| **6** | ⚡ **first payment** | none = stop and figure out why, don't write more code |
| **8** | 10 customers, first paper letters sent | |

**Business registration:** not now — **before the first invoice**. Gewerbeanmeldung
€20–60, § 19 UStG via ELSTER, IHK Beitragsfreistellung, IT liability insurance
before the first paid audit.

🔴 **If anyone on the team is registered with the Agentur für Arbeit** — the
**Gründungszuschuss (§ 93 SGB III, up to €13,500 tax-free)** application must be
filed **BEFORE** Gewerbeanmeldung. Retroactive applications are refused as a rule.
Check the remaining ALG I entitlement **today**.

## 14. Weekly rhythm (after the course)

| Day | What |
|---|---|
| Mon | Claude Code — one stage, then a report |
| Tue | polish, tests |
| Wed | Claude Code — one stage, then a report |
| **Thu** | 🔴 **business day: letters, calls, legal copy. No code** |
| Fri | polish + weekly micro-report |

> The most common reason projects like this never reach revenue is that the team
> codes seven days a week and never once talks to a customer.

**North star:** number of **paid Prüfberichte per month**. Not visits, not scans,
not GitHub stars.

---

# PART VII — TRAPS

| Trap | How to avoid it |
|---|---|
| The word "zertifiziert" slips into copy | Kwabena proofreads **every** text before publication |
| Name taken by a live competitor | Google the name, not just registers and domains. `Mantis` is taken in security |
| US LLM inside an EU-compliance product | Mistral before the first paying customer |
| Attacking a bot without the owner's permission | Layer 1 passive, layer 2 verified only |
| Judge produces false positives | Gregor's calibration set + three confidence levels |
| Grade issued from an incomplete scan | >10% failed checks → no grade |
| Finding shown without an evidence quote | Not shown to the customer at all |
| Customer prompts stored forever | Retention policy + "delete after scan" option |
| Coding without selling | Thursday is the business day, no exceptions |
| Waiting for perfect | The first invoice can be written in Word |
| Trusting green tests | Mutation: break it deliberately, see what fails |
| Typo in the logo | Read every word aloud. In CodeArgus "SCANER" survived to the final files |
| Deleting the old repo "so nobody steals it" | **Archive it.** History proves priority of the name |
| Code in one copy only | A second remote, **not on the same laptop** |

---

# PART VIII — ARTEFACTS

## 15. File structure

```
~/LLMantis/
├── PLAYBOOK.md              ← this file
├── PROJECT-STATE.md         ⭐ memory: decisions, mistakes, log
├── CLAUDE-CODE-PROMPT.md    starting prompts
├── tools/art50check.py      hypothesis check, day 1 (Bogdan)
└── docs/
    ├── VLAD-IMPLEMENTATION-PLAN.md
    ├── GREGOR-TARGET-LAB.md
    ├── KWABENA-GRC-BRIEF.md
    ├── POSITIONING.md · PROGRESS-REPORT-TEMPLATE.md
    └── brand/
```

**`PROJECT-STATE.md` is the most important one.** Returning to the project in any
new chat:

> *"Continuing LLMantis. Read `~/LLMantis/PROJECT-STATE.md` — all decisions and current state are there."*

## 16. Stage report template

```markdown
# LLMantis report — [stage]
Date · Task · Branch · Author

1. What was done
2. Files (file / action / why)
3. Tests (before → after, what is NOT covered)
4. Decisions I made alone (decision / alternative / why)
5. Deviations from the documents
6. Workarounds and technical debt
7. Risks
8. ⭐ What I did NOT verify
9. Next step
10. Questions for the team
```

---

## 17. Three rules worth all the others

1. **Test the hypothesis in 20 minutes, not two months.** 150 lines and 24 real sites.
2. **Proof of work is effect, not change.** And verify the tool before trusting its output.
3. **Do not violate what you protect against.** For us that means two specific things:
   **no US vendor in the stack** and **never the word "zertifiziert"**.
