"""
Fetch the live-chat fingerprints engine.py uses.

    python tools/art50v2/fetch_signatures.py

Source: enthec/webappanalyzer, the maintained continuation of Wappalyzer's
fingerprint database after the original went private in August 2023. Category 52
is "Live chat" — 378 technologies, including the German vendors a hand-written
list keeps missing: MoinAI, Melibo, Kauz, Onlim, Solvemate, Cognigy, UserLike.

The result is gitignored. It is GPL-3.0 data and this repo is public, so
committing it would be redistribution; see .gitignore for the reasoning. Nothing
breaks without it — engine.py keeps its own asset-name and structural signals,
which are the two that actually fired on real German sites.
"""
from __future__ import annotations

import json
import string
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/enthec/webappanalyzer/main/src/technologies"
LIVE_CHAT = 52
KEEP = ("scriptSrc", "dom", "js", "xhr", "cookies", "html", "headers")
OUT = Path(__file__).parent / "livechat.json"


def main() -> None:
    found: dict[str, dict] = {}
    for shard in list(string.ascii_lowercase) + ["_"]:
        try:
            with urllib.request.urlopen(f"{BASE}/{shard}.json", timeout=20) as r:
                data = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"  {shard}.json: skipped ({type(e).__name__})")
            continue
        for name, spec in data.items():
            if LIVE_CHAT in (spec.get("cats") or []):
                found[name] = {k: spec[k] for k in KEEP if spec.get(k)}

    if not found:
        raise SystemExit("No live-chat technologies fetched — check network access.")

    OUT.write_text(json.dumps(found, ensure_ascii=False, indent=1), encoding="utf-8")
    signals: dict[str, int] = {}
    for spec in found.values():
        for k in spec:
            signals[k] = signals.get(k, 0) + 1
    print(f"{len(found)} live-chat technologies -> {OUT}")
    print("signals:", ", ".join(f"{k} {v}" for k, v in sorted(signals.items())))


if __name__ == "__main__":
    main()
