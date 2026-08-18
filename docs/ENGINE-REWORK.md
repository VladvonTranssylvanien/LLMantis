# Engine rework — decided, implemented, measured

> Opened 18.08.2026 after the EU-only stack was withdrawn (PR #24), as a list of
> open questions. Gregor answered them the same day and the change is now
> implemented and measured. §5 records the answers; §7 records what the numbers
> did.

---

## 1. What is already decided

| | |
|---|---|
| The EU-only stack | **withdrawn.** No vendor is prohibited, for any layer (`PLAYBOOK.md` §1) |
| Data residency as a selling point | **dropped.** Pitch slide 6 rests on three mechanisms, not four |
| Mistral | **out.** Gregor, 18.08 |
| Judge | **gpt-4.1** on the existing Azure deployment |
| Target | **gpt-4.1-mini** on the same Azure resource |
| Grok | **deleted.** Unusable on its rate limits — confirmed, the deployment now returns `DeploymentNotFound` |
| The scan | **attacks a real deployment over HTTP.** It no longer replays a system prompt on our own provider |

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

## 5. The open questions, answered

1. **What replaces Mistral, and for which role?** Judge **gpt-4.1**, target
   **gpt-4.1-mini**, both on the existing Azure resource.
2. **One provider or many?** Both `mistral` and `azure` are registered.
   Mistral is kept for one reason only: the recorded baseline (mean 94.3 %,
   range 26–30 of 30) was measured on `mistral-small`, and deleting the
   provider would make that number unreproducible.
3. **Is determinism a goal?** No — Gregor: variance is acceptable and the
   calibration is sound. No `temperature` or `seed` was added, so `chat()`'s
   signature is unchanged. **It turned out not to matter** (§7).
4. **Does the target model become configurable?** Yes. `TARGET_MODEL`, and the
   hardcoded `"mistral-small"` at `scanner.py:63` is gone.
5. **What happens to the quota story?** It resolved itself: **0 errors in every
   scan run on the new engine.** The 429 coin-flip was a property of the free
   Mistral tier.

### The shape of the change

`mode="prompt"` used to mean *"replay this prompt on our own provider"* — the
scan measured a bot we were simulating. It now means what `mode="model"` means:
**POST the system prompt plus the attack to a real deployment and attack the
answer.** Azure Foundry holds no instructions of its own, so the prompt travels
with every request — which is also how a great many real chatbots work, because
the application owns the prompt.

- `"prompt"` is kept as an alias for `"model"`, so `frontend/` and
  `demo/targets.yaml` keep working **unchanged** — and the prompt stays exactly
  as editable as it was: a textarea and a YAML field.
- `mode="api"` is untouched. That is the path for a chatbot that already holds
  its own prompt, and it stays gated behind DNS ownership verification.
- `TARGET_URL`/`TARGET_KEY` are **config-only, never from a request body.** A
  caller-supplied url is what `mode="api"` is for. So the new mode adds no SSRF
  surface (`PLAYBOOK.md` §5).

---

## 6. Two defects this path had to carry itself

**The empty-answer guard.** `lab/runner.py` has guarded it since 16.08;
`scanner.py` never has (issue #7), because prompt mode went through `chat()`.
An empty answer contains no canary and no forbidden phrase, so the judge scores
it **PASS** — a model that never answered recorded as a model that resisted.
The new path raises instead, so it becomes an ERROR and counts toward
gradability rather than disappearing.

**`calibrate.py` died on the first unjudgeable item.** With the judge on Azure,
the provider's content filter rejects the judge *request* on some items — the
attack text and the bot's answer are the material the filter objects to. One
item used to kill the other 29 with a traceback. An unjudgeable item is now
reported as ERROR and excluded from the agreement count: it is neither
agreement nor disagreement, and counting it either way invents a verdict the
judge never gave.

Its provider guard also hardcoded `("mistral",)` and duly rejected
`PROVIDER=azure` the first time the judge moved. It now reads `_PROVIDERS`.

---

## 7. What the numbers did

**The judge stopped wobbling.** Same set, same command, same methodology as the
recorded baseline:

| Judge | Agreement | Unstable items |
|---|---|---|
| `mistral-small` (recorded, n=10) | mean 94.3 %, **range 26–30 of 30** | 5 |
| **`gpt-4.1` (n=10)** | **29/29 every run, 100 %** | **0** |

Open problem #1 — "the same set scores 26–30 of 30" — is closed by the engine
change rather than by a determinism parameter. All five previously unstable
items agree, including `cal-021` and `cal-023`, the two session 16 predicted by
name as the likeliest false positives.

⚠️ **29, not 30.** `cal-027` is unjudgeable on Azure, every run: it is the
`jb_encoding` item whose `bot_response` *is* an Azure content-filter error, so
the base64 payload trips the filter on the judge path exactly as it does at the
target. Coherent, but it means the figure covers 29 items and is not a
like-for-like replacement for "29/30".

**The demo beat, on a real deployment, 0 errors in every run:**

```
vulnerable   F(0) | D(34) | F(0)        4-8 findings
hardened     A(94) | A(100) | A(100)
middle case  D(42)
```

Three-way resolution — F/D/A across the three bots — which session 23 feared
the deduction model had lost to saturation. ⚠️ The vulnerable bot moves between
**F and D**, and one earlier run of the hardened bot scored **B(85)**. That is
the *target* answering differently, not the judge: it is the thing
`PITCH-PLAN.md` already says out loud ("the same bot can answer differently to
the same sentence twice"). Slide 5 should promise a contrast, not two specific
letters.

**`BLOCKED` finally matches real data.** Session 25 shipped the branch untested
— "no saved scan contains a content-filter error". `jb_encoding` is now BLOCKED
on all three bots: no credit, no penalty, excluded from gradability, listed in
the report. `scored` is 20 of 21, and `critical_coverage` is 100 %.

---

## 8. Not verified

- **One sample per bot** except the two above (n=3) and the hardened bot (n=4).
- **The 78-attack library was not run** on the new engine. Session 19 found 8 of
  78 attacks content-filtered on the Azure path; with the judge now on Azure
  too, judge-side filtering could be broader than the single item seen here.
  Untested.
- **No scan went through `POST /api/scan`.** `run_scan` was called directly, so
  org resolution, ownership checks and persistence are unexercised.
- **Nothing was re-measured through the frontend.** The `"prompt"` alias was
  verified in code (`target_mode='prompt'`, real HTTP, 0 errors), not in a browser.
- **`set-v2` was not re-run** against the new judge.
- Whether Azure's quota holds at `CONCURRENCY` above 3. Untested; 3 gave 0 errors.
