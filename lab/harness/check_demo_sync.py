#!/usr/bin/env python3
"""Fail if demo/targets.yaml has drifted from lab/bots/*.yaml.

Why this exists
---------------
The same three bots live in two places, because they are reached two
different ways:

    demo/targets.yaml  -> frontend dropdown -> scanner mode="prompt"
    lab/bots/*.yaml    -> lab/runner.py     -> Azure, scanner mode="api"

That duplication already caused the defect this script prevents. The two
files drifted all the way apart - English versus German prompts, one canary
shared across both TeleShop bots, and no Art. 50 line in the demo copy - so
every number measured in the lab described bots the demo never showed.

Nothing in the code enforces the link, so it has to be checked. A mismatch
is a real defect, not a style nit: it silently decouples the pitch from the
evidence behind it.

Checks performed
----------------
1. Every mapped lab bot has a demo entry and vice versa.
2. system_prompt is byte-for-byte identical between the two.
3. canary is identical between the two.
4. Each canary appears in its own prompt - a canary that is not in the
   prompt cannot leak, so layer 1 would be silently dead.
5. Canaries are unique across bots, so a leak can be attributed to one bot
   (GREGOR-TARGET-LAB.md:144).

Usage:  python lab/harness/check_demo_sync.py
Exit:   0 all checks pass, 1 drift found.
"""

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]

# demo target id -> lab bot file
PAIRS = {
    "teleshop_vulnerable": "lab/bots/teleshop-a.yaml",
    "teleshop_hardened": "lab/bots/teleshop-b.yaml",
    "praxis_weber": "lab/bots/praxis-weber.yaml",
}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    problems: list[str] = []

    demo_path = REPO / "demo" / "targets.yaml"
    demo_targets = {t["id"]: t for t in load(demo_path).get("targets", [])}

    unmapped = sorted(set(demo_targets) - set(PAIRS))
    if unmapped:
        problems.append(
            f"demo/targets.yaml has entries with no lab bot: {', '.join(unmapped)}. "
            "Either add the lab bot or add it to PAIRS in this script."
        )

    canaries: dict[str, str] = {}

    for demo_id, lab_rel in PAIRS.items():
        lab_path = REPO / lab_rel
        if not lab_path.exists():
            problems.append(f"{lab_rel}: missing")
            continue
        if demo_id not in demo_targets:
            problems.append(f"demo/targets.yaml: no target with id '{demo_id}' (pairs with {lab_rel})")
            continue

        lab = load(lab_path)
        demo = demo_targets[demo_id]

        if lab.get("system_prompt") != demo.get("system_prompt"):
            problems.append(
                f"{demo_id}: system_prompt differs from {lab_rel}. "
                "The demo would scan a different bot than the lab measured."
            )

        lab_canary, demo_canary = lab.get("canary"), demo.get("canary")
        if lab_canary != demo_canary:
            problems.append(
                f"{demo_id}: canary differs - lab {lab_canary!r} vs demo {demo_canary!r}"
            )

        for label, canary, prompt in (
            (lab_rel, lab_canary, lab.get("system_prompt") or ""),
            (f"demo:{demo_id}", demo_canary, demo.get("system_prompt") or ""),
        ):
            if canary and canary not in prompt:
                problems.append(
                    f"{label}: canary {canary!r} is not in its own system_prompt. "
                    "It cannot leak, so layer-1 detection is silently dead."
                )

        if demo_canary:
            if demo_canary in canaries:
                problems.append(
                    f"{demo_id} and {canaries[demo_canary]} share the canary "
                    f"{demo_canary!r}. A leak could not be attributed to one bot."
                )
            else:
                canaries[demo_canary] = demo_id

    if problems:
        print("DRIFT between demo/targets.yaml and lab/bots/:\n")
        for p in problems:
            print(f"  - {p}")
        print(f"\n{len(problems)} problem(s).")
        return 1

    print(f"In sync: {len(PAIRS)} bots, prompts and canaries identical, all canaries distinct.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
