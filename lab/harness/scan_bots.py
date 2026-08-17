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
import contextlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from backend.scanner import Target, run_scan  # noqa: E402

# Secrets are read from the bot YAML, never kept here. They used to be a
# hardcoded dict in this file, which meant calibration/calibrate.py - which
# reads the bot YAML - could not see them, and rejected a genuinely
# deterministic clean_fail item because the secret it leaked was invisible to
# everything except this script. One value, one home, same rule as the canary.
def bot_secrets(target_id: str) -> list[str]:
    path = REPO / LAB_BOT_FILE[target_id]
    spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(spec.get("secrets") or [])


LAB_BOT_FILE = {
    "teleshop_vulnerable": "lab/bots/teleshop-a.yaml",
    "teleshop_hardened": "lab/bots/teleshop-b.yaml",
    "praxis_weber": "lab/bots/praxis-weber.yaml",
}


@contextlib.contextmanager
def lab_runner(spec: dict, model: str, port: int):
    """Serve one bot on an Azure model and yield its /chat URL.

    This is what turns --model into a real black-box scan: the attacks go over
    HTTP to a bot we do not introspect, exactly as they would against a
    customer endpoint, instead of the prompt being replayed on mistral-small.
    """
    env = {**os.environ,
           "LAB_AZURE_MODEL": model,
           # Reasoning models spend the budget thinking before answering; 600
           # leaves some returning an empty string (lab/harness/matrix.py).
           "LAB_AZURE_MAX_TOKENS": "2500",
           # The scanner gives up at 30s; the runner must fail first. Raised
           # here because we are measuring the model, not enforcing the
           # product's timeout - a clipped call reads as a resisting bot.
           "LAB_AZURE_TIMEOUT_S": "25"}
    bot_yaml = REPO / LAB_BOT_FILE[spec["id"]]
    proc = subprocess.Popen(
        [sys.executable, str(REPO / "lab" / "runner.py"), str(bot_yaml),
         "--port", str(port)],
        cwd=REPO, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                httpx.get(f"http://127.0.0.1:{port}/health", timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError(f"runner did not come up for {spec['id']} on {model}")
        yield f"http://127.0.0.1:{port}/chat"
    finally:
        proc.terminate()
        proc.wait(timeout=10)


async def scan_one(spec: dict, out_dir: Path, model: str | None = None,
                   port: int = 8099) -> dict:
    if model:
        stack = lab_runner(spec, model, port)
    else:
        stack = contextlib.nullcontext(None)

    with stack as api_url:
        return await _scan(spec, out_dir, model, api_url)


async def _scan(spec: dict, out_dir: Path, model: str | None, api_url: str | None) -> dict:
    # system_prompt is set even in api mode, and deliberately. scanner.py:39
    # documents it as prompt-mode only, but _ask_target branches on mode alone,
    # so setting it costs nothing and keeps the AI judge from being handed an
    # empty <instructions> block - which silently degrades exactly
    # prompt_injection and data_leakage. Fine for lab bots we own; it would not
    # be fine for a real customer target, where we do not have their prompt.
    target = Target(
        mode="api" if api_url else "prompt",
        api_url=api_url or "",
        system_prompt=spec["system_prompt"],
        canary=spec["canary"],
        secrets=bot_secrets(spec["id"]),
    )
    started = time.time()

    async def progress(result, n, total):
        if n % 10 == 0 or n == total:
            print(f"    {n}/{total}  ({time.time() - started:.0f}s)", flush=True)

    where = f" via {model} (api mode)" if model else " (prompt mode, mistral-small)"
    print(f"\n=== {spec['id']} — {spec['name']}{where} ===", flush=True)
    # The full 78-attack corpus, named rather than inherited. The server's
    # default is now the 21-attack demo set (config.DEFAULT_ATTACK_LIBRARY),
    # and this script exists to measure the bots against the full one — the
    # reports in calibration/scans-v78/ are only comparable across runs if the
    # corpus is fixed, not read from an environment variable.
    report = await run_scan(target, on_result=progress,
                            library_name="attacks.yaml")

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{spec['id']}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # The grade lives in summary, NOT at the top level. Reading report["grade"]
    # returns None for every scan and reads as "no grade issued", which is a
    # different and much more alarming thing than the grade it actually got.
    s = report["summary"]
    confirmed = sum(1 for r in report["results"]
                    if r.get("verdict") == "FAIL" and r.get("confidence") == "confirmed")
    # Print the reason scoring.py actually gave. This used to hardcode
    # "error rate > 10%", which stopped being the rule when gradability became
    # absolute — it reported 41% error rate as the cause when the real one was
    # "only 6 of 15 critical attacks completed". A wrong reason on a withheld
    # grade sends you to fix the wrong thing.
    verdict = s["grade"] or "WITHHELD — " + "; ".join(s.get("incomplete_because") or ["reason not given"])
    print(f"  grade={verdict}  score={s['score']}  "
          f"failed={s['failed']}/{s['total']}  confirmed={confirmed}  "
          f"errors={s['errors']}", flush=True)
    print(f"  -> {path}", flush=True)
    return report


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--out", type=Path, default=REPO / "calibration" / "scans-v78")
    ap.add_argument("--only", nargs="+", default=None, help="target ids to scan")
    ap.add_argument("--model", default=None,
                    help="Azure deployment name. Serves each bot through "
                         "lab/runner.py and scans it in api mode over HTTP, "
                         "instead of replaying the prompt on mistral-small.")
    ap.add_argument("--port", type=int, default=8099)
    args = ap.parse_args()

    targets = yaml.safe_load(
        (REPO / "demo" / "targets.yaml").read_text(encoding="utf-8")
    )["targets"]
    if args.only:
        targets = [t for t in targets if t["id"] in args.only]
        if not targets:
            sys.exit(f"No target matched {args.only}")

    for spec in targets:
        await scan_one(spec, args.out, args.model, args.port)


if __name__ == "__main__":
    asyncio.run(main())
