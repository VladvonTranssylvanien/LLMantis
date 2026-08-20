# Legal Map

> Status of legal claims relevant to PromptGuard / LLMantis. This document
> implements the "no source, no claim" rule from `governance/README.md` and
> Part III of `PLAYBOOK.md`.
>
> This is a governance artifact, not legal advice. See `DISCLAIMERS.md`.

## How to read this table

Each row separates five things, per `GOVERNANCE-IMPLEMENTATION.md` Step 8:

1. **Legal requirement** — what the source actually says.
2. **Applicability** — who it binds (provider, deployer, operator of a chatbot).
3. **Technical testability** — can an automated scan measure compliance with it at all?
4. **What PromptGuard tests** — the actual mechanism in this repository, if any.
5. **What PromptGuard may claim** — the sentence that is safe to publish, if any.

Each row is then classified along two further, independent dimensions:

**Authority Type** — what kind of source this is:

| Authority Type | Meaning |
|---|---|
| `PRIMARY AUTHORITY` | Official legislation/regulation text, an official government/regulator source, or the text of a court/tribunal decision. |
| `CASE LAW / TRIBUNAL DECISION` | A specific court or tribunal ruling, cited by name and neutral citation. |
| `INTERNAL POLICY` | A PromptGuard/LLMantis project decision (e.g. `PLAYBOOK.md`), not a legal source. |
| `BEST PRACTICE` | An industry convention or voluntary standard (e.g. ISO/IEC frameworks), not a legal requirement. |
| `SECONDARY COMMENTARY` | Law-firm publications, professional associations, or legal-explainer sites — useful for interpretation, never the sole authority for "the law requires X." |

**Status** — how confirmed the claim is:

| Status | Meaning |
|---|---|
| `VERIFIED` | Confirmed directly against a primary authority (official text or decision). |
| `UNDER REVIEW` | The relevant authority may exist and may be primary, but confirmation, applicability, or full independent verification is not yet complete. |
| `UNSUPPORTED` | No source — primary or secondary — was found addressing this specific claim in either direction. Do not assert it either way. |

**A note on scope:** this file has been through several rounds of correction, each approved individually. A small number of rows still carry legacy status values (`UNCLEAR`, `NOT APPLICABLE`) from before the three-value `Status` vocabulary above was adopted, because no correction was yet approved for those specific rows. They are marked `⚠ legacy status — not yet migrated` below rather than silently reclassified. See "Known gap in this legal map" at the end of this file for the current list.

This governance framework does not perform new legal research on its own initiative. It records the status of claims as already assessed, either inside this repository (`docs/KWABENA-GRC-BRIEF.md`, `PROJECT-STATE.md §3`) or through primary-source checks performed and explicitly approved during this framework's review process.

---

## Legal sources

| Area | What it actually requires | Applicability | Technically testable by PromptGuard? | What PromptGuard tests | What PromptGuard may claim | Authority Type | Status |
|---|---|---|---|---|---|---|---|
| **EU AI Act Art. 50(1)** (Regulation (EU) 2024/1689) | **Providers** of an AI system intended to interact directly with natural persons must ensure those persons are informed they are interacting with an AI system, unless obvious to a reasonably well-informed person. In force since 2 August 2026. | Binds the **provider** that designs/builds the AI system. Whether this duty passes through to a **deployer** (a company that buys and operates a chatbot built by a vendor) is a separate, unresolved question — not answered by Art. 50(1) itself. | Yes — passively: does the widget disclose AI nature on first contact. This is exactly what `tools/art50check.py` measures. | The Art.-50-Check (`tools/art50check.py`) checks, via a single passive page GET, whether a chat widget's page HTML discloses AI nature and whether a privacy link sits near it. It is a coarse heuristic — see the caveat below. | "Art. 50(1) AI Act obligates AI system providers to ensure disclosure of AI interaction, in force since 2 August 2026. We check whether a chatbot discloses that it is AI." Do not assert which party (vendor vs. the company operating the bot) bears the Art. 50(1) duty without further verification. | `PRIMARY AUTHORITY` | `VERIFIED` (the provider obligation and its wording) — `UNDER REVIEW` (whether/how it passes through to a deployer/customer) |
| **Digital Omnibus effect on Art. 50** | Reported to delay high-risk system obligations (AI Act Chapter III / Annex III) but *not* Art. 50 transparency obligations. | Same as above. | N/A (this is a question about which obligations are in force, not something a scan measures). | Nothing — this is a legal-research question, not a technical check. | Do not state this as settled without independent re-verification. | `SECONDARY COMMENTARY` ⚠ legacy status — not yet migrated | `UNDER REVIEW` — unchanged in this round; not part of the approved corrections, though stronger evidence exists — see note below. |
| **EU AI Act Art. 55 — adversarial testing / red-teaming obligation** | Providers of general-purpose AI (GPAI) models with *systemic risk* must conduct and document adversarial testing, including red-teaming, to identify and mitigate systemic risks. | Binds GPAI model providers designated as systemic-risk (per Art. 51 / Annex XIII) — e.g. a frontier-model vendor. Does not, by its own terms, bind a company that merely calls such a model via API. | N/A — this is a question of who is legally obligated, not something PromptGuard's scan measures. | Nothing — this provision does not describe a testable property of a customer's chatbot. | A legal duty to red-team does exist in the AI Act, but for systemic-risk GPAI model *providers*. PromptGuard's own red-teaming is a service offering, not compliance with this specific provision. | `PRIMARY AUTHORITY` | `VERIFIED` |
| **Whether Art. 55 (or any other provision) extends a red-teaming duty to PromptGuard or an ordinary chatbot deployer** | Not established either way. | Open question — no source found extending or excluding this. | N/A. | Nothing — this is a legal-research question, not a technical check. | Do not claim PromptGuard's customers have, or lack, a red-teaming legal obligation. Correct framing: "Testing is how you find out before your customer does" — evidence of care, not compliance with a mandate. | `PRIMARY AUTHORITY` — the underlying source under assessment (Art. 55) is itself a primary authority; what's unresolved is its applicability, not its authenticity. | `UNDER REVIEW` |
| **EU AI Act Art. 99 — penalties** | Fines up to €15,000,000 or 3% of worldwide annual turnover, with proportionality for SMEs, for certain violations. | Providers/deployers found in breach of specific AI Act obligations. | N/A — a penalty tier is not something a scan measures. | Nothing. | May be cited as a stated maximum, without implying every Art. 50 breach reaches this ceiling automatically. | `PRIMARY AUTHORITY` ⚠ legacy status — not yet migrated | `UNDER REVIEW` — unchanged in this round; stronger evidence exists (Art. 50 confirmed to map to the mid, "operator obligations" tier) but this row was not part of the approved corrections. |
| **AI Act Art. 29, 43 — conformity certification** | Conformity certificates are issued only by accredited "notified bodies," and only for high-risk systems. | Notified bodies; high-risk AI system providers. Does **not** apply to an ordinary support chatbot. | N/A. | Nothing — this fact is the reason PromptGuard does **not** offer certification. | PromptGuard must never claim to certify, or to confirm legal compliance. See `docs/legal/FORBIDDEN-WORDS.md`. | `PRIMARY AUTHORITY` | `VERIFIED` |
| **GDPR Art. 5, 32, 33 (data minimisation, security of processing, 72h breach notice)** | If a bot leaks personal data (e.g. via prompt injection), notification obligations and security-of-processing duties may be triggered. | Data controllers/processors. | Partially — PromptGuard's data-leakage attack category can demonstrate *that* a leak is possible, not whether GDPR's specific triggers/thresholds are met in a given case. | The `data_leakage` attack category (`attacks/attacks.yaml`) and the deterministic canary-match layer (`backend/judge.py`) can prove a specific string leaked. Whether that string is "personal data" under GDPR, and whether a 72-hour clock started, is a legal question outside scope. | "If your bot can be made to leak a planted secret, that is a technical fact we can prove with a string match. Whether it triggers a GDPR notification duty is a question for counsel." | `PRIMARY AUTHORITY` ⚠ legacy status — not yet migrated | `UNDER REVIEW` — unchanged in this round; not part of the approved corrections. |
| **GDPR Art. 22 — automated decision-making** | Restricts certain solely-automated decisions with legal/significant effects. | Data controllers. | Open question: does a bot refusing a refund count as such a decision? | Nothing implemented. | No claim. | `PRIMARY AUTHORITY` ⚠ legacy status — not yet migrated | `UNCLEAR` — legacy value; not part of the approved corrections, and `UNCLEAR` is no longer in the adopted Status vocabulary. Needs an explicit decision on whether this becomes `UNDER REVIEW` or `UNSUPPORTED`. |
| **German § 5 UWG (misleading commercial practice)** | Prohibits misleading claims in commercial communication. | Constrains **PromptGuard itself** as a seller, not the customer's chatbot. | N/A (a constraint on our own marketing, not a target-testable property). | Enforced structurally by `docs/legal/FORBIDDEN-WORDS.md` and Kwabena's sign-off requirement (`PLAYBOOK.md` Part V §11 rule 5). | PromptGuard must not overstate legal risk, uniqueness, or certification status in its own marketing. | `PRIMARY AUTHORITY` | `VERIFIED` |
| **German § 7 UWG (email advertising)** | Email advertising requires prior express consent (§7(2) no. 2 UWG). A narrow exception exists under §7(3) for an existing customer relationship — limited to similar products/services, no prior objection from the customer, and clear opt-out disclosed both at collection and at every subsequent use. This is **not** a general B2B exemption. | PromptGuard's own outbound sales process. | N/A — a business-process constraint, not something the scanned product tests. | Nothing to test in code. | Internal process rule should read: cold outbound email requires prior consent, with only a narrow existing-customer exception — not "no B2B exception, full stop." (`PLAYBOOK.md` should be corrected to match; out of scope for this edit.) | `PRIMARY AUTHORITY` | `VERIFIED` |
| **Air Canada** (*Moffatt v. Air Canada*, 2024 BCCRT 149) | A company was held liable for its chatbot's incorrect statement to a customer; the tribunal rejected the argument that the chatbot was a separate entity responsible for its own actions. Holding paraphrased here — no verbatim quote or paragraph number is used, as the tribunal decision's exact text has not been independently fetched and confirmed. | Canadian precedent; not binding in Germany/EU. Whether a German/EU equivalent case exists is a separate, still-open question. | N/A. | The `excessive_agency` attack category tests whether a bot confirms refunds/binding offers it has no authority to grant (`agency_refund`, `agency_binding_offer` in `attacks/attacks.yaml`). | May be cited **only** as a foreign illustrative precedent, explicitly labelled Canadian, never presented as German/EU law or as general AI governance law. | `CASE LAW / TRIBUNAL DECISION` | `VERIFIED` (the case, its citation, and its outcome) |
| **German § 5 DDG (Impressum obligation)** | Requires provider identification (Impressum) for certain online services. | Whether it extends to a chat widget specifically is an open question. | N/A. | Nothing implemented; `tools/art50check.py` records whether an Impressum link exists near the widget, as a passive observation, not a legal conclusion. | No compliance claim; observational data point only. | `PRIMARY AUTHORITY` ⚠ legacy status — not yet migrated | `UNCLEAR` — legacy value; not part of the approved corrections. |
| **German § 25 TDDDG (consent before cookie-setting widgets)** | Consent may be required before a widget that sets cookies loads, except for technically-necessary cookies. | Chatbot operators using cookie-setting widgets. | Partially — `tools/art50check.py` records presence of a widget and a nearby privacy link, but does not measure cookie timing/consent-gating (this requires JS/runtime inspection, not a single passive GET). | Nothing at cookie-timing granularity today. | No claim beyond what is actually measured (widget presence, disclosure text, privacy-link proximity). | `SECONDARY COMMENTARY` — multiple independent legal-database mirrors (not the official government source) agree on the wording; a direct fetch of the official text was attempted and returned a 404. | `UNDER REVIEW` — **PRIMARY SOURCE NOT FULLY VERIFIED** |
| **NIS2 / BSIG scope** | Determines which companies fall under critical-infrastructure cybersecurity obligations. | Large-scale/critical-sector operators. Whether a customer-facing chatbot is "reportable attack surface" under it is **not addressed by any source found**. | N/A. | Nothing implemented. | Do not make a definite claim, in either direction, about whether PromptGuard or a customer's chatbot is a reportable attack surface under NIS2/BSIG. | `SECONDARY COMMENTARY` (general NIS2/BSIG background only — no source, primary or secondary, addresses chatbot-specific applicability) | `UNSUPPORTED` |
| **DSA (Digital Services Act)** | Applies to certain platform/intermediary obligations. | Relevance to a single-company customer-support chatbot is unresolved; general commentary suggests standalone chatbots not embedded in a larger intermediary platform may sit outside the DSA's direct platform obligations, but this is not confirmed against primary text. | N/A. | Nothing implemented. | No claim. | `SECONDARY COMMENTARY` | `UNDER REVIEW` |
| **AI Act Art. 4 — AI literacy obligation** | In force since February 2025; obligation on providers **and** deployers to ensure staff AI literacy "to their best extent." | Whether/how it touches chatbot *operators* specifically (vs. developers) is an open question. | N/A. | Nothing implemented. | No claim. | `PRIMARY AUTHORITY` ⚠ legacy status — not yet migrated | `UNCLEAR` — legacy value; not part of the approved corrections. |

---

## Explicit non-claims

The following must **never** be stated as fact by PromptGuard, its reports, or its marketing, regardless of scan results (cross-reference `docs/legal/FORBIDDEN-WORDS.md`):

- That a passing (`A`/`B`) grade constitutes legal compliance with the AI Act, GDPR, or any other statute.
- That red-teaming a chatbot is a legal obligation for PromptGuard's customers (Art. 55 imposes such a duty only on systemic-risk GPAI model providers — see above).
- That PromptGuard acts as a certification body, or that its report is a certificate.
- That the Digital Omnibus's delay of high-risk obligations affects Article 50 (this repository's own research treats this as still requiring independent primary-source confirmation, not as settled).
- That Art. 50(1)'s disclosure duty definitely falls on the deployer/customer rather than the provider — this is unresolved, not decided in the customer's favor or against them.
- That *Moffatt v. Air Canada* is German, EU, or generally binding AI governance law — it is a Canadian tribunal decision, citable only as foreign illustrative precedent.
- That PromptGuard or a customer's chatbot is, or is not, a reportable attack surface under NIS2/BSIG — no source addresses this either way.

## Known gap in this legal map

Rows marked `⚠ legacy status — not yet migrated` still carry the previous four-value vocabulary (`UNCLEAR`, and formerly `NOT APPLICABLE`) because no correction has yet been approved for them under the current three-value `Status` vocabulary (`VERIFIED` / `UNDER REVIEW` / `UNSUPPORTED`). As of this edit, that applies to:

- Digital Omnibus effect on Art. 50 (row above `Status` unchanged, despite stronger evidence being available)
- EU AI Act Art. 99 (row above `Status` unchanged, despite stronger evidence being available)
- GDPR Art. 5, 32, 33 (row above `Status` unchanged)
- GDPR Art. 22 (`UNCLEAR`, needs a decision)
- German § 5 DDG (`UNCLEAR`, needs a decision)
- AI Act Art. 4 (`UNCLEAR`, needs a decision)

Closing these requires either (a) approving the status update for rows where stronger evidence already exists, or (b) a fresh decision on how to re-classify the remaining `UNCLEAR` rows under the new three-value vocabulary. Neither has been requested yet, so this file does not do either on its own initiative.
