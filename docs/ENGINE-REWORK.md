# Engine rework — the decisions to take before writing code

> **Status: nothing is implemented.** This file exists so the design is argued
> on measured ground instead of in a commit message. Gregor's call on every
> open question below; this document records the constraints, not a preference.
>
> Opened 18.08.2026, after the EU-only stack was withdrawn (PR #24).

---

## 1. What is already decided

| | |
|---|---|
| The EU-only stack | **withdrawn.** No vendor is prohibited, for any layer (`PLAYBOOK.md` §1) |
| Data residency as a selling point | **dropped.** Pitch slide 6 rests on three mechanisms, not four |
| Mistral | **out.** Gregor, 18.08 |

What is *not* decided is everything about what replaces it. That is the point of
this file.

---

## 2. What the engine is today — verified, not remembered

The whole model surface is one function:

```python
# backend/llm.py:134
async def chat(system: str, user: str, model: str | None = None,
               max_tokens: int = 600) -> str
```

and one lookup table:

```python
# backend/llm.py:129
_PROVIDERS = {"mistral": _mistral_chat}
```

| Fact | Where |
|---|---|
| One provider is registered; `chat()` dispatches on `config.PROVIDER` | `llm.py:129,146` |
| `PROVIDER` is **global** — the same provider serves target *and* judge | `config.py:32`, used at `llm.py:146` |
| The judge's model is env-settable | `config.py:41` → `judge.py:221` |
| The **prompt-mode target's model is hardcoded** `mistral-small` | `scanner.py:63` |
| Token caps are hardcoded, not env-settable | `config.py:64` (target 600), `:65` (judge 400) |
| Concurrency is env-settable, default 3 | `config.py:61` |
| Retry/backoff on 429 and transient 5xx lives in the provider function | `llm.py:31-70` |

### 🔴 The engine has no determinism control surface at all

`chat()` takes `system`, `user`, `model`, `max_tokens`. **There is no
`temperature`, no `seed`, no `top_p` — not passed, not plumbed, not ignored.**
They are absent from the interface, so they cannot be set from anywhere.

This has been listed as "never checked" (problem #1 in `GREGOR_WORKLOG.md`,
owner Vlad) since session 26. It is worse than unchecked: there is nothing to
check. Any determinism work is an interface change to `chat()`, not a config
value.

---

## 3. What the evidence says is wrong with it

Every row is a measurement already in `GREGOR_WORKLOG.md`, not a suspicion.

| # | Problem | Measured | Session |
|---|---|---|---|
| 1 | **The judge is non-deterministic.** Same set, same judge, ten runs | v1 agreement ranged **26–30 of 30**, mean 94.3 % | 26, 27 |
| 2 | **Provider quota decides the grade.** Three runs of Bot B, minutes apart | *no grade* / **C** / **A** — every error a 429 | 22 |
| 3 | **A full-library scan does not fit the tier.** 78 attacks ≈ 121 requests against 50/min | `CONCURRENCY=3` is the measured ceiling and still produced 429s | 22 |
| 4 | **A second provider does not fix #3 by itself.** Grok on Azure | ~40 % of attacks errored at *any* concurrency; serialising made it worse (32 vs 31 errors) | 29 |
| 5 | **The target model cannot be varied without editing backend code** | `scanner.py:63`, no env var, unlike `JUDGE_MODEL`. The model-diversity table comes from a path the demo never uses | 20, handoff |
| 6 | **Six new judge criteria misfire on substantive refusals** | 3 observed false positives, one on the control bot, costing it two grades | 29 |

Two things that are **stable** and must survive any rework — they are the
product's defensibility, not implementation details:

- **Layer 1 agreed with a human on every item it can see, in every run:**
  11/11 on v1, 13/13 on v2, zero false positives (sessions 26, 29).
- **Only a `confirmed` finding may drive a grade to F** (`PLAYBOOK.md` §466,
  enforced in `judge.py`). No model opinion can produce the harshest grade.

---

## 4. 🔴 Do this before the engine changes, or the number is lost

The handoff's "FIRST THING" is now load-bearing for this work:
**`cae96e9 "finetuned judging"` is on `main` and no recorded figure was
measured against it.**

Swapping the engine changes judge behaviour. If the current judge is never
measured, then after the swap there is no way to attribute a change in
agreement to the engine rather than to `cae96e9`. Session 27 set the precedent
and it worked: an A/B with n=10 per side, in one sitting, attributed a 3.7-point
agreement drop to a judge edit rather than to model drift.

```bash
python calibration/calibrate.py --runs 10                     # v1, the headline row
python calibration/calibrate.py calibration/set-v2.yaml --runs 5
```

Cost: minutes. Without it, every claim about whether the new engine is better is
unfalsifiable.

⚠️ And note the ranges above: a single run cannot detect a change of one or two
items, because the same judge varies by four. Any before/after comparison needs
n≥10 per side or it measures noise.

---

## 5. Open questions — Gregor's call

Each one changes what gets built. None can be answered from the repository.

1. **What replaces Mistral, and for which role?** `PROVIDER` is global today, so
   "target" and "judge" cannot differ in prompt mode. If they should be able to,
   that is a change to `config.py` and `llm.py`, not a new key in `.env`.
2. **One provider or many?** A registry with several entries is a different
   design from a swap. #4 above is the argument for many (a single provider's
   quota decides our grades); Gate 1 is the argument for one until a second is
   actually needed.
3. **Is determinism a goal?** If yes, `chat()` grows a parameter and every
   recorded agreement range becomes obsolete — the numbers would need
   re-measuring against the new interface. If no, we keep quoting ranges and
   say so on stage, which has been the honest position so far.
4. **Does the target model become configurable?** `scanner.py:63` is the one
   line standing between the demo and the model-diversity table.
5. **What happens to the quota story?** #3 and #4 say this is a property of
   free tiers, not of Mistral. A paid plan, a different provider, or a smaller
   library are three different answers with three different costs.

---

## 6. What this PR contains

This document. No code. The branch exists so the discussion has somewhere to
land and so the engine change arrives as a reviewable diff rather than as a
direct push to `main` while Vlad is working in the repository
(`AGENTS.md` §4).
