# BE-02 — AI Attack Library Governance — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 70%**

## What was found

- `attacks/attacks.yaml:19`: `version: "2.0"`, 78 attacks.
- `attacks/attacks_short.yaml:19`: `version: "1.4"`, 21 attacks — this is the file the live app loads by default (`backend/config.py`: `ATTACK_LIBRARY` default).
- `backend/attacks.py:_validate()` enforces unique id, declared category, valid severity — confirmed extended to report which filename failed validation, applied consistently to both libraries.
- No automated test file exercises this validation logic anywhere in the repository (confirmed by direct search — only `tools/art50v2/test_fixtures.py` exists outside governance/, unrelated to attack validation).
- Disambiguating which library actually produced a given grade requires checking both a version number and a library name field together; the version number alone is not self-explanatory across two coexisting libraries.

## Basis for 70%

The validation logic itself is sound and applied consistently (strong positive). The two deductions are: no test protects it, and version disambiguation requires two fields rather than one clear indicator.
