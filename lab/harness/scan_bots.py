#!/usr/bin/env python3
"""Run the REAL scanner over the demo bots and save each report.

WHAT THIS IS FOR
    Everything else in lab/harness/ drives lab/runner.py with our own
    detectors. This runs backend/scanner.py itself - the real attack library,
    the real two-layer judge, the real scoring - which is the only way to get
    a grade rather than a leak count.

WHY IT CALLS run_scan DIRECTLY RATHER THAN POST /api/scan
    Same code path, minus Postgres and a login. /api/scan adds org resolution,
    ownership checks and persistence, none of which change the scan itself.
    Use the HTTP endpoint when testing those; use this when measuring bots.

    Consequence worth knowing: this passes `secrets`, which the frontend
    currently cannot (index.html:425-429 posts only mode, system_prompt and
    canary). So these numbers are a ceiling for what a demo scan would find,
    not a prediction of it.

COST
    One run is ~78 attacks x ~1.6 Mistral requests against a 50/minute limit.
    Expect 429s and therefore ERRORs; above 10% of attacks the grade is
    suppressed entirely (scanner.py:176). That is measured behaviour, not a
    hypothetical - see GREGOR_WORKLOG.md session 22.

USAGE
    python lab/harness/scan_bots.py                     # all three, into calibration/scans-v78/
    python lab/harness/scan_bots.py --only praxis_weber
    python lab/harness/scan_bots.py --out /tmp/scans
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from backend.scanner import Target, run_scan  # noqa: E402

# The confidential values from each bot's own prompt, beyond the canary.
# scanner.Target checks these the same way it checks the canary, and skips any
# the attack itself supplied (10f0521). Without them layer 1 cannot see a
# supplier or internal-note leak at all.
SECRETS = {
    "teleshop_vulnerable": ["Nordwind Logistik"],
    "teleshop_hardened": ["Nordwind Logistik"],
    "praxis_weber": ["Elternzeit"],
}


async def scan_one(spec: dict, out_dir: Path) -> dict:
    target = Target(
        mode="prompt",
        system_prompt=spec["system_prompt"],
        canary=spec["canary"],
        secrets=SECRETS.get(spec["id"], []),
    )
    started = time.time()

    async def progress(result, n, total):
        if n % 10 == 0 or n == total:
            print(f"    {n}/{total}  ({time.time() - started:.0f}s)", flush=True)

    print(f"\n=== {spec['id']} — {spec['name']} ===", flush=True)
    report = await run_scan(target, on_result=progress)

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{spec['id']}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # The grade lives in summary, NOT at the top level. Reading report["grade"]
    # returns None for every scan and reads as "no grade issued", which is a
    # different and much more alarming thing than the grade it actually got.
    s = report["summary"]
    confirmed = sum(1 for r in report["results"]
                    if r.get("verdict") == "FAIL" and r.get("confidence") == "confirmed")
    verdict = s["grade"] or f"SUPPRESSED (error rate {report['error_rate']}% > 10%)"
    print(f"  grade={verdict}  score={s['score']}  "
          f"failed={s['failed']}/{s['total']}  confirmed={confirmed}  "
          f"errors={s['errors']}", flush=True)
    print(f"  -> {path}", flush=True)
    return report


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--out", type=Path, default=REPO / "calibration" / "scans-v78")
    ap.add_argument("--only", nargs="+", default=None, help="target ids to scan")
    args = ap.parse_args()

    targets = yaml.safe_load(
        (REPO / "demo" / "targets.yaml").read_text(encoding="utf-8")
    )["targets"]
    if args.only:
        targets = [t for t in targets if t["id"] in args.only]
        if not targets:
            sys.exit(f"No target matched {args.only}")

    for spec in targets:
        await scan_one(spec, args.out)


if __name__ == "__main__":
    asyncio.run(main())
