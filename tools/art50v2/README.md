# Art.-50 engine v2 — browser-driven

> **Prototype.** Not imported by `backend/`, not in `requirements.txt`, and
> excluded from the Docker image along with the rest of `tools/`. Nothing here
> can affect the demo path.

The question this answers: **can we take a customer's URL, open their site, find
their bot, and say whether it discloses being AI?**

Short answer: yes, and the engine does it. But the numbers below decide *which
product* it can be, and they are not the numbers we assumed.

---

## Setup

```bash
pip install playwright && python -m playwright install chromium
python tools/art50v2/test_fixtures.py            # 10 cases, all must pass
```

`livechat.json` is the live-chat slice (category 52, 378 technologies) of
[enthec/webappanalyzer](https://github.com/enthec/webappanalyzer), the
maintained continuation of Wappalyzer's fingerprint database. GPL-3.0, which is
compatible with this project's AGPL-3.0 — **Kwabena should confirm that before
it ships.** The file is optional: without it the engine still works on its own
two signals.

---

## Measured on 24 real German sites, 17.08

```
24  attempted
 0  disallowed us in robots.txt
 6  unreachable          403 / 429 / 401 — bot protection, not robots.txt
18  reachable
 3  chat widget found
 1  verdict provable     westwing.de — launcher reads "Westwing AI (BETA)"
```

Four things this changed:

**The passive GET was the wrong tool, and not mainly because of JavaScript.**
Six sites never served a usable page to a non-browser client at all: telekom.de
answered `202` with an empty body, dm.de an 11 KB app shell, obi.de `404` to our
own User-Agent and `200` to Chrome. We were not failing to find widgets — we did
not have the pages.

**Vendor-domain fingerprints are defeated by ordinary bundling.** Wappalyzer's
signatures are mostly third-party hosts. Sites now compile the widget into their
own build: `static.vattenfall.de/.../chatBot.js`,
`myposter.de/_nuxt/ZendeskMessengerLauncher.css`. No vendor domain appears. The
fifth signal in `engine.py` matches the **filename** instead, which nothing in
the fingerprint database does; it caught both cases, 2 of 2.

**`robots.txt` is not the obstacle we reported.** An earlier probe called nine
sites "robots.txt disallows" — that was `RobotFileParser.read()` treating a
`403` on `robots.txt` as *disallow everything*. Read with a browser UA, **zero
of 24** disallow us; three of the nine explicitly allow `LLMantis-Checker`. The
real obstacle is bot protection, and there is no honest way around it.

**Scroll and help pages did not help.** Both were added on the theory that
launchers lazy-load or live on `/hilfe`. Yield stayed at 3 of 18. Recorded as a
negative result so nobody tries it again.

---

## The eleven probes, and which ones earn their keep

Detection lives in `probes.py`. **Every probe runs on every check and none
short-circuits**, so a negative result arrives with the list of what was tried —
which is the only thing that makes "no widget found" defensible in a
Prüfbericht. It is also how each of the false positives below was found: by
reading the log, not by guessing.

| Probe | Confidence | What it proves |
|---|---|---|
| `websocket` | strong | A live chat connection was opened |
| `chat_endpoint` | strong | The page called a conversation endpoint |
| `vendor_asset` | strong | A **chat-only** vendor's name is in a loaded file |
| `generic_chat_asset` | strong | A loaded file is named `chat…` |
| `vendor_fingerprint` | strong | Wappalyzer signature matched a vendor domain |
| `vendor_platform` | medium | HubSpot/Salesforce/Zendesk **plus** chat wording |
| `vendor_global` | medium | A vendor script installed a global object |
| `fixed_launcher` | medium | A chat-like button is pinned to a corner |
| `iframe` | medium | A chat widget is embedded in an iframe |
| `aria` | medium | Accessibility metadata announces a chat surface |
| `page_text` | weak | The page's own copy mentions a chat assistant |
| `consent_gate` | context | A cookie banner is covering the page |

**Three false positives, all caught by the log and all fixed:**

- `/assistant/` in `chat_endpoint` matched `cdn.eye-able.com/…/assistant/js/…` on
  westwing.de — Eye-Able is **accessibility** software. Bare `assistant` and bare
  `bot` are out; `NOT_CHAT` now disqualifies a11y overlays, consent managers,
  newsletter pop-ups and back-to-top buttons outright.
- `frage` matched *Anfrage* inside tchibo.de's cookie banner, reporting a consent
  notice as a chat launcher and turning a correct `no_widget_found` into
  `not_determinable`. Every term in `CHATTY_TEXT` is anchored now.
- `hubspot` and `salesforce` fired on hellofresh.de and congstar.de, neither of
  which has a chat widget — both are also CRM and analytics tags. Multi-product
  platforms moved to `vendor_platform`, which requires chat wording in the same
  URL.

**A Python trap worth remembering:** `WALK_FIXED` is a JS literal in a Python
triple-quoted string. `\b` there is not a word boundary, it is **0x08**, so
`/\bchat/` reached the browser as `/<backspace>chat/` and matched nothing —
9 of 10 fixtures failed at once. Every JS literal in this package is now `r"""`.

### Two sweep modes, and why the flag exists

The twelve probes always run on every page visited. What used to stop early was
the *sweep*: desktop finding a widget meant mobile was never tried, and a hit on
the entry page meant the candidate pages were never visited. Vlad asked for
everything to be tried before a result is issued, and he was right — a
Prüfbericht's negative half is worth exactly as much as the list behind it.

`--exhaustive` never stops. Every candidate page, both form factors, probe
results merged by name across all of them.

| Site | Default | `--exhaustive` |
|---|---|---|
| westwing.de | 1 signal, 1 page, 25 s | **3 signals**, 18 pages, both viewports, 150 s |
| myposter.de | 3 signals, 1 page, 3 s | **4 signals**, 18 pages, 102 s |

**This corrects a claim made earlier in this file.** The Wappalyzer signatures
were described as firing once in the whole test and effectively dead. Under an
exhaustive sweep `vendor_fingerprint` fires on both sites above. They were not
dead — they needed pages the default sweep never reached. The ranking still holds
(our own signals fire first and more often), but "useless" was wrong.

Six times the wall clock. Reasonable for a paid report, expensive for a free
check — which is why it is a flag and not the default. The economics match the
layers: exhaustive for the customer who paid, fast for the funnel.

### Detection rate, 8 sites, after the fixes

```
6 of 8   a widget found            (was 3 of 18 with the vendor-domain approach alone)
2 of 8   nothing found             tchibo.de, hellofresh.de
0        false positives remaining on this set
```

`vendor_fingerprint` finally fired once, on flaschenpost.de. The borrowed
signatures are not useless — they are just last in line behind five signals of
our own.

---

## Stability: the same site, five runs each

Found by Vlad re-running the CLI and getting a different answer from the one in
this file. Measured properly afterwards:

| Site | Before | After | Detected by |
|---|---|---|---|
| westwing.de | `disclosed` 3/5, **`no_widget_found` 2/5** | `disclosed` 3/5, `not_determinable` 2/5 | DOM + generic chat asset |
| vattenfall.de | `not_determinable` 5/5 | `not_determinable` 5/5 | network (`asset:chatbot`) |
| myposter.de | — | `not_determinable` 5/5 | network (`asset:zendesk`) |
| tchibo.de | — | `no_widget_found` 5/5 | nothing to find |

The split named the cause. Sites detected by a **network** signal were stable
5 of 5: a request either happened or it did not. westwing.de was detected only
from the **DOM**, and that was a race.

Two things were wrong, both fixed:

- **The widget was never missing.** Six runs of six fired 13 chat-related
  requests, always including `ChatOverlayContent-…js` from a Shopify CDN. The
  named-vendor asset pattern did not match that filename, so the network signal
  never fired and everything rested on the DOM. `ASSET_GENERIC` now matches any
  asset whose filename begins "chat".
- **The label lives in a shadow root.** `Westwing AI (BETA)` was absent from
  `document.body.innerText` on 6 of 6 runs, because `innerText` does not cross a
  shadow boundary. Both the launcher query and the text-surface snapshot now walk
  shadow roots.

**What remains, and why it is acceptable:** westwing.de still reads `disclosed`
on some runs and `not_determinable` on others. Both are true statements — the
disclosure is real when we see it, and "we could not determine it" is honest when
we do not. What no longer happens is the wrong answer. Adding a fixed sleep
would trade honesty for the appearance of consistency, which is the trade this
product exists to refuse.

A `not_disclosed` verdict is never affected by this: it only comes from the
authorised path, where the widget was opened and the greeting actually read.

---

## Why the verdict has four values

This is the part that shapes the business, and it came out of the measurement
rather than a design meeting.

| Verdict | When | Layer that can produce it |
|---|---|---|
| `disclosed` | The launcher's own visible label says AI — westwing.de | Free |
| `not_determinable` | Widget found, launcher silent, we did not open it | Free |
| `no_widget_found` | Nothing found on the pages checked | Free |
| `not_disclosed` | Widget opened, greeting read, no disclosure in it | **Authorised only** |

vattenfall.de's launcher is the bare CSS class `chatBot__bubble`; myposter.de's
says `Hilfe`. Neither proves anything, because Art. 50(1) governs what a person
is told **when the conversation starts**, and that text is inside the widget.
Calling either non-compliant from the outside would be a claim with no evidence
in a paid report — the § 5 UWG problem `PLAYBOOK.md` forbids everywhere else.

So the free layer is **structurally incapable** of producing the finding that
sells. That is not a flaw in the funnel; it is the funnel. Free says *"you have
an assistant and we cannot confirm it identifies itself."* Paid says *"here is
your assistant's first message, dated, with no disclosure in it."*

`authorized=True` is the only path that clicks the launcher, and it requires
both the ownership checkbox **and** the DNS TXT verification in
`backend/ownership.py`. A checkbox alone proves nothing.

---

## Design decisions worth not re-litigating

- **Evidence is human-visible text only.** `launcher_label` holds `aria-label`,
  `title` and `innerText`; ids and classes go to `launcher_technical` and are
  used to *find* the widget, never to judge it. Quoting `chatBot__bubble` at a
  customer as their disclosure would be nonsense.
- **The greeting is a diff, not a grep.** Text surfaces are snapshotted before
  the click and after, and only new lines count as the bot's words — including
  inside iframes, or stray iframe text would be attributed to the assistant.
  Grepping the whole page is how the old checker passed a blog for mentioning AI.
- **Impersonation is a finding, not a pass.** A bot answering *"Ich bin Lisa vom
  Kundenservice"* is worse than one that says nothing. `IMPERSONATION` flags it
  and it can never produce `disclosed`.
- **German and English lexicons always both run.** A German site can carry an
  English bot; gating on a detected language is its own failure mode.
- **No evasion.** Real Chrome UA (an unusual one loses pages for no benefit),
  but `navigator.webdriver` is left visible, no stealth plugin, no proxy, and
  the `X-LLMantis-Checker` header points at `/scanner`. A site that blocks us is
  a finding, not an obstacle to route around.
- **We never accept a cookie banner.** It is a legal act, it changes what is
  being measured, and "widget gated behind consent" is a valid result.
- **`robots.txt` is recorded, never enforced** — team decision 17.08. RFC 9309
  is voluntary; the German case law that gives it force (§ 44b UrhG, OLG Hamburg
  5 U 104/24) concerns text-and-data mining under copyright, not whether a page
  may be loaded. `frontend/scanner.html` was rewritten to say what we actually
  do, because the old text promised otherwise.

---

## Open, before this replaces `backend/art50check.py`

| | |
|---|---|
| Packaging | Playwright + Chromium is ~300 MB plus system libraries. The app image is `python:3.13-slim`. Separate service, or a fatter image? |
| Async API | A check takes 15–40 s. `POST /api/art50check` is synchronous today; this needs a job id and polling |
| One browser per check | `check()` launches and closes Chromium each call. Fine for 24 sites, wasteful at scale |
| 15 of 18 sites showed no launcher | Behind login, behind consent, or on a page we did not reach. Unexplained |
| Fixture coverage | Five pages, no consent banner and no cross-origin iframe among them. Both are the realistic hard cases |
| Legal | Whether the Art. 50(1) duty falls on the deployer (our buyer) or the provider (their widget vendor) is unresolved and load-bearing for who we sell to — `PITCH-PLAN.md` T0-6, Kwabena |
