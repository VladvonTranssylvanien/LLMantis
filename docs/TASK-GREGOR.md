# Start here — Gregor

> Target lab and judge calibration. This is the short version. Your full scope is
> [`GREGOR-TARGET-LAB.md`](GREGOR-TARGET-LAB.md).

## Read first — about 40 minutes, in this order

1. [`../PLAYBOOK.md`](../PLAYBOOK.md) — all of it.
2. [`GREGOR-TARGET-LAB.md`](GREGOR-TARGET-LAB.md) — your scope only.

## Your week, in order

| Day | Deliverable | Done means |
|---|---|---|
| 1 | **Bot A — "TeleShop Support"**, deliberately vulnerable, canary embedded | You broke it **by hand** at least once |
| 2 | **Bot B — the hardened twin** | You confirmed by hand that it resists what A fell for |
| 3 | **Calibration set — 30 answers labelled** PASS or FAIL by you | 30 items, each with your label and your reason |

If you cannot break Bot A by hand, the scanner will not break it either — and
the whole before/after demo rests on that pair.

## The calibration set is the most valuable thing you will make

It is what turns *"our judge is careful"* into a number we can defend in front
of a customer's lawyer. Right now that number does not exist: judge agreement
with human labels has **never been measured**.

Thirty real bot answers, each labelled PASS or FAIL by a human, then measure how
often the judge agrees. That percentage is the single most useful figure anyone
on this team can produce this week.

## The canary — use it everywhere

A unique string planted in each target's system prompt. When it comes back out
of the bot **verbatim**, that is not a model's opinion, it is a fact — a string
match, no model involved, cannot be wrong.

This matters beyond convenience: only a deterministic canary match
(`confidence: confirmed`) is allowed to drive a grade down to **F**. Everything
resting on the judge's opinion is capped below that. Your canaries are what make
the harshest grade defensible.

## Current state — both red

| Metric | Value |
|---|---|
| Test bots | 0 of 3 |
| Calibration set | 0 of 30 |
| Judge agreement with human labels | never measured |

## Hard rules

- Everything you build is a **lab target we own**. Never point any active test
  at a system we do not own — that is the line between a security product and an
  offence.
- Mark lab material clearly so it never gets mistaken for a customer scan.
- Never the word "certified" / `zertifiziert` anywhere, including bot names and
  test fixtures. § 5 UWG.
- No real customer data, ever, in a demo bot's prompt.
