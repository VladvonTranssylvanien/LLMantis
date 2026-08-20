# BE-08 — Application and Network Security — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 45%**

## What was found

- `backend/netguard.py:assert_public_host()`/`is_private_url()`: resolves every address a hostname maps to and rejects private/loopback/link-local (including the 169.254.169.254 cloud-metadata address)/multicast/reserved/unspecified ranges — a genuinely comprehensive check. `backend/art50check.py` (the file this evidence previously cited as a consumer) was deleted on 18.08; its guarded behavior is now inside `backend/art50engine.py`, which gates the initial URL and additionally runs a Playwright request-interception guard re-checking every single network request the rendered page makes — specifically to defeat DNS-rebinding TOCTOU.
- **`backend/scanner.py` still contains zero references to `netguard`, `assert_public_host`, or `is_private_url`** (re-confirmed by direct grep at commit f301d3e) — despite `netguard.py`'s own docstring claiming it covers both the passive check and the active api-mode scan. The only SSRF check for the active-scan path is a single, one-time `is_private_url()` call in `backend/main.py`, evaluated once before a scan that then runs multiple attacks over several seconds, each performing its own fresh DNS resolution inside `httpx` with no re-check. `backend/scanner.py`'s 54-line diff since the previous baseline is entirely unrelated (error-message wording, severity escalation, a new `secrets` field) — none of it touches the outbound HTTP call.
- `backend/main.py`: `Limiter(key_func=get_remote_address)` registered as app-level middleware; limits vary by endpoint (registration 5/min, login 10/min, Art.50 check 4/min) — confirmed per-IP, unchanged and solid.

## Two facts that temper, but do not close, the gap

- `PROJECT-STATE.md` (item 14 of its known-issues table, updated today) already self-discloses this exact DNS-rebinding gap by name, with the precise code locations, an assigned owner, and an explicit fix condition — the opposite of an undisclosed finding.
- The same entry states the scan endpoint currently sits behind the site's Basic-Auth, so the gap is not reachable by an anonymous caller today, even though the underlying code path is unguarded.

## Basis for 45%

Per the Governance V2 principle of assessing by code path, not by feature existence: SSRF protection remains real and thorough on the Art. 50 Check path and **fully absent** on the active-scan path, unchanged since the previous pass. Rate limiting remains sound. The score is set slightly below the previous pass's 50% because closer reading shows the one admission-time check that exists is weaker than "50% partial" implied (no re-validation across a multi-request scan) — partially offset, but not neutralized, by the honest self-disclosure and the temporary Basic-Auth compensating control, both newly confirmed this pass.
