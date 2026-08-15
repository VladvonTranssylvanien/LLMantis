# GRC Brief — Kwabena

> Read `PLAYBOOK.md` first. This file is your scope only.
> **You own every sentence in the product that contains the words *Gesetz*, *Pflicht*, *Art.*, *§*, or a fine amount.** Nobody publishes legal wording without your sign-off — not Bogdan, not Claude Code.

---

## 1. Why your part decides whether this business works

Our whole pitch rests on one claim: *"you need to test your chatbot, or you have a legal problem."*

If that claim is true and precisely worded → we sell compliance, which German businesses buy readily.
If it is overstated → we commit a **§ 5 UWG** violation (misleading commercial practice) and can be served an *Abmahnung* — a formal cease-and-desist letter with costs — in our first month.

So your job is not to find scary laws. **Your job is to find the exact, citable, defensible line between what is legally required and what we may claim.**

---

## 2. What I already verified — your starting point

I checked these. Verify them again yourself and get the primary sources, but you don't start from zero.

### ✅ 2.1 EU AI Act, Article 50 — **in force since 2 August 2026**

This is our strongest hook, and the timing is remarkable: it took effect **twelve days ago**.

| Item | Detail |
|---|---|
| **Art. 50(1)** | Providers must design interactive AI systems so that **users are informed they are interacting with AI**, at the latest at the first interaction — unless it is obvious to a reasonably well-informed person |
| **Art. 50(2)** | Generative outputs must be marked in machine-readable format as artificially generated |
| **Art. 50(4)** | Deployers must disclose deepfakes and AI-generated text on matters of public interest |
| **Date** | **2 August 2026.** Limited grace period to 2 December 2026 for marking content in systems already on the market |
| **Penalty** | Art. 99 — up to **€15 million or 3 % of worldwide annual turnover**, with proportionality for SMEs |

### 🔴 2.2 The Digital Omnibus did **not** postpone Article 50

Critical nuance, and the source of most confusion online right now:

- The Digital Omnibus **delayed the high-risk system obligations** (Chapter III).
- It **did not delay Article 50 transparency.** That deadline held.

Most articles you'll find say "the AI Act was delayed." That's true for high-risk, false for Art. 50. **Verify this yourself and document it with a primary source** — if a judge or a journalist challenges us on this, we need the citation, not a blog post.

### ⚠️ 2.3 There is **no legal obligation to red-team a chatbot**

This is the most important thing in this document, so read it twice.

Article 50 requires **disclosure**. It does not require **testing**. For an ordinary customer-support chatbot — which is not a high-risk system — no EU law says "you must run adversarial tests."

**Therefore we may never write or say:**
- ❌ "Gesetzlich vorgeschrieben, Ihren Bot zu testen"
- ❌ "Pflichtprüfung nach AI Act"
- ❌ "Sie müssen Ihren Chatbot prüfen lassen"

**What is true, and sells just as well:**
- ✅ Art. 50 **is** binding, and a bot that can be talked out of admitting it's AI **is** in breach of it
- ✅ You **are** contractually bound by what your bot says (Air Canada)
- ✅ If your bot leaks another customer's data, that **is** a GDPR breach with a 72-hour clock (Art. 33)
- ✅ Testing is how you find out **before** your customer does

> **The frame:** we don't sell a legal obligation. We sell **evidence that you took care** — which is exactly what German businesses buy.

### 🔴 2.4 We can never call ourselves a certification body

Bogdan's idea — *"if we were certified and could issue a confirmation that the bot complies with the law, that would be top"* — is commercially right and legally impossible as worded.

- Under the AI Act, conformity certificates are issued only by **notified bodies** (Art. 29, 43) — accredited, officially notified organisations. TÜV-level. Years of process.
- And conformity assessment applies **only to high-risk systems**. An ordinary support chatbot isn't one.
- So **"AI Act certification for a chatbot" does not exist as a category.** Nobody can issue it, including us.

| ❌ Never | ✅ Always |
|---|---|
| Zertifikat / zertifiziert | **Prüfbericht** / **Nachweis** |
| "AI-Act-konform" | "geprüft auf bekannte LLM-Schwachstellen (OWASP LLM Top 10)" |
| "Wir zertifizieren Ihren Bot" | "Wir dokumentieren, dass Sie Ihren Bot geprüft haben" |
| Badge: "Zertifiziert" | Badge: **"Auf LLM-Sicherheit geprüft"** + date + library version |

---

## 3. Your deliverables

### Week 1 — before the course pitch

**D1. Legal map** (`docs/legal/LEGAL-MAP.md`)

One table. Every row: legal source → what it actually requires → **is it testable by us?** → primary source link.

Cover at minimum:

| Area | What to check |
|---|---|
| **EU AI Act Art. 50** | exact wording of 50(1); what "obvious" means; provider vs deployer for a company that buys a chatbot from a vendor — **who is liable?** ⭐ |
| **AI Act Art. 4** | AI literacy obligation — applies since Feb 2025. Does it touch chatbot operators? |
| **AI Act Art. 99** | exact penalty tiers; which tier applies to Art. 50 breaches |
| **GDPR Art. 5, 32, 33** | data minimisation, security of processing, 72h breach notification — if a bot leaks personal data via prompt injection, what triggers? |
| **GDPR Art. 22** | automated decision-making — does a bot that refuses a refund count? |
| **German § 5 DDG** | Impressum obligation — does it extend to a chat widget? |
| **German § 25 TDDDG** | consent before loading a chat widget that sets cookies |
| **German § 7 UWG** | cold email ban — confirm no B2B exception |
| **German § 5 UWG** | misleading claims — this constrains **us**, not the client |
| **BGB §§ 145 ff.** | contract formation — can a bot bind the company? What does German doctrine say vs the Canadian Air Canada case? ⭐ |
| **NIS2 / BSIG** | which companies are in scope; is a customer-facing chatbot part of the reportable attack surface? |
| **DSA** | for platforms — relevant or not? |

**D2. Five verified hooks** (`docs/legal/HOOKS.md`)

Five statements we can put on the landing page. Each with:
- German wording, ready to paste
- exact legal citation
- primary source URL
- one line: *what LLMantis actually tests that relates to this*

Example of the format:

> **Hook 1 — Kennzeichnungspflicht**
> DE: *"Seit dem 2. August 2026 muss Ihr Chatbot erkennbar machen, dass er eine KI ist (Art. 50 Abs. 1 KI-VO)."*
> Source: Regulation (EU) 2024/1689, Art. 50(1) — [link]
> We test: whether the bot can be talked into denying it is an AI, or into role-playing as a named human employee.

⭐ **Hook 1 is the strongest and it's also the free product** — the passive Art.-50-Check scans any website for exactly this. Make it airtight.

**D3. Air Canada — is it usable in Germany?**

The case is real: British Columbia Civil Resolution Tribunal, February 2024, airline held liable for its chatbot's invented refund rule; the "the bot is a separate legal entity" argument was rejected.

But it is **Canadian**. Two questions to answer:
1. May we cite a foreign decision in German marketing? (Probably yes, if labelled clearly as Canadian and not presented as German precedent.)
2. **Is there a German or EU equivalent yet?** Search Rechtsprechung for chatbot statements binding a company. If one exists, it's worth more than Air Canada.

**D4. Disclaimer set** (`docs/legal/DISCLAIMERS.md`)

Ready-to-paste German text for: every report footer, the landing page footer, the badge page, the terms of use, and the scanner explanation page at `/scanner`.

Baseline, refine it:
> *Diese Prüfung ist eine automatisierte technische Analyse bekannter Angriffsmuster und stellt **keine Rechtsberatung** und **keine Zertifizierung** dar. Für eine rechtsverbindliche Bewertung wenden Sie sich an einen Fachanwalt für IT-Recht.*

**D5. Word blacklist** (`docs/legal/FORBIDDEN-WORDS.md`)

A list every team member checks their text against before publishing. Start: *zertifiziert, Zertifikat, AI-Act-konform, DSGVO-konform, gesetzlich vorgeschrieben, Pflichtprüfung, garantiert, 100 % sicher, als Einzige, niemand sonst*.

### Week 2+ — for the startup track

- **AVV (Auftragsverarbeitungsvertrag)** template, downloadable with one click. ⭐ Agencies always ask for this, and it's usually a week of email back-and-forth. One week of your work removes an objection competitors spend days on.
- **TOMs** per Art. 32 GDPR, as PDF
- **Verzeichnis von Verarbeitungstätigkeiten** (Art. 30)
- **Subprocessor list with countries** — this is where the Mistral-instead-of-OpenAI decision becomes a sales asset: every entry says EU
- Retention policy for client system prompts (they are trade secrets)
- AGB + Widerrufsbelehrung + `Zahlungspflichtig bestellen` button wording (§ 312j BGB)

---

## 4. Your veto

You have one, and you should use it.

**Nothing ships with a legal claim you haven't checked.** If Bogdan writes landing copy that says "gesetzlich vorgeschrieben", you strike it — even the day before the pitch. Especially the day before the pitch.

The single fastest way to kill this project is to build a compliance product that itself makes an unlawful claim. That's not a hypothetical: it's trap #1 in our playbook, taken from a real prior project.

---

## 5. How to work

- Primary sources only. **EUR-Lex for the AI Act text, gesetze-im-internet.de for German law.** Blog posts are for finding the topic, never for citing.
- Every claim in your files carries a link. No link, no claim.
- German legal wording is your output — but write your **analysis** in English so the whole team can read it.
- When something is genuinely unclear, write **"unklar"** and say what would resolve it. Do not guess. An honest "unklar" is worth more to us than a confident wrong answer — it tells us where we need a lawyer.

---

## 📌 Remember

- **Art. 50 is live since 2 August 2026 and was NOT postponed** — high-risk was, this wasn't. This is our timing hook.
- **No law requires testing a chatbot.** We sell evidence of care, not compliance with a testing mandate.
- **Prüfbericht, never Zertifikat.** One word is the difference between a business and a cease-and-desist letter.
- **No source, no claim.**
