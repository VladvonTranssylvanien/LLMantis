# Controlled Wording — Forbidden and Restricted Terms

> Every team member checks copy against this list before publishing, per
> `docs/KWABENA-GRC-BRIEF.md` D5 and `PLAYBOOK.md` Part III §5. This applies
> to UI text, comments, variable names, documentation, commit messages,
> marketing copy, and this governance framework's own reports.

## Rule

These terms require **evidence and GRC sign-off before publication** — they
are not an absolute ban on the underlying concept (e.g. it is fine to discuss
*why* something isn't certified), but the exact wording below must not appear
in anything customer-facing without review, per
`GOVERNANCE-IMPLEMENTATION.md` Step 9.

**No source, no claim.** If a word below is used, the sentence containing it
must carry a citation that has itself been marked `VERIFIED` in
`LEGAL-MAP.md` — not `UNDER REVIEW` or `UNCLEAR`.

## Controlled terms (German)

| Term | Why it is controlled |
|---|---|
| `zertifiziert` | Certification is a legal category issued only by notified bodies for high-risk systems (AI Act Art. 29, 43). PromptGuard is not one and cannot become one. |
| `Zertifikat` | Same as above. |
| `AI-Act-konform` | Implies a compliance status that a technical scan cannot establish. |
| `DSGVO-konform` | Same — GDPR compliance is a legal determination, not a scan output. |
| `gesetzlich vorgeschrieben` | No identified law requires red-teaming a chatbot (see `LEGAL-MAP.md`). Using this phrase for testing itself would misstate the law. |
| `Pflichtprüfung` | Same reasoning — implies a mandatory-testing regime that has not been established to exist. |
| `garantiert` | Absolute-outcome language; § 5 UWG risk (misleading commercial practice). |
| `100 % sicher` | No security testing product can claim 100% security; false-negative risk always exists. |
| `als Einzige` | Uniqueness/sole-provider claims (Alleinstellungsbehauptung) are unprovable and a § 5 UWG risk. |
| `niemand sonst` | Same as above. |

## Controlled terms (English equivalents)

The same reasoning applies regardless of language. Per `README.md` and
`PLAYBOOK.md`, these are banned in code, comments, variable names,
documentation and commit messages, not only customer-facing copy:

| Term | Why it is controlled |
|---|---|
| `certified` / `certification` | See `zertifiziert` above. |
| `AI-Act-compliant` / `AI Act compliant` | See `AI-Act-konform` above. |
| `GDPR-compliant` / `GDPR compliant` | See `DSGVO-konform` above. |
| `legally mandatory` / `legally required` (applied to testing itself) | See `gesetzlich vorgeschrieben` above. |
| `guaranteed` | See `garantiert` above. |
| `100% secure` / `completely secure` | See `100 % sicher` above. |
| `the only one` / `nobody else does this` | See `als Einzige` / `niemand sonst` above. |

## Correct alternatives

| Instead of | Use |
|---|---|
| "Zertifikat" / "certified" | **Prüfbericht** / **Nachweis** / "test report" |
| "AI-Act-konform" / "AI-Act-compliant" | "geprüft auf bekannte LLM-Schwachstellen (OWASP LLM Top 10)" / "tested against known LLM vulnerabilities (OWASP LLM Top 10)" |
| "Wir zertifizieren Ihren Bot" | "Wir dokumentieren, dass Sie Ihren Bot geprüft haben" |
| "Gesetzlich vorgeschrieben" (re: testing) | "Art. 50 AI Act gilt seit dem 2. August 2026. Wir prüfen, ob Ihr Bot die Kennzeichnungspflicht einhält." (disclosure obligation only — see `LEGAL-MAP.md`) |

## Enforcement in this repository

This list is currently enforced by **manual review only** (the GRC owner
proofreading copy before publication, per `PLAYBOOK.md` Part V §11 rule 5 and
Part VII "Traps"). No automated lint/CI check scans for these terms in
tracked files as of this governance framework's initial implementation — see
`GOVERNANCE_REPORT.md`, control LOG-01/GOV-10, for the related gap. Adding an
automated grep-based check (e.g. a CI step scanning `frontend/`, `docs/`, and
commit messages for the terms above) would close this gap and is a
recommended next step, not yet implemented.
