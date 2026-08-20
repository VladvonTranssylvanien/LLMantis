# Disclaimers

> Ready-to-paste disclaimer wording. Ownership: per `PLAYBOOK.md` Part V §11
> rule 5, any text containing "Gesetz", "Pflicht", "Art." or "§" — which
> includes every disclaimer below — is written and signed off by the GRC
> owner, not by Bogdan or by Claude Code. Treat the wording below as a
> baseline draft pending that sign-off, per `docs/KWABENA-GRC-BRIEF.md` D4,
> not as final, published copy.

## Status of this document

`UNDER REVIEW` — the baseline wording below is copied from
`docs/KWABENA-GRC-BRIEF.md` §3 (D4), which itself labels it "baseline, refine
it." No sign-off record exists in the repository at the time this governance
framework was implemented.

---

## Baseline disclaimer (German — report footer, landing page footer, badge page, terms of use, scanner explanation page)

> *Diese Prüfung ist eine automatisierte technische Analyse bekannter
> Angriffsmuster und stellt **keine Rechtsberatung** und **keine
> Zertifizierung** dar. Für eine rechtsverbindliche Bewertung wenden Sie sich
> an einen Fachanwalt für IT-Recht.*

English gloss (for internal review only — the shipped disclaimer stays
German, per `PLAYBOOK.md`'s documented exception for customer-facing text):

> This test is an automated technical analysis of known attack patterns and
> does not constitute legal advice or a certification. For a legally binding
> assessment, consult a qualified IT-law attorney.

## Where this disclaimer must appear

Per `docs/KWABENA-GRC-BRIEF.md` D4, at minimum:

- [ ] Every generated report (`frontend/report.html`) — **not yet confirmed present in the current template; verify before shipping any report to a customer.**
- [ ] The landing page footer (`frontend/landing.html`) — **not yet confirmed present; verify.**
- [ ] The badge page (badge feature not yet built, per `PROJECT-STATE.md` §6 deferred items — this requirement applies once it ships).
- [ ] The terms of use (not yet found in this repository).
- [ ] The `/scanner` explanation page referenced in `tools/art50check.py`'s User-Agent string (`LLMantis-Checker/0.1 (+https://llmantis.de/scanner)`) — **this page does not appear to exist yet in `frontend/`.**

This governance framework records where the disclaimer is *required* to
appear per the project's own documents. It does not assert that it currently
does appear everywhere — that must be verified against the live templates
before each surface ships to a customer.

## Additional disclaimer — legal citation currency

Because `LEGAL-MAP.md` records several claims as `UNDER REVIEW` or
`UNCLEAR` (notably: whether the Digital Omnibus affects Art. 50, and whether
any law requires red-teaming a chatbot), any report or marketing copy that
cites these must not present them as settled fact. Suggested guard sentence,
pending GRC sign-off:

> *Rechtliche Einschätzungen in diesem Bericht basieren auf öffentlich
> zugänglichen Quellen zum Zeitpunkt der Prüfung und ersetzen keine
> individuelle Rechtsberatung.*

## What this disclaimer does NOT cover

It does not substitute for:

- A data processing agreement (AVV) between PromptGuard and a customer.
- Retention-policy disclosure for stored system prompts/scan evidence.
- Any claim-specific caveat required by `LEGAL-MAP.md` (e.g. the Air Canada
  precedent must carry its own "Canadian, illustrative only" label wherever
  it is cited, in addition to this general disclaimer).
