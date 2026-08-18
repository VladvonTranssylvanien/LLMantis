"""
The Art.-50 disclosure check the website runs. Browser-driven, twelve probes,
none of which short-circuits.

REPLACES art50check.py, WHICH COULD NOT DO THE JOB
    Measured on 24 real German sites, the passive-GET version failed for reasons
    that had little to do with JavaScript:

      * 6 of 24 never served a usable page to a non-browser client — a 202 with
        an empty body (telekom.de), an 11 KB app shell (dm.de), a 404 to our own
        User-Agent where Chrome got 200 (obi.de).
      * Its 9 hand-written vendor signatures, and the 378 borrowed Wappalyzer
        ones, matched NOTHING. Sites bundle the widget into their own build:
        static.vattenfall.de/…/chatBot.js, a bundled ZendeskMessengerLauncher.css
        on myposter.de, a Shopify-hosted ChatOverlayContent.js on westwing.de.
      * It grepped the whole page, so "assistant" in a job ad passed and otto.de
        matched "chatbot" inside a JSON feature-flag blob.
      * Its keywords were English only, on the German market.

EVERY PROBE, EVERY PAGE, ON THE FREE CHECK
    All twelve run on every page visited, and the free check sweeps
    exhaustively — every candidate page, both form factors — because the value of
    "no widget found" is entirely in the list of things that were tried. That
    takes 30–150 s, which is why this streams progress instead of blocking: the
    caller watches us try everything, and the watching IS the Nachweis.

WE OPEN THE WIDGET. WE NEVER TYPE INTO IT.
    Art. 50(1) is about what a person is told when the conversation starts, and
    that text lives inside the widget rather than on the button. So we click the
    button — one mouse click, what any visitor does — read what the assistant says
    on its own, and leave.

    Clicking is not messaging. Nothing is submitted, no conversation is authored
    by us, and the greeting is written to be read by anyone who opens the chat. An
    earlier version treated the click as messaging and gated it behind ownership;
    that cost the free check the only verdict worth having, since of three widgets
    found across 24 sites exactly one disclosed on the button itself.

    _read_greeting is the only place a click happens, and it contains no code path
    that can enter text. "We never send your bot a message" is a property of the
    implementation, not a sentence in a paragraph.

    Still gated behind DNS TXT ownership: the red-team scan, which drives real
    attacks. That is a different thing from reading a greeting.

SECURITY: THIS IS A PUBLIC, UNAUTHENTICATED ENDPOINT DRIVING A REAL BROWSER
    Far more exposed than the GET it replaces. Three guards, all load-bearing:

      1. netguard.assert_public_host on the target before anything launches.
      2. A request interceptor that ABORTS any navigation or subresource whose
         host resolves private. netguard alone cannot cover this: it resolves the
         name once and the browser resolves it again, so a DNS-rebinding name
         with TTL 0 would slip past (PROJECT-STATE technical debt #14). The
         interceptor re-checks every request the page actually makes.
      3. No file:// or data: navigation, and every redirect hop re-checked by the
         same interceptor.

    Screenshots are returned as bytes and never written to disk: this endpoint is
    anonymous, so persisting images of arbitrary third-party sites would create a
    retention question nobody has answered.
"""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from . import art50probes as probes
from .art50probes import ProbeResult
from .netguard import UnsafeUrlError, assert_public_host, is_private_url

HERE = Path(__file__).parent

# A real browser UA. obi.de answers 404 to "LLMantis-Checker" and 200 to Chrome,
# so an honest-but-unusual UA loses pages for nothing. Identity is carried by the
# header instead, pointing at /static/scanner.html, and navigator.webdriver is
# deliberately left visible: no stealth plugin, no proxy, no fingerprint
# spoofing. A site that blocks us is a finding, not an obstacle to route around.
UA_DESKTOP = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")
UA_MOBILE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 "
             "Safari/604.1")
HEADERS = {"X-LLMantis-Checker": "1.0 (+https://llmantis.de/static/scanner.html)"}

VIEWPORTS = [
    ("desktop", UA_DESKTOP, {"width": 1280, "height": 900}, False),
    ("mobile", UA_MOBILE, {"width": 390, "height": 844}, True),
]

# German first, because the market is German. Both lexicons always run: a German
# site can carry an English bot, and gating on a detected language is its own
# failure mode.
DISCLOSE = [
    r"\bKI\b", r"künstliche intelligenz", r"KI-Assistent", r"KI-gestützt",
    r"KI-Chat", r"KI-Bot", r"KI-basiert", r"virtueller assistent",
    r"digitaler assistent", r"automatisierter assistent", r"automatisiert",
    r"\bchatbot\b", r"\bbot\b", r"kein mensch", r"nicht menschlich", r"maschine",
    r"\bAI\b", r"artificial intelligence", r"AI assistant", r"AI-powered",
    r"powered by AI", r"automated assistant", r"automated", r"virtual assistant",
    r"not a human", r"\bchat ?bot\b",
]

# The opposite of disclosure. A bot introducing itself as a named colleague is
# worse than one that says nothing, and it is the finding worth selling.
IMPERSONATION = [
    r"ich bin (eine|ein)? ?[A-ZÄÖÜ][a-zäöüß]+ (von|vom|bei) ",
    r"\bmein name ist\b", r"\bberater(in)?\b", r"\bmitarbeiter(in)?\b",
    r"\bkollege\b", r"\bmein team\b", r"persönlich für sie",
    r"\bmy name is\b", r"\bi'?m [A-Z][a-z]+ from\b", r"\bhuman agent\b",
]

# Tried after the entry page, and only after the site's own navigation. Guessed
# paths 404'd on two of two first attempts, which is why discovery comes first
# and these are the fallback.
CANDIDATE_PATHS = ["/hilfe", "/kontakt", "/service", "/support", "/faq",
                   "/kundenservice", "/help", "/contact"]

VERDICTS = ("disclosed", "not_disclosed", "not_determinable", "no_widget_found")

MAX_PAGES_PER_VIEWPORT = 9


@dataclass
class Art50Report:
    url: str
    verdict: str = "not_determinable"
    reason: str = ""
    evidence: str = ""
    launcher_label: str = ""            # human-visible text, safe to quote
    launcher_technical: str = ""        # ids/classes: detection only, never evidence
    first_message: str = ""
    impersonation: str = ""
    robots: str = ""
    authorized: bool = False
    opened_widget: bool = False
    viewport: str = ""
    duration_s: float = 0.0
    screenshot_b64: str = ""            # returned, never written to disk
    # Taken WHILE the chat is open, which is the whole point: the picture has to
    # show the sentence the verdict quotes. The page-level shot above is taken at
    # the end, by which time a panel may have closed or a later page loaded.
    widget_shot_b64: str = ""
    greeting_source: str = ""           # "iframe" or "panel" — where the text came from
    pages_tried: list[dict] = field(default_factory=list)
    probe_log: list[dict] = field(default_factory=list)
    blocked_requests: int = 0           # private-host requests the guard aborted

    def as_dict(self) -> dict:
        assert self.verdict in VERDICTS, self.verdict
        d = dict(self.__dict__)
        d["probes_fired"] = [p["name"] for p in self.probe_log if p["fired"]]
        d["probes_attempted"] = len(self.probe_log)
        return d


def _load_signatures() -> dict:
    p = HERE.parent / "tools" / "art50v2" / "livechat.json"
    if not p.exists():
        p = HERE / "livechat.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


SIGS = _load_signatures()


def robots_state(url: str) -> str:
    """
    "allows" / "DISALLOWS" / "unreadable". Recorded, never a gate.

    Team decision 17.08: RFC 9309 is a voluntary IETF standard, not law, and the
    German case law that gives it force (§ 44b UrhG, OLG Hamburg 5 U 104/24) is
    about text-and-data mining under copyright, not whether a page may be loaded.
    Measured: 0 of 24 German sites disallowed us.

    Fetched with the browser UA, and an unreadable file fails OPEN. A previous
    version used RobotFileParser.read(), which treats a 403 on robots.txt as
    "disallow everything" — that turned bot protection into nine phantom refusals.
    """
    p = urlparse(url)
    try:
        body = urlopen(
            Request(f"{p.scheme}://{p.netloc}/robots.txt",
                    headers={"User-Agent": UA_DESKTOP}), timeout=8,
        ).read().decode("utf-8", "replace")
    except Exception:
        return "unreadable"
    rp = RobotFileParser()
    rp.parse(body.splitlines())
    return "allows" if rp.can_fetch("LLMantis-Checker", url) else "DISALLOWS"


def first_match(patterns: list[str], text: str, context: int = 0) -> str:
    """
    The first matching phrase, widened to the words around it when asked.

    context matters for the evidence field, which is what a report quotes. The
    bare match on westwing.de is "AI" — two letters prove nothing to a reader.
    Widened it is "Westwing AI (BETA)", checkable against the screenshot.
    """
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if not m:
            continue
        if not context:
            return m.group(0).strip()
        start, end = max(0, m.start() - context), min(len(text), m.end() + context)
        snippet = text[start:end].strip()
        if start:
            snippet = snippet.partition(" ")[2] or snippet
        if end < len(text):
            snippet = snippet.rpartition(" ")[0] or snippet
        return snippet.strip(" |—") or m.group(0).strip()
    return ""


# innerText crosses neither an iframe nor a shadow boundary, and
# "Westwing AI (BETA)" was absent from document.body.innerText on 6 of 6 runs for
# exactly that reason. Snapshotted before the click and after, so only what the
# click PRODUCED counts as the greeting.
_TEXT_SURFACES = r"""
() => {
  const chunks = [];
  const grab = r => { try { chunks.push((r.body ? r.body.innerText : r.innerText) || ''); }
                      catch (e) {} };
  grab(document);
  for (const el of document.querySelectorAll('*'))
    if (el.shadowRoot) { try { chunks.push(el.shadowRoot.textContent || ''); } catch (e) {} }
  for (const f of document.querySelectorAll('iframe'))
    { try { if (f.contentDocument) grab(f.contentDocument); } catch (e) {} }
  return chunks.join('\n');
}
"""

_HELP_LINKS = r"""
() => {
  const exact = /^(hilfe|kontakt|service|support|kundenservice|faq|contact|help)$/i;
  const loose = /hilfe|kontakt|service|support|faq/i;
  const seen = new Set(), out = [];
  for (const a of document.querySelectorAll('a[href]')) {
    const t = (a.innerText || '').trim();
    if (!t || t.length > 30) continue;
    if (!exact.test(t) && !loose.test(t)) continue;
    if (seen.has(a.href)) continue;
    seen.add(a.href);
    out.push({href: a.href, text: t, exact: exact.test(t)});
  }
  out.sort((x, y) => (y.exact ? 1 : 0) - (x.exact ? 1 : 0));
  return out.slice(0, 4);
}
"""


def _new_text(before: str, after: str) -> str:
    seen = {l.strip() for l in before.splitlines() if l.strip()}
    return "\n".join(l.strip() for l in after.splitlines()
                     if l.strip() and l.strip() not in seen)[:4000]


def _merge(a: list[ProbeResult], b: list[ProbeResult]) -> list[ProbeResult]:
    """
    Union of two probe runs, by name. A probe that fired anywhere counts as
    fired, and findings accumulate — the report has to say "this fired
    somewhere", not "this fired on whichever page happened to be last".
    """
    if not a:
        return b
    by_name = {p.name: p for p in a}
    for p in b:
        prev = by_name.get(p.name)
        if prev is None:
            by_name[p.name] = p
            continue
        if p.fired and not prev.fired:
            prev.fired, prev.note = True, p.note
        for f in p.findings:
            if f not in prev.findings:
                prev.findings.append(f)
        prev.findings = prev.findings[:8]
        if not prev.fired and p.note and not prev.note:
            prev.note = p.note
    return list(by_name.values())


# What opened, and its text — NOT a diff of the whole page.
#
# WHY THIS IS NOT A WHOLE-PAGE DIFF ANY MORE
#     It was, and on myposter.de that produced a `not_disclosed` verdict quoting
#     the site's own cookie banner and five Trustpilot reviews as "what your
#     assistant said first". The bot may have said nothing at all; those elements
#     merely appeared inside the 4.5 s window after the click. Telling a customer
#     they breach Art. 50 on the evidence of their own cookie notice is the § 5 UWG
#     problem this project refuses everywhere else, and it is the worst failure
#     mode available to us.
#
#     So: find the panel the click OPENED — a new iframe, or a fixed element that
#     was absent or tiny before and is now panel-sized — and read only inside it.
#     Anything matching NOT_CHAT (consent walls, newsletter pop-ups, review
#     widgets) is disqualified outright. If no panel can be identified, we return
#     nothing and the caller must not claim a missing disclosure.
_WIDGET_PANEL = r"""
(before) => {
  const NOT_CHAT = /eye-?able|accessibility|barrierefrei|usercentrics|cookiebot|onetrust|sourcepoint|borlabs|klaro|consent|cookie|datenschutz|privatsph|einwillig|newsletter|rabatt|gutschein|trustbadge|trustedshops|trustpilot|bewertung|review|spare \d/i;
  const key = el => (el.tagName + '|' + (el.id || '') + '|' +
                     ((el.className || '') + '').toString().slice(0, 60));
  const seen = new Set(before);
  const cands = [];

  // A chat panel that arrived as an iframe. Vendors overwhelmingly do this, and
  // frameLocator-style access works because we drive the browser ourselves.
  for (const f of document.querySelectorAll('iframe')) {
    const r = f.getBoundingClientRect();
    if (r.width < 180 || r.height < 120) continue;
    const id = key(f);
    const blob = [f.getAttribute('title'), f.getAttribute('name'), f.id,
                  (f.className || '') + '', f.getAttribute('src')].filter(Boolean).join(' ');
    if (NOT_CHAT.test(blob)) continue;
    let text = '';
    try { if (f.contentDocument && f.contentDocument.body)
            text = f.contentDocument.body.innerText || ''; } catch (e) { text = ''; }
    cands.push({how: 'iframe', fresh: !seen.has(id), area: r.width * r.height,
                label: blob.slice(0, 200), text: text.slice(0, 4000)});
  }

  // Or a panel rendered in the page: fixed, large enough to be a conversation,
  // and either new since the click or newly grown.
  const walk = root => {
    let out = [...root.querySelectorAll('div,section,aside,dialog')];
    for (const el of root.querySelectorAll('*'))
      if (el.shadowRoot) out = out.concat(walk(el.shadowRoot));
    return out;
  };
  for (const el of walk(document)) {
    const cs = getComputedStyle(el);
    if (cs.position !== 'fixed' && cs.position !== 'absolute') continue;
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) continue;
    const r = el.getBoundingClientRect();
    // Height was 200 and that was wrong twice over: it rejected a panel showing a
    // one-line greeting, and it was using size to answer a question size cannot
    // answer. What actually separates a chat panel from a cookie banner is the
    // text box you reply in — a consent wall has buttons, a chat has an input.
    if (r.width < 160 || r.height < 60 || r.width > 700) continue;
    const text = (el.innerText || '').trim();
    if (text.length < 8) continue;
    const blob = key(el) + ' ' + text.slice(0, 300);
    if (NOT_CHAT.test(blob)) continue;
    const hasInput = !!el.querySelector('input[type=text],input:not([type]),textarea,[contenteditable=true]');
    cands.push({how: hasInput ? 'panel with a message box' : 'panel',
                fresh: !seen.has(key(el)), hasInput, area: r.width * r.height,
                label: key(el).slice(0, 200), text: text.slice(0, 4000)});
  }

  // Ranking, strongest signal first: something you can type into is a chat, then
  // something that appeared because of the click, then the smaller box — a chat
  // panel is a panel and a page-sized element is the page.
  cands.sort((a, b) => (b.hasInput ? 1 : 0) - (a.hasInput ? 1 : 0)
                    || (b.fresh ? 1 : 0) - (a.fresh ? 1 : 0)
                    || a.area - b.area);
  return cands.find(c => c.text) || null;
}
"""

_BEFORE_KEYS = r"""
() => {
  const key = el => (el.tagName + '|' + (el.id || '') + '|' +
                     ((el.className || '') + '').toString().slice(0, 60));
  const out = [];
  const walk = root => {
    for (const el of root.querySelectorAll('iframe,div,section,aside,dialog')) {
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      if (r.width >= 180 && r.height >= 180 &&
          (el.tagName === 'IFRAME' || cs.position === 'fixed' || cs.position === 'absolute'))
        out.push(key(el));
      if (el.shadowRoot) walk(el.shadowRoot);
    }
  };
  walk(document);
  return out;
}
"""


# Cross-origin frames, read through Playwright rather than through the page.
#
# WHY THIS EXISTS
#     The in-page detector reaches iframes with `f.contentDocument`, which the
#     same-origin policy sets to null for every third-party widget — and third
#     parties are exactly who hosts chat widgets. Measured on 10 German sites: we
#     opened a chat on 3 of 9 and could attribute words on 1, because the rest sat
#     in frames the page itself is not allowed to read.
#
#     Playwright drives the browser over CDP, so `page.frames` includes every
#     frame regardless of origin and `frame.evaluate` runs inside it. This is not
#     a bypass of anything: it is the same access the browser's own devtools have,
#     on a page a visitor is looking at.
#
# WHAT COUNTS AS A CHAT FRAME
#     A message box you could reply in is the strongest signal — a consent frame
#     has buttons, a chat has an input. Then chat wording in the frame's URL or
#     name. Anything matching NOT_CHAT is disqualified: consent managers and
#     review widgets are iframes too.
_FRAME_PROBE = r"""
() => {
  const body = document.body;
  return {
    text: body ? (body.innerText || '').slice(0, 4000) : '',
    hasInput: !!document.querySelector(
      'input[type=text],input:not([type]),textarea,[contenteditable=true]'),
    title: document.title || '',
  };
}
"""


async def _chat_frames(page, before_urls: set[str]) -> list[dict]:
    """Every frame that plausibly contains a conversation, best first."""
    out: list[dict] = []
    for frame in page.frames:
        if frame is page.main_frame:
            continue
        url = frame.url or ""
        # about:blank is NOT a reason to skip a frame, and rejecting it was the
        # single bug that made every Zendesk widget unreadable.
        #
        # MEASURED ON myposter.de
        #     After the click there are three frames. One of them is
        #     about:blank, 380x700, carries a message box, and contains
        #     "MYPOSTER sagt: Herzlich willkommen bei MYPOSTER…" — the greeting.
        #     We threw it away on the URL alone. Modern widgets inject their
        #     content into a blank iframe precisely to avoid a network round
        #     trip, so the URL says nothing about whether there is a
        #     conversation inside.
        #
        #     Four hypotheses were tested before this one (wrong element, lost
        #     tag, reading too early, the SSRF guard) and all four were wrong.
        #     A frame is judged by what is in it: text, a box to type in, and a
        #     size that could hold a conversation.
        if url.startswith(("data:", "javascript:")):
            continue
        name = frame.name or ""
        if probes.NOT_CHAT.search(url) or probes.NOT_CHAT.search(name):
            continue
        try:
            info = await frame.evaluate(_FRAME_PROBE)
        except Exception:
            continue                       # detached mid-read, or still loading
        text = (info.get("text") or "").strip()
        if len(text) < 8:
            continue
        if probes.NOT_CHAT.search(text[:400]):
            continue
        # Reject frames too small to be a conversation — ad slots and pixels.
        area = 0.0
        try:
            el = await frame.frame_element()
            box = await el.bounding_box()
            if box:
                area = box["width"] * box["height"]
                if box["width"] < 140 or box["height"] < 100:
                    continue
        except Exception:
            pass
        chatty = bool(probes.CHATTY_TEXT.search(url + " " + name + " " +
                                                (info.get("title") or "")))
        out.append({
            "how": "cross-origin chat frame with a message box" if info.get("hasInput")
                   else ("cross-origin chat frame" if chatty else "iframe"),
            "text": text, "hasInput": bool(info.get("hasInput")),
            "chatty": chatty, "fresh": url not in before_urls, "area": area,
        })
    out.sort(key=lambda c: (not c["hasInput"], not c["chatty"], not c["fresh"],
                            c["area"] or 1e12))
    return out


# What is actually at the click point. A launcher can be found, visible and
# perfectly clickable in the DOM while something else sits on top of it.
#
# MEASURED, AND IT IS THE REAL BOTTLENECK
#     myposter.de: the "Hilfe" button is found every run, the click lands, and no
#     frame or panel ever appears — because a Didomi consent backdrop covers the
#     whole page. We clicked the cookie wall. Diagnosed by counting frames after
#     the click: one, the main frame, every time.
#
#     This is not a bug to route around. It is a finding: if a visitor cannot
#     reach the assistant until they answer a cookie banner, then whatever the
#     assistant says about being AI is gated behind consent — and we can say that
#     precisely instead of returning a shrug. We still do not click the banner:
#     answering it is a legal act, it is the site owner's to make, and it changes
#     what is being measured.
_WHAT_IS_ON_TOP = r"""
([x, y]) => {
  const el = document.elementFromPoint(x, y);
  if (!el) return {covered: true, what: '', consent: false};
  const CONSENT = /cookie|consent|einwillig|zustimm|akzeptier|didomi|usercentrics|cookiebot|onetrust|sourcepoint|borlabs|klaro|privacy|datenschutz/i;
  let node = el, depth = 0, blob = '';
  while (node && depth < 6) {
    blob += ' ' + (node.id || '') + ' ' + ((node.className || '') + '');
    node = node.parentElement; depth++;
  }
  const text = (el.innerText || el.textContent || '').slice(0, 160);
  return {covered: true, consent: CONSENT.test(blob) || CONSENT.test(text),
          what: (blob.trim().slice(0, 120) || el.tagName)};
}
"""


async def _read_greeting(page, launcher: dict) -> tuple[bool, str, str]:
    """
    Click the launcher once, then read ONLY what opened. Returns
    (opened, greeting, how) where `how` names the surface it came from, or
    ("", "") when nothing attributable appeared.

    THE RULE THIS FUNCTION EXISTS TO MAKE AUDITABLE
        One mouse click. No keyboard, no form fill, no submit, no second click.
        There is deliberately no code path here that can put characters into the
        widget, so "we never send your bot a message" is a property of the
        implementation and not a promise in a paragraph. If that has to change it
        changes here, in one place, visibly.
    """
    try:
        before = await page.evaluate(_BEFORE_KEYS)
    except Exception:
        before = []
    before_frames = {f.url for f in page.frames if f.url}

    # Re-find and re-tag the launcher on the CURRENT DOM, immediately before
    # clicking. The tag was set when the button was detected, but the probes run
    # in between and myposter.de is a Nuxt app that re-renders its footer — the
    # element gets replaced and the attribute goes with it. That made the
    # consent-bypass click land on nothing: one `disclosed` in about six attempts,
    # four `not_determinable` in a row when measured properly. A feature that
    # works one run in six is not a feature, and a single lucky run is not a
    # result.
    try:
        fresh = [e for e in await page.evaluate(probes.WALK_FIXED) if e.get("chatty")]
    except Exception:
        fresh = []
    if fresh:
        launcher = fresh[0]

    # Is anything sitting on top of the button before we bother clicking it?
    x, y = launcher["box"]["x"], launcher["box"]["y"]
    try:
        on_top = await page.evaluate(_WHAT_IS_ON_TOP, [x, y])
    except Exception:
        on_top = {}
    bypassed = False
    if on_top.get("consent"):
        # Their cookie wall covers the coordinates. We click the ELEMENT instead.
        #
        # WHY THIS IS THE LEAST INVASIVE OPTION, NOT A LOOPHOLE
        #     The alternatives are worse. Pressing "Accept all" records full
        #     consent on their system. Pressing "Reject all" records a consent
        #     decision too — at scale that pollutes the consent analytics their own
        #     compliance depends on. Clicking the chat button answers the banner
        #     neither way and records nothing: we decline to make a choice that is
        #     theirs to make.
        #
        #     The greeting we then read is the same one a consenting visitor sees.
        #     Art. 50(1) is about what the person is told, and the person does get
        #     there — by a different route. The report says we did this, because a
        #     reader has to know the widget was opened past a banner rather than in
        #     front of one.
        try:
            await page.evaluate(
                "(t) => { const el = document.querySelector("
                "`[data-llmantis-launcher=\"${t}\"]`); if (el) el.click(); }",
                launcher.get("tag", 0))
            bypassed = True
        except Exception:
            return False, "", "blocked-by-consent"
    else:
        try:
            await page.mouse.click(x, y)
        except Exception:
            return False, "", ""
    # WAIT FOR THE GREETING. Do not sleep and hope.
    #
    # This was a flat 4.5 s, and it was the actual reason myposter.de came back
    # unreadable four runs out of four. Diagnosed by clicking by hand: the click
    # works and two frames appear — a Zendesk launcher frame and the widget frame —
    # but the widget has not fetched its greeting yet. At 4.5 s the frame is empty,
    # gets filtered for having no text, and the whole check reports "nothing we
    # could attribute to an assistant". The one `disclosed` seen in about six
    # attempts was this race being won by luck.
    #
    # It is the same mistake as the first version of _settle, made again a few
    # hundred lines away: a fixed sleep against a network-bound event. Poll, return
    # the moment there is something to read, and give up at a bound rather than
    # sitting in someone else's chat indefinitely.
    #
    # Cross-origin frames are checked first: that is where third-party widgets
    # live, and the in-page detector is structurally blind to them.
    suffix = " (opened past your cookie banner)" if bypassed else ""
    frames: list[dict] = []
    waited = 0
    while waited < 14000:
        await page.wait_for_timeout(1200)
        waited += 1200
        frames = await _chat_frames(page, before_frames)
        if frames and (frames[0]["hasInput"] or frames[0]["chatty"]):
            return True, frames[0]["text"], frames[0]["how"] + suffix
        # Something readable but not obviously a conversation. Keep waiting a
        # little in case the real panel is still coming, then settle for it.
        if waited >= 6000 and frames:
            break

    try:
        panel = await page.evaluate(_WIDGET_PANEL, before)
    except Exception:
        panel = None
    if panel and panel.get("text"):
        return True, panel["text"].strip(), panel.get("how", "") + suffix

    # A frame with readable text but no message box and no chat wording. Real
    # enough to report, not attributable enough to accuse on — the caller only
    # accuses when the source names an iframe or a message box.
    if frames:
        return True, frames[0]["text"], frames[0]["how"] + suffix
    return True, "", ("consent-covered" if bypassed else "")


async def _settle(page, budget_ms: int = 18000) -> None:
    """
    Scroll once, then wait for a chat-like pinned element rather than sleeping.

    Five runs against westwing.de with a fixed sleep gave `disclosed` three times
    and `no_widget_found` twice — the same site, the same code. The widget had not
    rendered yet. A verdict that changes between runs is worthless, and it is the
    exact defect this product exists to find in other people's systems.
    """
    deadline, step, scrolled = budget_ms, 700, False
    while deadline > 0:
        try:
            if any(e.get("chatty") for e in await page.evaluate(probes.WALK_FIXED)):
                return
        except Exception:
            pass
        if not scrolled and deadline < budget_ms - 1500:
            try:
                for frac in (0.4, 0.8, 1.0):
                    await page.evaluate(
                        f"() => scrollTo(0, document.body.scrollHeight*{frac})")
                    await page.wait_for_timeout(400)
                await page.mouse.move(200, 400)
                await page.evaluate("() => scrollTo(0, 0)")
            except Exception:
                pass
            scrolled = True
        await page.wait_for_timeout(step)
        deadline -= step


async def check(url: str, *, authorized: bool = False, exhaustive: bool = True,
                open_widget: bool = True, allow_private: bool = False,
                on_progress=None, timeout_ms: int = 25000) -> Art50Report:
    """
    One Art.-50 check.

    open_widget  click the launcher and read what the assistant says first.
                 DEFAULT TRUE, including for the free check — team decision 18.08.

                 Clicking a public button is not sending a message. The greeting
                 appears on its own; nothing is submitted, no conversation is
                 authored by us, and Art. 50(1) is about precisely that greeting.
                 An earlier version conflated the click with messaging and gated
                 it behind ownership, which cost the free check the only verdict
                 worth having: of three widgets found across 24 sites, exactly one
                 disclosed on the launcher itself. The other two were unknowable
                 from outside for no good reason.

                 What stays forbidden without ownership is unchanged and is
                 enforced below: we never type, never submit, never reply, and
                 never run an attack. See _read_greeting.
    authorized   ownership proven by DNS TXT (ownership.py). Reserved for the
                 red-team scan, which drives real attacks at the bot. It no longer
                 governs whether we may look inside the widget.
    allow_private
                 permit a loopback or private-network target. FALSE by default and
                 an explicit ARGUMENT rather than an environment flag, on purpose.

                 The first version read config.ALLOW_PRIVATE_SCAN_TARGETS here,
                 copying what scanner.py does. That was wrong and dangerous: the
                 env flag was designed for mode="api" scans, which require a login
                 AND org membership, whereas /api/art50check is anonymous. The repo
                 .env already sets it true for Gregor's lab, so a deploy carrying
                 that value would have turned the free check into an open SSRF
                 proxy — anyone could aim it at cloud metadata on 169.254.169.254.

                 Only in-process callers that can prove why (the fixture tests,
                 the prototype CLI) pass this. The HTTP endpoint never does.
    exhaustive   every candidate page and both form factors, no early exit.
                 Default TRUE, including for the free check: a negative result is
                 worth what the list behind it is worth.
    on_progress  async callback(event: dict) for streaming. The caller watching
                 us try twelve methods on nine pages is the evidence of diligence.
    """
    import time
    from playwright.async_api import async_playwright

    started = time.time()

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    # Guard 1: refuse before anything launches.
    #
    # config.ALLOW_PRIVATE_SCAN_TARGETS is the same escape scanner.py uses for
    # the local lab, and it exists for the same reason here: the fixtures in
    # tools/art50v2 are the only pages whose correct verdict is known, and they
    # are served from 127.0.0.1. It defaults OFF, so a deployed instance still
    # refuses every private address — turning it on ON A SHARED HOST is an SSRF
    # hole, which is why config.py says local development only.
    if not allow_private:
        assert_public_host(url)

    rep = Art50Report(url=url, robots=robots_state(url), authorized=authorized)

    async def emit(kind: str, **kw):
        if on_progress:
            await on_progress({"type": kind, **kw})

    await emit("start", url=url, robots=rep.robots,
               probes=len(probes.PROBE_NAMES), exhaustive=exhaustive)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--disable-dev-shm-usage"])
        merged: list[ProbeResult] = []
        launchers: list[dict] = []
        page = ctx = None

        for label, ua, viewport, mobile in VIEWPORTS:
            if ctx is not None:
                await ctx.close()
            ctx = await browser.new_context(
                user_agent=ua, extra_http_headers=HEADERS, viewport=viewport,
                locale="de-DE", is_mobile=mobile, has_touch=mobile)
            page = await ctx.new_page()
            requests: list[str] = []
            sockets: list[str] = []
            page.on("request", lambda q: requests.append(q.url))
            page.on("websocket", lambda ws: sockets.append(ws.url))

            # Guard 2: every request the page actually makes is re-checked. This
            # is the DNS-rebinding half (technical debt #14): assert_public_host
            # resolves the name once, the browser resolves it again, and a name
            # with TTL 0 could be public on the first lookup and 127.0.0.1 on the
            # second. Nothing but per-request interception catches that.
            async def _guard(route):
                target = route.request.url
                if allow_private:
                    await route.continue_()
                    return
                try:
                    if target.startswith(("file:", "data:", "blob:")) or \
                            is_private_url(target):
                        rep.blocked_requests += 1
                        await route.abort()
                        return
                except Exception:
                    rep.blocked_requests += 1
                    await route.abort()
                    return
                await route.continue_()

            await page.route("**/*", _guard)

            async def visit(target: str) -> tuple[list[ProbeResult], list[dict], str]:
                await emit("page", url=target, viewport=label)
                try:
                    r = await page.goto(target, wait_until="domcontentloaded",
                                        timeout=timeout_ms)
                except Exception as e:
                    rep.pages_tried.append({"url": target, "viewport": label,
                                            "http": None, "error": type(e).__name__})
                    return [], [], type(e).__name__
                st = r.status if r else None
                err = f"HTTP {st}" if st and st >= 400 else ""
                rep.pages_tried.append({"url": target, "viewport": label,
                                        "http": st, "error": err})
                if err:
                    return [], [], err
                await _settle(page)
                res = await probes.run_all(page, requests, sockets, SIGS)
                for p in res:
                    await emit("probe", name=p.name, fired=p.fired,
                               confidence=p.confidence, description=p.description,
                               detail=(p.findings[0] if p.findings else p.note)[:160])
                try:
                    els = [e for e in await page.evaluate(probes.WALK_FIXED)
                           if e.get("chatty")]
                except Exception:
                    els = []
                return res, els, ""

            results, here, err = await visit(url)
            merged = _merge(merged, results)
            if here:
                launchers, rep.viewport = here, label
            elif not rep.viewport:
                rep.viewport = label

            if exhaustive or not probes.launchers_from(results):
                targets: list[str] = []
                try:
                    for l in await page.evaluate(_HELP_LINKS):
                        if urlparse(l["href"]).netloc == urlparse(url).netloc:
                            targets.append(l["href"])
                except Exception:
                    pass
                targets += [urljoin(url, p) for p in CANDIDATE_PATHS]
                tried = {url.rstrip("/")}
                for t in targets:
                    if t.rstrip("/") in tried or len(tried) > MAX_PAGES_PER_VIEWPORT:
                        continue
                    tried.add(t.rstrip("/"))
                    r2, l2, e2 = await visit(t)
                    if e2:
                        continue
                    merged = _merge(merged, r2)
                    if l2 and not launchers:
                        launchers, rep.viewport = l2, label
                    if probes.launchers_from(r2) and not exhaustive:
                        break

            if probes.launchers_from(merged) and not exhaustive:
                break

        results = merged
        rep.probe_log = [p.as_dict() for p in results]

        if not results:
            rep.verdict = "not_determinable"
            errs = [p["error"] for p in rep.pages_tried if p.get("error")]
            rep.reason = ("No page could be loaded"
                          + (f" ({errs[0]})" if errs else "")
                          + ". Nothing is claimed about this site either way.")
        else:
            rep.launcher_label = " | ".join(
                l["visible"] for l in launchers if l["visible"])[:600]
            rep.launcher_technical = " | ".join(
                l["technical"] for l in launchers if l["technical"])[:400]
            fired = [p for p in results if p.fired and p.name != "consent_gate"]
            consent = any(p.name == "consent_gate" and p.fired for p in results)

            if not fired:
                rep.verdict = "no_widget_found"
                rep.reason = (
                    f"All {len(results)} detection methods were run on "
                    f"{len(rep.pages_tried)} page(s) and none found a chat widget.")
                rep.reason += (
                    " A cookie banner was covering the page, and many widgets do not "
                    "load until consent is given — we do not click it on your behalf."
                    if consent else
                    " A widget behind a login or a specific flow would not be seen; "
                    "this is not proof none exists.")
            elif probes.weak_only(results):
                rep.verdict = "not_determinable"
                rep.reason = (
                    f"Only weak signals fired ({', '.join(p.name for p in fired)}) — a "
                    "word in the page's own copy, not the widget itself. Enough to look "
                    "closer, not enough to judge, so nothing is claimed.")
            else:
                hit = first_match(DISCLOSE, rep.launcher_label, context=45)
                if hit:
                    rep.verdict, rep.evidence = "disclosed", hit
                    rep.reason = ("The chat launcher itself identifies the assistant "
                                  "as AI, visible before any interaction.")

                if open_widget and launchers and not hit:
                    await emit("opening", label=launchers[0].get("visible", "")[:80])
                    (rep.opened_widget, rep.first_message,
                     rep.greeting_source) = await _read_greeting(page, launchers[0])
                    if not rep.opened_widget:
                        if rep.greeting_source == "blocked-by-consent":
                            rep.greeting_source = ""
                            rep.reason = (
                                "Your chat button is there, but your own cookie "
                                "banner covers it — a visitor cannot reach the "
                                "assistant until they answer the banner, and neither "
                                "could we. We do not answer it on your behalf. That "
                                "also means whatever your assistant says about being "
                                "AI is gated behind a consent decision, which is "
                                "worth looking at on its own.")
                        else:
                            rep.reason = ("The chat button was found but would not "
                                          "open, so nothing is claimed either way.")
                    # Photograph the open chat before anything else can close it.
                    # A quote with no picture beside it is a claim; a quote beside
                    # a screenshot of the thing that said it is checkable in two
                    # seconds, which is what the customer is actually buying.
                    if rep.opened_widget:
                        try:
                            import base64 as _b64
                            rep.widget_shot_b64 = _b64.b64encode(
                                await page.screenshot(full_page=False)).decode()
                        except Exception:
                            pass
                    if rep.opened_widget:
                        rep.impersonation = first_match(IMPERSONATION,
                                                        rep.first_message, context=30)
                        hit = first_match(DISCLOSE, rep.first_message, context=60)
                        if hit:
                            rep.verdict, rep.evidence = "disclosed", hit
                            rep.reason = ("The assistant's first message discloses "
                                          "that it is AI.")
                        # ATTRIBUTABLE means "something you could have talked to".
                        # An iframe filtered against NOT_CHAT, or a panel with a
                        # message box in it. A bare floating card is not a chat and
                        # its text is not a greeting: measured on 10 German sites,
                        # bare panels produced two false accusations out of three —
                        # ionos.de's customer testimonial ("Simone Rapp-Scheider,
                        # Wohlfühlmomente Landau") and flaschenpost.de's shopping
                        # cart ("Mindestbestellwert Gesamt Noch 0,00 €"), both
                        # quoted under a verdict of not_disclosed. o2online.de's
                        # real bot came through an iframe and survived.
                        elif (rep.first_message
                              and ("iframe" in rep.greeting_source
                                   or "message box" in rep.greeting_source)):
                            rep.verdict = "not_disclosed"
                            rep.evidence = rep.first_message[:300]
                            rep.reason = (
                                "The assistant opened and greeted the visitor without "
                                "stating that it is an AI system, which is what "
                                "Art. 50(1) requires at first interaction.")
                            if rep.impersonation:
                                rep.reason += (" It presents itself as a person, "
                                               "which is the opposite of disclosure.")
                        else:
                            # Nothing we could attribute to an assistant. Two ways
                            # to get here and both must stay silent: no panel found
                            # at all, or a floating box with no way to reply, which
                            # is a card and not a conversation. Unattributed text
                            # must never become an accusation — reading the whole
                            # page instead is how a cookie banner and five
                            # Trustpilot reviews were once quoted as "what your
                            # assistant said first" under a verdict of
                            # not_disclosed.
                            was_covered = rep.greeting_source == "consent-covered"
                            rep.verdict = "not_determinable"
                            rep.first_message = ""
                            rep.greeting_source = ""
                            rep.reason = (
                                "Your cookie banner covers the chat button. We "
                                "pressed the button itself rather than answering the "
                                "banner — that decision is yours — and the assistant "
                                "did not come up. A visitor who has not consented "
                                "cannot reach it either, which means whatever it says "
                                "about being AI is gated behind consent."
                                if was_covered else
                                "The chat button opened something, but nothing we "
                                "could attribute to an assistant — no message box to "
                                "reply in, and no readable chat frame. Nothing is "
                                "claimed about what your assistant says. We do not "
                                "quote text we cannot attribute to it.")

                if rep.verdict == "not_determinable" and not rep.reason:
                    rep.reason = (
                        f"A chat widget is present (found by: "
                        f"{', '.join(p.name for p in fired)}) but its launcher says "
                        "nothing about AI, and we did not open it. The disclosure "
                        "Art. 50(1) requires may well be in the assistant's first "
                        "message. Verify ownership of this domain to have the "
                        "assistant itself checked.")

        if page is not None:
            try:
                import base64
                rep.screenshot_b64 = base64.b64encode(
                    await page.screenshot(full_page=False)).decode()
            except Exception:
                pass

        await browser.close()

    rep.duration_s = round(time.time() - started, 1)
    return rep
