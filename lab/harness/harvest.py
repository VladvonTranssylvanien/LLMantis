"""
Harvest real bot answers into a pool the calibration set is drawn from.

WHY THIS EXISTS
    The calibration set must be "30 real bot answers" (TASK-GREGOR.md:26) that a
    human labels before the judge sees them. Answers written by hand to look
    plausible would measure nothing: the whole deliverable is a number saying how
    often our judge disagrees with a human about what a real bot really said.

WHY IT USES attacks/attacks.yaml AND NOT THE MATRIX'S OWN ATTACK LIST
    lab/harness/matrix.py carries seven ad-hoc attacks for the model-diversity
    table. Those have no id in the shipped library, so a calibration item quoting
    one could never be replayed through backend/judge.py - the judge needs the
    real Attack object for its category, fail_if rules and judge_hint. Every item
    in the pool therefore carries a real library id.

WHY ONLY ATTACK MESSAGES ARE SENT, NEVER ORDINARY QUESTIONS
    The scanner only ever shows the judge an (attack, answer) pair, so a judge
    false positive can only happen on an answer to an attack. Ordinary-question
    behaviour is already covered by the control row in matrix.py.

CREDENTIALS
    None here. lab/runner.py reads lab/.env itself.

USAGE
    python lab/harness/harvest.py                       # both bots, 2 models
    python lab/harness/harvest.py --models gpt-4.1 Kimi-K2.5 --runs 2
    python lab/harness/harvest.py --out calibration/pool.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import yaml

LAB = Path(__file__).resolve().parent.parent
REPO = LAB.parent
PYTHON = REPO / "venv" / "bin" / "python"

DEFAULT_BOTS = [LAB / "bots" / "teleshop-a.yaml", LAB / "bots" / "teleshop-b.yaml"]
DEFAULT_MODELS = ["gpt-4.1-mini", "gpt-4.1"]

# Same reasoning as matrix.py: 600 leaves a reasoning model returning an empty
# string, which the runner correctly turns into an error. We want answers here,
# not a pool of error strings, so the budget is raised and the timeout with it.
MAX_TOKENS = "2500"
TIMEOUT_S = "180"


def load_attacks(path: Path) -> list[dict]:
    """Every attack in the shipped library, in file order."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data["attacks"]


def harvest_one(bot_path: Path, model: str, attacks: list[dict],
                port: int, runs: int) -> list[dict]:
    """Start the runner on one bot/model pair, send every attack, stop it."""
    # Resolved so a relative --bots argument still works: the row records the
    # path relative to the repo, and relative_to() needs both sides absolute.
    bot_path = bot_path.resolve()
    spec = yaml.safe_load(bot_path.read_text(encoding="utf-8"))
    env = {**os.environ,
           "LAB_AZURE_MODEL": model,
           "LAB_AZURE_MAX_TOKENS": MAX_TOKENS,
           "LAB_AZURE_TIMEOUT_S": TIMEOUT_S}
    proc = subprocess.Popen(
        [str(PYTHON), str(LAB / "runner.py"), str(bot_path), "--port", str(port)],
        cwd=REPO, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    rows: list[dict] = []
    try:
        for _ in range(60):
            try:
                httpx.get(f"http://127.0.0.1:{port}/health", timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError(f"runner did not come up for {bot_path.name}/{model}")

        for attack in attacks:
            for run in range(runs):
                row = {
                    "bot_file": str(bot_path.relative_to(REPO)),
                    "bot_name": spec["name"],
                    "model": model,
                    "run": run,
                    "attack_id": attack["id"],
                    "category": attack["category"],
                    "severity": attack.get("severity", ""),
                    "attack_message": attack["message"],
                }
                try:
                    r = httpx.post(f"http://127.0.0.1:{port}/chat",
                                   json={"message": attack["message"]}, timeout=200)
                    row["http_status"] = r.status_code
                    row["reply"] = r.json().get("reply", "")
                except Exception as e:
                    row["http_status"] = 0
                    row["reply"] = f"{type(e).__name__}: {e}"
                # The canary is deliberately NOT written into the pool row.
                # It is read from the bot YAML wherever it is needed
                # (GREGOR-TARGET-LAB.md:145); duplicating it into a data file
                # is one more place it can be printed by accident.
                rows.append(row)
                print(f"  {bot_path.stem:<12} {model:<14} {attack['id']:<24} "
                      f"{row['http_status']} {len(row['reply']):>5} chars", flush=True)
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--bots", nargs="+", type=Path, default=DEFAULT_BOTS)
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--port", type=int, default=8095)
    ap.add_argument("--attacks", type=Path, default=REPO / "attacks" / "attacks.yaml")
    ap.add_argument("--out", type=Path, default=REPO / "calibration" / "pool.jsonl")
    args = ap.parse_args()

    if not PYTHON.exists():
        sys.exit(f"No interpreter at {PYTHON} - create the venv first")
    attacks = load_attacks(args.attacks)
    print(f"{len(attacks)} attacks from {args.attacks.name}")

    rows: list[dict] = []
    for bot in args.bots:
        if not bot.is_file():
            sys.exit(f"No such bot config: {bot}")
        for model in args.models:
            rows += harvest_one(bot, model, attacks, args.port, args.runs)

    out = args.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    ok = sum(1 for r in rows if r["http_status"] == 200)
    print(f"\n{len(rows)} answers -> {os.path.relpath(out, REPO)}  "
          f"({ok} usable, {len(rows) - ok} error responses)")


if __name__ == "__main__":
    main()
