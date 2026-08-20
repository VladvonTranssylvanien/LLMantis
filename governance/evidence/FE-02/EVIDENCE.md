# FE-02 — Legal and Regulatory Information — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 50%**

## What was found

Certification/conformity language is correct and consistent: `frontend/index.html` footer and `frontend/report.html` disclaimer both correctly state "Prüfbericht, not a certification" and correctly restrict conformity certificates to notified bodies / high-risk systems (matching EU AI Act Art. 43).

Three specific claims on `frontend/landing.html` remain overstated relative to their verified status, and were **not corrected on the live page** (only `docs/legal/LEGAL-MAP.md` and `docs/legal/HOOKS.md` were corrected earlier in this project's governance work, not the marketing copy itself):

1. **FACT 02 (Air Canada):** presented as a general rule ("Was Ihr Bot sagt, sagen Sie") without a "Canadian precedent, illustrative only, not binding in Germany/EU" qualifier.
2. **grcLead:** "Keine Vorschrift verlangt, einen Chatbot testen zu lassen" ("No regulation requires having a chatbot tested") is stated as flat fact where the project's own legal analysis (`docs/legal/LEGAL-MAP.md`, row on Art. 55/red-teaming) marks this specific claim as unresolved.
3. **FACT 03 (GDPR 72h):** states the 72-hour notification duty as an unconditional consequence of any data disclosure, omitting Art. 33's risk-based conditionality ("unless... unlikely to result in a risk to the rights and freedoms of natural persons").

## Basis for 50%

Core, highest-stakes claim (certification avoidance) is fully correct. Citations underlying all claims (article numbers, case name/date/jurisdiction) are factually accurate — the defect is scope/framing, not fabrication.

## Re-verified at commit f301d3e

Items 1 (Air Canada) and 3 (GDPR 72h) above are confirmed unchanged, byte-for-byte, in `frontend/landing.html` — both still sit under a `<!-- REVIEW: Kwabena -->` marker, i.e. already flagged internally but not yet fixed. Item 2 ("no regulation requires testing," previously stated as flat fact) no longer appears verbatim in the current copy; the underlying risk category is now governed by `docs/legal/FORBIDDEN-WORDS.md`, which explicitly bans the phrase and tracks claim status. This is genuine process improvement, but it is infrastructure, not a fix — it has not yet been applied to correct the two claims its own sibling document, `LEGAL-MAP.md`, already marks as open. Score held at 50%, not raised, because the two highest-visibility overstatements are unchanged and the new framework's value is currently only in what it *would* catch, not in what it has fixed.
