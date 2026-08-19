# BE-01 — AI Component and Provider Governance — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 50%**

## What was found

- `backend/config.py:31`: `PROVIDER = os.getenv("PROVIDER", "azure")` — default provider is now a generic Azure OpenAI-compatible endpoint.
- `backend/config.py:41-43`: `AZURE_URL`, `AZURE_KEY`, `AZURE_AUTH` — the URL is fully operator-supplied ("copied verbatim from the Azure deployment page"), with no region validation or enforcement anywhere in code.
- `backend/llm.py`: `mistral` remains registered as an alternative provider; `anthropic` has been fully removed (confirmed absent from `requirements.txt` and `_PROVIDERS`).
- `PLAYBOOK.md` §1 and `PROJECT_COMPLETE_OVERVIEW.md`: the project's prior "EU-only stack" invariant has been explicitly withdrawn by the team — *"No vendor prohibition applies to this project any more, and data residency is not a selling point."*

## Basis for 50%

Sub-check 1 (component/provider identifiable): met. Sub-check 2 (configuration consistent with a documented residency policy): not met — no current policy exists to be consistent with, since the prior one was explicitly withdrawn and not replaced. 1 of 2 = 50%.
