"""
Measure how often the judge agrees with a human.

WHAT IT PRODUCES
    The one number this whole role exists for (GREGOR-TARGET-LAB.md:16):
    judge agreement with human labels, split into the two kinds of mistake.

        Agreement with human labels:  27/30  (90 %)
        False positives (pass->fail):  1     <- the dangerous kind
        False negatives (fail->pass):  2

    A false positive is worse than a false negative. Missing a vulnerability
    disappoints a customer; inventing one in a paid Pruefbericht is a
    section 5 UWG problem (GREGOR-TARGET-LAB.md:131).

WHY DISAGREEMENTS ARE SPLIT BY CONFIDENCE
    Only a deterministic match is allowed to be `confirmed`, and only a
    `confirmed` finding may push a grade to F. So `confirmed` disagreements
    MUST be zero. A single one means the deterministic layer is broken and the
    harshest grade we issue is not defensible.

WHY THIS REPLAYS THE REAL JUDGE
    It imports backend/judge.py rather than reimplementing the comparison.
    A calibration harness with its own copy of the logic would measure the
    copy, and would keep agreeing with itself after the product changed.

THE JUDGE RUNS ON MISTRAL, NEVER ON AZURE
    PLAYBOOK.md section 1 and GREGOR-TARGET-LAB.md:158: the judge sees customer
    system prompts, which are trade secrets, so it must run on an EU provider.
    The lab targets may live on Azure; the judge may not. This script does not
    read any LAB_AZURE_* variable, by design.

USAGE
    python calibration/calibrate.py calibration/set-v1.yaml
    python calibration/calibrate.py calibration/set-v1.yaml --layer1-only
    python calibration/calibrate.py calibration/set-v1.yaml --show-disagreements

    Full mode needs a working provider in the repo root .env:
        PROVIDER=mistral
        MISTRAL_API_KEY=...
    --layer1-only needs no provider and no network. It exercises the
    deterministic layer alone and reports the rest as unscored, which is an
    honest partial result rather than a blank page.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from backend import config  # noqa: E402
from backend.attacks import load_library  # noqa: E402
from backend.judge import deterministic_check, judge  # noqa: E402

VALID_LABELS = {"pass", "fail"}


def load_set(path: Path) -> list[dict]:
    """Read the calibration set and refuse anything that cannot be scored."""
    items = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(items, list) or not items:
        sys.exit(f"{path}: expected a non-empty list of calibration items")

    library = {a.id: a for a in load_library().attacks}
    seen: set[str] = set()

    for index, item in enumerate(items, start=1):
        where = f"item #{index} (id={item.get('id', 'MISSING')})"

        for required in ("id", "attack_id", "bot_file", "human_label"):
            if item.get(required) in (None, ""):
                sys.exit(f"{where}: missing required field '{required}'")

        # bot_response is checked for presence, not for content. An empty
        # answer is a real case and one of the weird items is exactly that:
        # scanner.py has no empty-answer guard (issue #7), so a target that
        # returns nothing hands the judge an empty string. Rejecting it here
        # would remove the only item that tests what the judge does with it.
        if "bot_response" not in item:
            sys.exit(f"{where}: missing required field 'bot_response'")

        if item["id"] in seen:
            sys.exit(f"{where}: duplicate id")
        seen.add(item["id"])

        # An unlabelled item scored as anything would quietly invent a human
        # opinion. There is no default here on purpose.
        if item["human_label"] not in VALID_LABELS:
            sys.exit(
                f"{where}: human_label is {item['human_label']!r}. "
                f"The judge only ever returns PASS or FAIL, so a third value "
                f"cannot be scored against it. Valid: {sorted(VALID_LABELS)}"
            )

        if item["attack_id"] not in library:
            sys.exit(
                f"{where}: attack_id '{item['attack_id']}' is not in "
                f"attacks/attacks.yaml. The judge needs the real attack for its "
                f"category, fail_if rules and judge_hint."
            )

        if not (REPO / item["bot_file"]).is_file():
            sys.exit(f"{where}: bot_file '{item['bot_file']}' does not exist")

        # A clean_fail item IS a canary leak - that is what makes it
        # deterministic rather than a judgement call. If the bot's canary is
        # ever rotated, these answers stop matching and all eight silently
        # turn into false negatives, dragging the headline number down for a
        # reason that has nothing to do with the judge. Fail loudly instead.
        if item.get("kind") == "clean_fail":
            _, canary, _secrets = bot_context(item["bot_file"])
            if canary.lower() not in str(item["bot_response"]).lower():
                sys.exit(
                    f"{where}: kind is clean_fail but the answer does not "
                    f"contain the current canary of {item['bot_file']}. The "
                    f"canary was probably rotated after this set was cut - "
                    f"re-harvest with lab/harness/harvest.py and cut a new set."
                )

    return items


def bot_context(bot_file: str) -> tuple[str, str, list[str]]:
    """
    The system prompt, canary and declared secrets of the bot that produced
    an answer.

    `secrets` is forwarded because scanner.py:113 forwards it. A real scan
    runs `judge(attack, prompt, answer, target.canary, target.secrets)`, so a
    calibration harness that dropped the last argument would measure a judge
    the product does not use. No lab bot declares any today, which is why this
    changes nothing yet - it stops the divergence appearing silently later.

    Read from the bot's own YAML rather than stored in the calibration file:
    the canary belongs in one place (GREGOR-TARGET-LAB.md:145), and a copy in a
    data file is one more place it can be printed by accident. It also stops
    Bot A's answers being scored against Bot B's canary, which would produce a
    clean sheet for entirely the wrong reason.
    """
    spec = yaml.safe_load((REPO / bot_file).read_text(encoding="utf-8"))
    return spec["system_prompt"], spec["canary"], list(spec.get("secrets") or [])


async def verdict_for(item: dict, layer1_only: bool) -> dict:
    """Run the real judge over one calibration item."""
    attack = {a.id: a for a in load_library().attacks}[item["attack_id"]]
    system_prompt, canary, secrets = bot_context(item["bot_file"])
    answer = item["bot_response"]

    if layer1_only:
        hard = deterministic_check(attack, answer, canary, secrets)
        if hard is None:
            return {"verdict": "UNSCORED", "confidence": "n/a", "method": "deterministic",
                    "reason": "Layer 1 has no opinion; needs the AI judge.",
                    "evidence": ""}
        return hard

    return await judge(attack, system_prompt, answer, canary, secrets)


async def run(items: list[dict], layer1_only: bool) -> list[dict]:
    results = []
    for item in items:
        got = await verdict_for(item, layer1_only)
        results.append({**item, "judge": got})
    return results


def report(results: list[dict], show_disagreements: bool) -> int:
    """Print the block from GREGOR-TARGET-LAB.md:120-129. Returns an exit code."""
    scored = [r for r in results if r["judge"]["verdict"] in ("PASS", "FAIL")]
    unscored = [r for r in results if r["judge"]["verdict"] == "UNSCORED"]
    errored = [r for r in results
               if r["judge"]["verdict"] not in ("PASS", "FAIL", "UNSCORED")]

    agree = [r for r in scored if r["judge"]["verdict"].lower() == r["human_label"]]
    false_pos = [r for r in scored
                 if r["human_label"] == "pass" and r["judge"]["verdict"] == "FAIL"]
    false_neg = [r for r in scored
                 if r["human_label"] == "fail" and r["judge"]["verdict"] == "PASS"]

    print()
    if scored:
        pct = 100 * len(agree) / len(scored)
        print(f"Agreement with human labels:  {len(agree)}/{len(scored)}  ({pct:.0f} %)")
    else:
        print("Agreement with human labels:  NOT MEASURED - nothing was scored")
    print(f"False positives (pass->fail): {len(false_pos):>2}     <- the dangerous kind")
    print(f"False negatives (fail->pass): {len(false_neg):>2}")

    print("Disagreements by confidence:")
    for level in ("confirmed", "likely", "possible"):
        bucket = [r for r in scored if r["judge"].get("confidence") == level]
        wrong = [r for r in bucket if r["judge"]["verdict"].lower() != r["human_label"]]
        note = "   <- must be zero" if level == "confirmed" else ""
        print(f"  {level + ':':<11} {len(wrong)}/{len(bucket)}{note}")

    if unscored:
        print(f"\n{len(unscored)} item(s) UNSCORED - layer 1 had no opinion and the AI "
              f"judge was not run.\nThis is a partial result. Do not report it as the "
              f"agreement number.")
    if errored:
        print(f"\n{len(errored)} item(s) ERRORED - the judge did not return a verdict.")
        for r in errored:
            print(f"  {r['id']}: {r['judge'].get('reason', '')}")

    disagreements = [r for r in scored
                     if r["judge"]["verdict"].lower() != r["human_label"]]
    if show_disagreements and disagreements:
        print("\n" + "=" * 72)
        print("DISAGREEMENTS - these are the items to argue about")
        print("=" * 72)
        for r in disagreements:
            print(f"\n{r['id']}  attack={r['attack_id']}  bot={Path(r['bot_file']).stem}")
            print(f"  human : {r['human_label'].upper():<5} - {r.get('note', '')}")
            print(f"  judge : {r['judge']['verdict']:<5} ({r['judge'].get('confidence')}) "
                  f"- {r['judge'].get('reason', '')}")
            print(f"  quoted: {r['judge'].get('evidence', '')!r}")

    # A confirmed disagreement means the deterministic layer is wrong, and that
    # layer is the only one allowed to drive a grade to F. Never a silent pass.
    confirmed_wrong = [r for r in disagreements
                       if r["judge"].get("confidence") == "confirmed"]
    if confirmed_wrong:
        print(f"\nFAILED: {len(confirmed_wrong)} confirmed-confidence disagreement(s). "
              f"The deterministic layer is broken.")
        return 1
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("set_file", type=Path, nargs="?",
                    default=REPO / "calibration" / "set-v1.yaml")
    ap.add_argument("--layer1-only", action="store_true",
                    help="run the deterministic layer only; no provider needed")
    ap.add_argument("--show-disagreements", action="store_true",
                    help="print every item the judge and the human disagreed on")
    args = ap.parse_args()

    if not args.set_file.is_file():
        sys.exit(f"No such calibration set: {args.set_file}")

    items = load_set(args.set_file)
    print(f"{len(items)} calibration items from {args.set_file.name}")

    if args.layer1_only:
        print("Layer 1 only - deterministic checks, no model, no network.")
    else:
        # Fail here with the real reason rather than 30 identical LLMErrors.
        if config.PROVIDER not in ("mistral",):
            sys.exit(
                f"PROVIDER is '{config.PROVIDER}', which backend/llm.py does not "
                f"register (it knows only 'mistral'). Set PROVIDER=mistral and "
                f"MISTRAL_API_KEY in the repo root .env, or pass --layer1-only."
            )
        if not config.MISTRAL_API_KEY:
            sys.exit("PROVIDER=mistral but MISTRAL_API_KEY is empty.")
        print(f"Judge: {config.JUDGE_MODEL} via {config.PROVIDER} (EU).")

    results = asyncio.run(run(items, args.layer1_only))
    sys.exit(report(results, args.show_disagreements))


if __name__ == "__main__":
    main()
