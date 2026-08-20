# BE-09 — Evidence, Traceability and Data Integrity — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 70%**

## What was found

- `backend/main.py:169`: `library_version=report.get("library_version", "1.0")` — sourced from the real report dict, which itself carries `library_version: library.version` from `backend/scanner.py:234-245`'s `run_scan()` return.
- `backend/main.py:156`: `system_prompt=request.system_prompt` — the actual submitted prompt is now persisted, resolving the prior gap where this field was hardcoded to an empty string.
- `backend/main.py:151`: `target_name = request.api_url or "Prompt-based target"` — for `mode="model"/"prompt"` (the common case), `request.api_url` is empty, so the persisted `Target.name` is **always** the literal placeholder string `"Prompt-based target"`, never the human-readable name the user typed. That name is deliberately never sent in the `ScanRequest` payload (`frontend/index.html`) and is instead stitched onto the report client-side, after the fact, in the browser session that ran the scan.
- At-rest database encryption was not independently verified this session.

## Basis for 70%

2 of 3 countable sub-checks met (library version persisted correctly; tested prompt persisted correctly). 1 not met (target display name is a hardcoded placeholder in the common mode). At-rest encryption is excluded from this ratio and flagged separately.

## Re-verified at commit f301d3e

`backend/main.py` is byte-for-byte unchanged since the previous baseline; all three findings above hold exactly. Additionally confirmed this pass: `backend/models.py` stores `system_prompt` as a plain `Text` column, and no column- or database-level encryption exists anywhere in the codebase or `deploy/` configuration — this is now confirmed absent by direct inspection, not merely unverified from outside. Given `system_prompt` is explicitly documented elsewhere in the project as a customer trade secret, this moves from "unverified" to "a named gap" without changing the percentage, since the countable sub-check ratio is unaffected.
