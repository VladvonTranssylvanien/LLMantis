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

Core, highest-stakes claim (certification avoidance) is fully correct. Three separate, identified overstatements remain live and uncorrected. Citations underlying all claims (article numbers, case name/date/jurisdiction) are factually accurate — the defect is scope/framing, not fabrication.
