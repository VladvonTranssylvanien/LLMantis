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

## Re-verified at commit f301d3e — new documentation-drift finding

`backend/config.py`, `backend/llm.py`, and `requirements.txt` are unchanged and the above still holds exactly. New this pass: `PLAYBOOK.md` and `PROJECT-STATE.md` both currently assert "Mistral is still the only provider `backend/llm.py` registers." This is factually wrong at the current commit — `llm.py`'s own docstring says it holds `mistral` and `azure`, and `PROVIDER` defaults to `azure`. `PROJECT-STATE.md` was edited as recently as today without this stale claim being caught, which is itself a small data point for BE-10 (change management) as well as this control. Not counted as a third sub-check failure (the underlying config facts are unaffected), but flagged as a recommendation — a governance reader who trusted the prose over the code would reach the wrong conclusion about which vendor governs production.
