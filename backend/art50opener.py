"""
An LLM decides which button opens the chat, when the heuristic cannot.

WHY THIS EXISTS
    Chat widgets do not agree on how to be opened. o2online.de puts a pre-chat
    panel between the launcher and the conversation; some vendors need a
    "Nachricht schreiben", others a channel picker, others nothing at all. A
    keyword list catches the common phrasings and then quietly fails — and it
    fails in the worst possible way, by looking like success: no next-step button
    found reads as "we are at the first message" when it means "we did not
    recognise the button".

    Measured cost of that: o2online.de was reported `not_disclosed` on the
    strength of its pre-chat screen. Its bot does disclose, several clicks in.

WHAT THIS IS AND IS NOT ALLOWED TO DO
    It chooses WHICH ELEMENT TO CLICK. That is all.

    It never decides the verdict. The verdict comes from the same deterministic
    rule as before — a message box in the same surface as the text, and the text
    read from it — because a compliance finding that depends on what a model felt
    like is the thing this product sells against. The model can only change which
    screen we end up looking at, never what we conclude about it.

COST, AND WHY IT IS A FALLBACK
    Free tiers are rate-limited and the red-team scan already saturates one
    (technical debt #12). So this runs only when the deterministic opener failed
    to reach a message box, and never more than MAX_STEPS times. A site the
    keyword opener already handles costs nothing at all.

SHARED TRANSPORT, SEPARATE CONFIGURATION
    The HTTP call goes through llm.openai_compatible_chat, because that function
    carries the 429 backoff measured against real rate limits — a page-reading
    fallback with no retry would hand every throttled call straight to "no
    suggestion" and quietly stop helping. One wire format in this repository
    rather than two.

    But the URL and key are ART50_AI_*, never AZURE_* or TARGET_*. Those belong
    to the vulnerability scan and Gregor decides them
    (docs/ENGINE-REWORK.md). Reading them here would mean his next provider
    change silently retargets page-reading as well, and a re-pointed lab would
    break a customer-facing check. Shared transport is a saving; a shared key is
    a shared outage.

WHAT LEAVES THE MACHINE
    A list of button labels. Not the page, not its text, not the screenshot. Two
    reasons: it is a fraction of the tokens, and the free check runs on sites that
    have not asked us for anything, so the less of someone else's page we send
    anywhere the better.

    Note that it is still someone else's page content leaving the machine, and
    since PR #24 withdrew the EU-only stack there is no residency guarantee to
    fall back on. Whether the privacy notice needs a line is Kwabena's call, not
    a code decision.
"""
from __future__ import annotations

import json
import re

from . import config
from .llm import openai_compatible_chat

# Bounded hard. Each step is one model call plus one page interaction, and an
# unbounded agent loop on a stranger's website is not a thing we ship.
MAX_STEPS = 3
MAX_CANDIDATES = 30

SYSTEM = """You help a compliance checker reach the first message of a website's \
chat assistant, so it can be read and checked against Art. 50(1) of the EU AI Act.

You are given the clickable elements currently on screen, numbered. Choose the ONE \
that most likely moves toward an open conversation with a message box.

Rules:
- Prefer anything that starts, opens or continues a chat.
- A contact or service panel is often the ROUTE to the chat: labels like \
"Kontaktoptionen anzeigen", "Kontakt", "Hilfe & Service", "Contact options" are \
worth opening if no direct chat button is visible.
- NEVER choose cookie or consent buttons, login, search, newsletter, cart, or \
anything that navigates away from the page.
- NEVER choose anything that SUBMITS OR SENDS data — no "Absenden", "Abschicken", \
"Senden", "Bestellen", "Anmeldung absenden", no form submit of any kind. We read \
pages; we never post to them.
- If a conversation with a message input already appears to be open, answer done.
- If nothing on the list would help, answer none.

Reply with JSON only:
{"choice": <number>, "why": "<a few words>"}
or {"choice": "done", "why": "..."} or {"choice": "none", "why": "..."}"""

TEMPLATE = """Site: {url}
A chat widget was detected. We pressed: {pressed}
A message box has {box}been reached.

Clickable elements on screen now:
{candidates}

Which one moves us toward the assistant's first message?"""

# ---------------------------------------------------------------- navigation
#
# WHERE THE CHAT LIVES, not just how to open it.
#
# The clicking half of this file assumes the chat is reachable from the page we
# are already on. Often it is not: o2online.de keeps its assistant on a page of
# its own, /service/aura/, and no keyword list would ever guess "aura". The
# homepage carries a Sprinklr teaser bubble that goes nowhere useful, so the
# keyword opener pressed that, found no conversation, and reported the widget
# unreadable — while the real chat sat one navigation away behind a link.
#
# A model reading link texts and paths can make that jump. CANDIDATE_PATHS in the
# engine cannot: it guesses /hilfe, /kontakt, /service, and "aura" is a brand
# name that exists in no list anyone could write in advance.
SYSTEM_NAV = """You help a compliance checker find the page where a website's chat \
assistant lives, so its first message can be read and checked against Art. 50(1) \
of the EU AI Act.

You are given links from the site, numbered. Choose the ONE most likely to lead to \
a page with a live chat or AI assistant.

Rules:
- Prefer service, help, contact and support pages.
- A brand or product name can be the assistant itself — a link named after an \
assistant ("Aura", "Julia", "Ada") is a strong candidate.
- NEVER choose logout, cart, checkout, login, legal or careers pages.
- If none of these plausibly hosts a chat, answer none.

Reply with JSON only:
{"choice": <number>, "why": "<a few words>"}
or {"choice": "none", "why": "..."}"""

NAV_TEMPLATE = """Site: {origin}
Pages already checked with no chat found: {tried}

Links on the site:
{links}

Which one most likely hosts the chat assistant?"""

# Same-origin links only, deduplicated by path, with their visible text. Recursive
# through shadow roots for the same reason the button walk is.
LINKS_JS = r"""
() => {
  const seen = new Map();
  const roots = [];
  const collect = (root, depth) => {
    roots.push(root);
    if (depth > 4) return;
    for (const el of root.querySelectorAll('*'))
      if (el.shadowRoot) collect(el.shadowRoot, depth + 1);
  };
  collect(document, 0);
  // ONE LINE, and no /x flag. A JS regex literal cannot contain a newline and JS
  // has no extended flag — that is Python. Written across two lines with /ix this
  // was a syntax error in the injected script, so page.evaluate threw, the caller
  // caught it and returned None, and the page suggestion silently never happened:
  // o2online.de went straight to the guessed /hilfe, /kontakt, /service instead.
  const SKIP = /logout|abmelden|warenkorb|cart|checkout|kasse|login|anmelden|impressum|datenschutz|agb|karriere|jobs|presse|investor/i;
  for (const root of roots) {
    for (const a of root.querySelectorAll('a[href]')) {
      let u; try { u = new URL(a.href, location.href); } catch (e) { continue; }
      if (u.origin !== location.origin) continue;
      if (!u.pathname || u.pathname === '/') continue;
      const t = ((a.innerText || a.getAttribute('aria-label') || '') + '')
                .trim().replace(/\s+/g, ' ').slice(0, 60);
      if (!t) continue;
      const path = u.pathname + (u.search || '');
      if (SKIP.test(path) || SKIP.test(t)) continue;
      if (!seen.has(path)) seen.set(path, t);
    }
  }
  // RANKED, not truncated in DOM order.
  //
  // The cap used to be .slice(0, 60) straight off the document, and on a telco
  // homepage the first sixty links are tariffs and handsets. o2online.de carries
  // <a>Aura</a> -> /service/aura/?open_chat=true, the assistant's own page, far
  // enough down that it never made the list — so the model was asked to find a
  // chat among sixty phone contracts and correctly answered that it saw none.
  //
  // Score first, cut second. A link whose path or text mentions service, help,
  // contact, chat or an assistant is what we came for; everything else only fills
  // the room that is left.
  const HOT = /service|hilfe|help|kontakt|contact|support|chat|assistent|assistant|faq|fragen|beratung|betreuung|kundenservice/i;
  const scored = [...seen.entries()].map(([path, text]) => {
    let score = 0;
    if (HOT.test(path)) score += 2;
    if (HOT.test(text)) score += 2;
    // A short distinctive label on a shallow path is often a product or
    // assistant name — "Aura", "Julia". Worth surfacing over a deep tariff URL.
    if (text.length <= 12 && (path.match(/\//g) || []).length <= 3) score += 1;
    return {path, text, score};
  });
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, 45).map(({path, text}) => ({path, text}));
}
"""


async def suggest_page(page, tried: list[str], on_note=None) -> str | None:
    """
    Ask the model which page on this site is most likely to host the chat.

    Returns an absolute same-origin URL, or None. Same-origin is enforced here
    rather than trusted from the model: a suggestion is a hint, not an authority,
    and the SSRF guard in art50engine re-checks every request regardless.
    """
    try:
        links = await page.evaluate(LINKS_JS)
    except Exception as e:
        if on_note:
            await on_note(f"could not read the site's links ({type(e).__name__})")
        return None
    origin = page.url.split("/")[0] + "//" + page.url.split("/")[2]
    tried_paths = {t.replace(origin, "") or "/" for t in tried}
    links = [l for l in links if l["path"] not in tried_paths][:40]
    if not links:
        if on_note:
            await on_note("no same-origin links left to try")
        return None

    listing = "\n".join(f"{i}. {l['text']}  ->  {l['path']}" for i, l in enumerate(links))
    raw = await _ask(SYSTEM_NAV, NAV_TEMPLATE.format(
        origin=origin, tried=", ".join(sorted(tried_paths)) or "none", links=listing))
    if raw is None:
        if on_note:
            await on_note("the page-finding model could not be reached")
        return None
    d = _parse(raw)
    c = d["choice"]
    if not isinstance(c, int) or not 0 <= c < len(links):
        if on_note:
            await on_note(f"model suggested no page: {d['why']}")
        return None
    picked = links[c]
    if on_note:
        await on_note(f'model suggests {picked["path"]} ({picked["text"]}) — {d["why"]}')
    return origin + picked["path"]


# Read from every frame, because widgets live in frames and the button that
# advances the conversation is usually inside the widget rather than beside it.
CANDIDATES_JS = r"""
() => {
  const SKIP = /akzeptier|zustimmen|accept all|alle zulassen|cookie|einwillig|anmelden|^login|registrier|warenkorb|newsletter|suchen$|^suche|absenden|abschicken|senden$|submit|bestellen|kaufen|bezahlen|jetzt buchen|speichern|löschen|abonnieren|subscribe|teilnehmen|eintragen/i;
  const out = [];
  // RECURSIVE. One level was not enough: o2online.de is built from TEF-* web
  // components with 456 shadow roots, and the button that actually leads to its
  // chat — "Kontaktoptionen anzeigen" — sits two levels down. A single-level walk
  // never showed it to the model, which then correctly reported that it could see
  // nothing worth pressing.
  const roots = [];
  const collect = (root, depth) => {
    roots.push(root);
    if (depth > 4) return;
    for (const el of root.querySelectorAll('*'))
      if (el.shadowRoot) collect(el.shadowRoot, depth + 1);
  };
  collect(document, 0);
  for (const root of roots) {
    // NO submit inputs, and nothing that belongs to a form. This is a SAFETY
    // rule, not a relevance filter.
    //
    // On phishing.workshop.bogdanorel.de the model pressed "Anmeldung absenden"
    // — submit registration — because it read as a step forward. It is not ours
    // to press: on a real site that is a contact form sent, an order placed, a
    // signup made in someone's name, from a check they never asked for. We read
    // pages. We do not post to them.
    for (const el of root.querySelectorAll('button,a,[role=button],[tabindex="0"]')) {
      if ((el.type || '').toLowerCase() === 'submit') continue;
      if (el.form && (el.type || '').toLowerCase() !== 'button') continue;
      const r = el.getBoundingClientRect();
      if (r.width < 12 || r.height < 12) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) continue;
      let t = ((el.innerText || el.value || el.getAttribute('aria-label') ||
                el.getAttribute('title') || el.getAttribute('data-testid') ||
                el.getAttribute('name') || '') + '').trim().replace(/\s+/g, ' ');
      // An element with no name at all is not offered. Measured on o2online.de:
      // the list contained several "(a, no label)" entries, the model had
      // nothing to reason about, and it picked one three times in a row with
      // three different confident-sounding justifications. A coin flip dressed
      // as a decision is worse than no suggestion, because it consumes the step
      // budget and it reads like progress in the click path.
      if (!t) continue;
      if (t.length > 80) t = t.slice(0, 80);
      if (SKIP.test(t)) continue;
      out.push({t, x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)});
    }
  }
  return out.slice(0, 40);
}
"""


async def _ask(system: str, user: str) -> str | None:
    """
    One call to the configured deployment. None on any failure.

    Never raises. A page-reading model that is down must degrade the check to the
    keyword opener, not fail the whole request — a fallback that can take the
    endpoint with it is not a fallback.

    temperature is not passed and that is a known gap, not an oversight:
    openai_compatible_chat has no determinism parameter at all
    (docs/ENGINE-REWORK.md §2, open question 3). Which button gets pressed can
    therefore vary between runs on the same page. The verdict cannot — that stays
    on the deterministic rule — but a click path that changes is a report that is
    harder to reproduce, and it is worth fixing when that interface grows the
    parameter.
    """
    if not config.art50_ai_ready():
        return None
    try:
        choice = await openai_compatible_chat(
            url=config.ART50_AI_URL, key=config.ART50_AI_KEY,
            auth=config.ART50_AI_AUTH, model=config.ART50_AI_MODEL,
            system=system, user=user, max_tokens=150,
            timeout=config.ART50_AI_TIMEOUT_S, what="art50 opener",
        )
        return choice["message"].get("content") or None
    except Exception:
        return None


def _parse(raw: str) -> dict:
    """Pull the JSON out, however the model wrapped it."""
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return {"choice": "none", "why": "unparseable reply"}
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"choice": "none", "why": "invalid JSON"}
    choice = d.get("choice")
    if isinstance(choice, str) and choice.strip().isdigit():
        choice = int(choice)
    if choice not in ("done", "none") and not isinstance(choice, int):
        return {"choice": "none", "why": "no usable choice"}
    return {"choice": choice, "why": str(d.get("why", ""))[:80]}


async def _collect(page) -> list[dict]:
    """One flat, numbered list of what could be pressed, across all frames."""
    seen: set[str] = set()
    out: list[dict] = []
    for frame in page.frames:
        try:
            items = await frame.evaluate(CANDIDATES_JS)
        except Exception:
            continue
        for it in items:
            key = it["t"]
            if key in seen:
                continue
            seen.add(key)
            it["frame"] = frame
            out.append(it)
            if len(out) >= MAX_CANDIDATES:
                return out
    return out


async def open_with_ai(page, url: str, pressed: list[str], has_box: bool,
                       on_note=None) -> list[str]:
    """
    Try to reach an open conversation. Returns the labels pressed, in order.

    on_note  optional async callback(str) so the streaming UI can show the model's
             reasoning as it happens — the caller watching us decide is part of
             what makes a non-deterministic step explainable afterwards.
    """
    path: list[str] = []

    for _ in range(MAX_STEPS):
        cands = await _collect(page)
        if not cands:
            break

        listing = "\n".join(f"{i}. {c['t']}" for i, c in enumerate(cands))
        user = TEMPLATE.format(
            url=url, pressed=", ".join(pressed + path) or "nothing yet",
            box="" if has_box else "NOT ", candidates=listing)
        raw = await _ask(SYSTEM, user)
        if raw is None:
            if on_note:
                await on_note("the page-reading model could not be reached")
            break

        d = _parse(raw)
        choice, why = d["choice"], d["why"]

        if choice == "done":
            if on_note:
                await on_note(f"model says the conversation is open: {why}")
            break
        if choice == "none" or not isinstance(choice, int) or not 0 <= choice < len(cands):
            if on_note:
                await on_note(f"model found nothing to press: {why}")
            break

        picked = cands[choice]
        label = picked["t"]
        # Compared against the UNPREFIXED labels. path stores "ai: <label>", so
        # the old `label in path` test never matched and the same button was
        # pressed until the step budget ran out.
        already = set(pressed) | {x.removeprefix("ai: ") for x in path}
        if label in already:
            # It suggested something already pressed, so the last press changed
            # nothing visible. Stop rather than knock on the same door twice.
            if on_note:
                await on_note("model repeated a button already pressed; stopping")
            break

        if on_note:
            await on_note(f'pressing "{label}" — {why}')
        try:
            await picked["frame"].evaluate(
                """([x, y]) => {
                     const el = document.elementFromPoint(x, y);
                     if (el) el.click();
                   }""", [picked["x"], picked["y"]])
        except Exception:
            break
        path.append(f"ai: {label}")
        await page.wait_for_timeout(3500)

    return path
