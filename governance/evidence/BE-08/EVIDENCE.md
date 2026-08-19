# BE-08 — Application and Network Security — Evidence

**Compliance Status: PARTIALLY COMPLIANT**

**Compliance Percentage: 50%**

## What was found

- `backend/netguard.py:assert_public_host()`: resolves every address a hostname maps to and rejects private/loopback/link-local (including the 169.254.169.254 cloud-metadata address)/multicast/reserved/unspecified ranges — a genuinely comprehensive check.
- Confirmed usage in `backend/art50check.py` (re-checked on every redirect hop) and `backend/art50engine.py` (gates the initial URL, plus a Playwright request-interception guard re-checking on every single network request the rendered page makes, specifically to defeat DNS-rebinding TOCTOU).
- **`backend/scanner.py` contains zero references to `netguard`, `assert_public_host`, or `is_private_url`** (confirmed by direct grep) — despite `netguard.py`'s own docstring explicitly claiming it covers "the passive Art.-50-Check... and the active api-mode scan (`backend/scanner.py`)." The only SSRF check for the active-scan path is a single, one-time `is_private_url()` call in `backend/main.py:1096`, evaluated once before a scan that then runs multiple attacks over several seconds, each performing its own fresh DNS resolution inside `httpx` with no re-check.
- `backend/main.py`: `Limiter(key_func=get_remote_address)` registered as app-level middleware; limits vary by endpoint (registration 5/min, login 10/min, Art.50 check 4/min) — confirmed per-IP, not a single shared site-wide bucket (the specific bug the project's own commit history records fixing).

## Basis for 50% — this is the session's highest-priority finding

Per the Governance V2 principle of assessing by code path, not by feature existence: SSRF protection is real and thorough on one path and **completely absent** on the other, despite shared documentation claiming full coverage. Rate limiting is solid. 1 of 2 major sub-areas (SSRF) has a serious, exploitable coverage gap on the higher-risk feature; the other (rate limiting) is sound.
