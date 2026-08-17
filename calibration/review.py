"""
Walk a human through the calibration set one answer at a time.

WHY THIS EXISTS
    The deliverable is "how often does the judge agree with a HUMAN"
    (GREGOR-TARGET-LAB.md:16). If the labels were written by a model, the number
    is model-versus-model agreement wearing a human's name, and it does not
    survive the first question from a customer's lawyer.

    So the set ships with a `draft_label` the agent proposed and an empty
    `human_label`. Only what a person confirms here becomes `human_label`, and
    only `human_label` is ever scored by calibrate.py. An item nobody has looked
    at stays unscored rather than quietly defaulting to anything.

    `draft_label` is kept after review on purpose: the gap between it and
    `human_label` says how often the drafting agent was wrong, which is worth
    knowing before anyone trusts a model to pre-label anything.

WHY THE DRAFT IS SHOWN AFTER THE ANSWER, NOT BEFORE
    Reading "pass" first anchors the judgement. The answer comes first, the
    proposal second, and you can hide it entirely with --blind.

USAGE
    python calibration/review.py                       # resume where you left off
    python calibration/review.py --blind               # never show the draft
    python calibration/review.py --only borderline     # just the hard ten
    python calibration/review.py --relabel             # revisit confirmed items

    p / f    label PASS / FAIL          (a reason is asked for straight after)
    a        accept the draft label and its reason as written
    s        skip, decide later
    b        back one item
    q        save and quit
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SET = REPO / "calibration" / "set-v1.yaml"

FIELD_ORDER = ["id", "attack_id", "category", "bot_file", "model", "kind",
               "source", "criterion", "bot_response", "draft_label",
               "draft_note", "human_label", "note"]

# render() writes only the fields it knows, so anything absent from
# FIELD_ORDER is silently dropped the first time a set is saved. `criterion`
# was added to v2 to record which judge rule an item exercises, and vanished
# on the first keystroke of review until it was listed here. Any future field
# must be added above or it will not survive a review session.

BOLD, DIM, RED, GREEN, YELLOW, RESET = (
    "\033[1m", "\033[2m", "\033[31m", "\033[32m", "\033[33m", "\033[0m")


def load(path: Path) -> list[dict]:
    items = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(items, list) or not items:
        sys.exit(f"{path}: expected a non-empty list of calibration items")
    return items


def leading_comment(path: Path) -> str:
    """The comment block at the top of the file, so saving does not delete it.

    render() rebuilds the file from the parsed items, and YAML comments do not
    survive parsing. set-v2.yaml opens with the explanation of what it is and
    where its answers came from — provenance a reader needs when looking at the
    file alone. Without this it was erased by the first keystroke of a review
    session, silently, because the round-trip check only compares item fields.
    """
    kept: list[str] = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.startswith("#") or not line.strip():
            kept.append(line)
        else:
            break
    return "\n".join(kept).rstrip("\n")


def attack_messages() -> dict[str, str]:
    """
    id -> the text actually sent to the bot.

    Read from attacks/attacks.yaml rather than copied into the calibration
    file. Nobody can judge whether an answer failed without seeing what was
    asked, and a stale copy of the question would have people labelling
    against an attack that no longer exists.
    """
    raw = yaml.safe_load((REPO / "attacks" / "attacks.yaml").read_text(encoding="utf-8"))
    return {a["id"]: a["message"] for a in raw["attacks"]}


def render(items: list[dict]) -> str:
    """
    Write the set back in a fixed, readable shape.

    Hand-rolled rather than yaml.safe_dump because dump folds the bot answers
    into single quoted lines with \\n escapes. These answers are read by a human
    making a judgement call about them, and a wall of escapes is how a
    borderline item gets mislabelled.
    """
    out: list[str] = []
    for item in items:
        first = True
        for key in FIELD_ORDER:
            if key not in item:
                continue
            value = item[key]
            lead = "- " if first else "  "
            first = False
            if key in ("bot_response", "draft_note", "note") and value:
                # "|-" strips the trailing newline a plain "|" would add, so
                # the text read back is byte-identical to the text written.
                text = str(value).rstrip("\n")
                out.append(f"{lead}{key}: |-")
                out += [f"    {line}" if line else "" for line in text.split("\n")]
            elif value is None:
                out.append(f"{lead}{key}: null")
            else:
                # json.dumps, not yaml.safe_dump: safe_dump on a bare scalar
                # appends a "..." document-end marker, which turns the next
                # item into a second YAML document and breaks the file. A
                # JSON string is a valid YAML double-quoted scalar.
                out.append(f"{lead}{key}: {json.dumps(value, ensure_ascii=False)}")
        out.append("")
    return "\n".join(out)


def save(path: Path, items: list[dict], header: str = "") -> None:
    text = render(items)
    if header:
        text = header + "\n\n" + text
    # Never leave a half-written set behind: parse what we are about to write
    # before replacing a file that holds hand-made labels.
    #
    # The bot answers are compared field by field, not just counted. They are
    # evidence - a quotation the judge has to match character for character
    # (judge.py:117) - so a renderer that silently reflowed one would change
    # the result of the measurement.
    reparsed = yaml.safe_load(text)
    if not isinstance(reparsed, list) or len(reparsed) != len(items):
        sys.exit("Refusing to save: the rendered file does not round-trip.")
    for before, after in zip(items, reparsed):
        for key in ("id", "bot_response", "human_label", "note", "draft_label"):
            if before.get(key) != after.get(key):
                sys.exit(f"Refusing to save: {before.get('id')} field '{key}' "
                         f"does not survive the round-trip.")
    path.write_text(text, encoding="utf-8")


def show(item: dict, index: int, total: int, blind: bool, attacks: dict[str, str]) -> None:
    print("\n" + "=" * 78)
    print(f"{BOLD}{item['id']}{RESET}  ({index + 1}/{total})   "
          f"{DIM}{item.get('kind', '')} · {item.get('attack_id')} · "
          f"{Path(item.get('bot_file', '')).stem} · {item.get('model', '')}{RESET}")
    print("=" * 78)
    print(f"{DIM}ATTACK SENT:{RESET}")
    message = attacks.get(item["attack_id"], f"(unknown attack {item['attack_id']})")
    for line in message.split("\n"):
        print(f"  {line}")
    print(f"\n{DIM}THE BOT ANSWERED:{RESET}")
    for line in str(item["bot_response"]).rstrip().split("\n"):
        print(f"  {line}")
    if item.get("human_label"):
        colour = GREEN if item["human_label"] == "pass" else RED
        print(f"\n{colour}already labelled {item['human_label'].upper()}{RESET}: "
              f"{item.get('note', '')}")
    if not blind and item.get("draft_label"):
        colour = GREEN if item["draft_label"] == "pass" else RED
        print(f"\n{DIM}draft (agent, unconfirmed):{RESET} {colour}"
              f"{item['draft_label'].upper()}{RESET} - {item.get('draft_note', '')}")


def ask_reason(default: str) -> str:
    """A label with no reason is not a calibration item, it is a guess."""
    while True:
        prompt = f"  reason{' [enter = keep draft reason]' if default else ''}: "
        reason = input(prompt).strip()
        if reason:
            return reason
        if default:
            return default
        print(f"  {YELLOW}A reason is required - it is what makes the label "
              f"reviewable later.{RESET}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("set_file", type=Path, nargs="?", default=DEFAULT_SET)
    ap.add_argument("--blind", action="store_true", help="never show the draft label")
    ap.add_argument("--only", help="review one kind only "
                                   "(clean_pass, clean_fail, borderline, weird)")
    ap.add_argument("--relabel", action="store_true",
                    help="include items that already carry a human label")
    args = ap.parse_args()

    if not args.set_file.is_file():
        sys.exit(f"No such calibration set: {args.set_file}")

    items = load(args.set_file)
    header = leading_comment(args.set_file)
    attacks = attack_messages()
    queue = [i for i, it in enumerate(items)
             if (args.relabel or not it.get("human_label"))
             and (not args.only or it.get("kind") == args.only)]

    if not queue:
        done = sum(1 for it in items if it.get("human_label"))
        print(f"Nothing to review. {done}/{len(items)} items carry a human label.")
        return

    print(f"{len(queue)} item(s) to review.  p=pass  f=fail  a=accept draft  "
          f"s=skip  b=back  q=save and quit")

    pos = 0
    while 0 <= pos < len(queue):
        item = items[queue[pos]]
        show(item, pos, len(queue), args.blind, attacks)
        choice = input(f"\n{BOLD}label{RESET} [p/f/a/s/b/q]: ").strip().lower()

        if choice == "q":
            break
        if choice == "b":
            pos = max(0, pos - 1)
            continue
        if choice == "s":
            pos += 1
            continue
        if choice == "a":
            if not item.get("draft_label"):
                print(f"  {YELLOW}No draft to accept.{RESET}")
                continue
            item["human_label"] = item["draft_label"]
            item["note"] = item.get("draft_note", "")
        elif choice in ("p", "f"):
            item["human_label"] = "pass" if choice == "p" else "fail"
            item["note"] = ask_reason(item.get("draft_note", "")
                                      if item["human_label"] == item.get("draft_label")
                                      else "")
        else:
            print(f"  {YELLOW}Use p, f, a, s, b or q.{RESET}")
            continue

        # Saved every item, not at the end: a review interrupted by a closed
        # terminal must not lose forty minutes of human judgement.
        save(args.set_file, items, header)
        pos += 1

    save(args.set_file, items, header)
    done = sum(1 for it in items if it.get("human_label"))
    agreed = sum(1 for it in items
                 if it.get("human_label") and it["human_label"] == it.get("draft_label"))
    print(f"\nSaved. {done}/{len(items)} items carry a human label.")
    if done:
        print(f"The draft agreed with you on {agreed}/{done}.")
    if done < len(items):
        print("calibrate.py will refuse to run until every item is labelled.")


if __name__ == "__main__":
    main()
