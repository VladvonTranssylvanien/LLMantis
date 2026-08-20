# Marketing Hooks — Legal/Compliance Claims

> Every hook here must satisfy "no source, no claim" (see `governance/README.md`
> and `LEGAL-MAP.md`). Each hook lists its German wording, its citation, and
> exactly what PromptGuard technically tests that relates to it. Nothing here
> may be published without sign-off from the GRC owner (`PLAYBOOK.md` Part V
> §11 rule 5: "Kwabena writes all legal wording").

Per `docs/KWABENA-GRC-BRIEF.md` §3 (D2), the target for this deliverable is
five verified hooks. At the time this governance framework was implemented,
**one** hook has full drafted wording with a citation in the repository's own
research notes; the remaining four are not yet drafted. This document records
that state honestly rather than inventing the missing four.

---

## Hook 1 — Kennzeichnungspflicht (disclosure obligation)

**Status: `UNDER REVIEW`** — wording and citation both drafted in
`docs/KWABENA-GRC-BRIEF.md` §3; not yet independently re-verified against a
primary EUR-Lex citation link inside this repository.

Art. 50(1) obligates the **provider** of the AI system, not automatically the
**deployer** (a company operating a chatbot bought from a vendor). See
`docs/legal/LEGAL-MAP.md`'s Art. 50(1) row — the wording below is phrased at
the disclosure obligation itself and should not be read as assigning
liability to any specific party in the provider/deployer chain.

- **German wording (ready to paste, pending sign-off):**
  > "Seit dem 2. August 2026 muss Ihr Chatbot erkennbar machen, dass er eine KI ist (Art. 50 Abs. 1 KI-VO)."
- **Citation:** Regulation (EU) 2024/1689, Art. 50(1).
- **What PromptGuard actually tests:** whether the bot can be talked into
  denying it is an AI, or into role-playing as a named human employee
  (`jailbreak` category attacks in `attacks/attacks.yaml`, e.g. `jb_dan`), and
  — passively, with no attack sent — whether a public-facing chat widget
  discloses its AI nature at all (`tools/art50check.py`).
- **Why this is the strongest hook:** it is also the free product. The
  passive Art.-50-Check requires no ownership verification because it is a
  single ordinary page view, not an attack (see `PLAYBOOK.md` Part II §4).

---

## Hooks 2–5 — not yet drafted

`docs/KWABENA-GRC-BRIEF.md` §3 (D2) calls for four more hooks in the same
format (Air Canada / contractual bindingness; GDPR Art. 33 / 72-hour breach
clock; and others to be chosen). As of this governance framework's initial
implementation:

| Candidate | Status | Why it is not yet a published hook |
|---|---|---|
| Air Canada — contractual bindingness of chatbot statements | `UNCLEAR` | Real Canadian precedent (BC Civil Resolution Tribunal, Feb 2024) exists and is documented in `PROJECT-STATE.md` and `LEGAL-MAP.md`, but `docs/KWABENA-GRC-BRIEF.md` D3 flags an open question — whether a German/EU equivalent case exists — as unresolved. Publish only with an explicit "Canadian precedent, illustrative only" label until that is resolved. |
| GDPR Art. 33 — 72-hour breach notification | `UNDER REVIEW` | Article number is real and cited in `PLAYBOOK.md`/`LEGAL-MAP.md`, but no primary-source link or German-wording draft exists yet in this repository. |
| AI Act Art. 99 — penalty ceiling | `UNDER REVIEW` | See `LEGAL-MAP.md` row on Art. 99 — which penalty tier applies to an Art. 50 breach specifically is an open question per `docs/KWABENA-GRC-BRIEF.md` D1. |
| A fifth hook | not started | No candidate topic has been recorded anywhere in the repository. |

**Action required:** the GRC owner should draft these following Hook 1's
format (German wording + citation + primary source URL + "what PromptGuard
tests" line) before they are used in any customer-facing copy. This governance
framework flags the gap; it does not fabricate legal marketing claims to fill
it.
