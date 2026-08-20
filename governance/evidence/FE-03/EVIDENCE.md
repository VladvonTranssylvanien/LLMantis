# FE-03 — User-Facing Security and Privacy — Evidence

**Compliance Status: NON-COMPLIANT**

**Compliance Percentage: 0%**

## What was found

`frontend/impressum.html` and `frontend/datenschutz.html` both contain, verbatim:

```
TODO — not legally reviewed. This page is a structural placeholder.
```

Both pages contain unfilled `{{TOKEN}}` fields for legally required information (e.g. `{{LEGAL_NAME}}`, `{{CONTACT_EMAIL}}`, `{{REGISTER_COURT}}`, `{{VAT_ID}}` in `impressum.html`; `{{HOSTING_PROVIDER}}`, `{{RETENTION}}`, `{{SUPERVISORY_AUTHORITY}}` in `datenschutz.html`).

## Why NON-COMPLIANT, not PARTIAL

The control's core requirement — real, complete, legally accurate disclosure content — is entirely unmet. The pages self-disclose their own incompleteness, which is honest, but does not satisfy § 5 DDG or GDPR Art. 13/14 in their current form.

## Gap confirmed by absence

No screenshot evidence is attached for this control — there is no compliant state to document. This is a documented gap, not an unexamined one.
