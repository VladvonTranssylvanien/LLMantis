"""
Widget-detection probes for the Art.-50 check. Every one runs on every page, and
each records whether it fired — nothing short-circuits.

Lifted from tools/art50v2/probes.py once the free check started using it. The
prototype copy stays for CLI experiments; this is the one the website runs.

WHY RUN THEM ALL RATHER THAN STOP AT THE FIRST HIT
    A Prüfbericht is a Nachweis der Sorgfalt — documented evidence that someone
    looked. "No chat widget found" is only worth anything if it comes with the
    list of things that were tried and came back empty. Stopping at the first hit
    saves a second and throws away the only part of a negative result that is
    defensible.

    It also keeps us honest about our own tools. Counting hits per probe across
    24 German sites is what revealed that the borrowed Wappalyzer fingerprints
    fired ZERO times — 378 technologies, no matches, while three signals we wrote
    ourselves found everything. That is not visible if the first hit wins.

CONFIDENCE, AND WHY IT IS NOT A SCORE
    `strong`   deterministic. A request was made, a socket was opened. It happened
               or it did not.
    `medium`   a rendered element or attribute. Real, but subject to timing —
               this is the class that made westwing.de's verdict flip between
               runs.
    `weak`     a name or a word. Enough to say "look closer", never enough to
               judge. otto.de matched "chatbot" inside a feature-flag blob.

    A weak hit alone can raise `not_determinable`. It must never produce
    `disclosed`, because that would put a guess in a paid report.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------- patterns

# Vendors that only sell chat. Their name in a request is the signal by itself.
VENDOR_ASSET = re.compile(
    r"(chat-?bot|chat-?widget|chat-?launcher|livechat|live-chat|web-?chat|"
    r"messenger-?launcher|intercom|crisp|tidio|userlike|freshchat|zopim|"
    r"zdassets|drift|cognigy|moin|melibo|kauz|onlim|solvemate|parloa|botpress|"
    r"liveagent|smartsupp|chatra|olark|purechat)", re.I)

# Platforms that sell chat as one product among many. Their name alone proves
# nothing, and treating it as a hit was a false positive on 2 of 8 sites:
# hellofresh.de loads HubSpot and congstar.de loads Salesforce, neither of which
# indicates a chat widget — HubSpot is also a CRM and analytics tag, Salesforce
# is also Marketing Cloud. Zendesk sells ticketing and help centres as well as
# chat, so it belongs here too. Each needs chat wording in the same URL.
VENDOR_PLATFORM = re.compile(
    r"(hubspot|salesforce|zendesk|genesys|liveperson|verint|sprinklr)"
    r"[^\s\"']*?(chat|messeng|conversation|embedded-?service|esw|widget)"
    r"|(chat|messeng|conversation|embedded-?service|esw)"
    r"[^\s\"']*?(hubspot|salesforce|zendesk|genesys|liveperson)", re.I)

# Any asset whose FILENAME begins "chat". Broader than the vendor list on
# purpose: westwing.de ships ChatOverlayContent-Der-J_6j.js from a Shopify CDN,
# which matches no vendor at all and was invisible until this existed.
GENERIC_ASSET = re.compile(r"/chat[a-z0-9_-]*\.(js|css|mjs)", re.I)

# Endpoints a running conversation talks to. Distinct from the asset that loads
# the widget: these mean the thing is live, not merely present.
#
# "assistant" was in this list and had to come out. westwing.de loads
# cdn.eye-able.com/altDesign/2.0/assistant/js/… — Eye-Able is ACCESSIBILITY
# software, not a chatbot, and the probe reported a hit for it. Same for bare
# "bot", which matches robots.txt fetchers and bot-detection scripts.
CHAT_ENDPOINT = re.compile(
    r"/(chat|chats|conversation|conversations|messages|messaging|"
    r"chatbot|livechat|webchat|dialogflow)(/|\?|$)", re.I)

# Chat-ish wording. Every term here is anchored, because the loose version cost
# real accuracy: "frage" matched Anfrage inside a cookie banner and turned
# tchibo.de from no_widget_found into not_determinable, and "assist" matched
# "Assistenztechnik" on an accessibility overlay.
CHATTY_TEXT = re.compile(
    r"\bchat|chatbot|\bbot\b|messenger|\bnachricht|"
    r"\bassistent\b|\bassistant\b|\bberater\b|"
    r"\bhilfe-?chat\b|\bfrage stellen\b|\bfragen\?|"
    r"schreiben sie uns|write to us|\bkonversation\b|"
    # An element pinned to a corner that says "AI" or "KI" is announcing an AI.
    # That is the cleanest signal there is, and tightening this pattern to kill
    # tchibo.de's "Anfrage" false positive removed it: westwing.de's launcher
    # reads "Westwing AI (BETA) — Suchst du etwas Bestimmtes…" and came back
    # chatty=false, so a site whose bot announces itself in the button was
    # reported as "widget present, launcher says nothing".
    r"\bKI\b|\bAI\b|künstliche intelligenz|"
    # Vendors name their own mount points. vfrc = Voiceflow React Chat.
    r"launcher|vfrc|voiceflow|webchat|web-chat", re.I)

# Things that live in a fixed corner, look chat-shaped, and are not chats. These
# are the systematic false positives — found by reading the probe log, not by
# guessing. A match here disqualifies a finding outright.
NOT_CHAT = re.compile(
    r"eye-?able|accessibility|barrierefrei|assistenztechnik|"          # a11y overlays
    r"usercentrics|cookiebot|onetrust|sourcepoint|borlabs|klaro|"      # consent CMPs
    r"consent|cookie|datenschutz|privatsphäre|einwillig|"
    r"newsletter|rabatt|gutschein|trustbadge|trustedshops|"           # marketing
    r"back-?to-?top|scroll-?to-?top|share|social|"
    # Community forums are not chat assistants. o2online.de embeds "inSided
    # in-page support" — its user forum — in a 400x720 iframe that carries a text
    # input from the moment it loads, while the real Live-Chat frame has none
    # until the conversation starts. Ranked by input alone, the forum won and the
    # assistant was never read.
    r"insided|community|forum|in-?page support|frag die community", re.I)

CONSENT = re.compile(
    r"cookie|consent|einwillig|zustimm|akzeptier|datenschutz-?einstellung|"
    r"privacy (settings|preferences)|alle akzeptieren|accept all", re.I)


# The probes, in run order. Declared here so a caller can report "12 methods
# will run" before the first page even loads — the streaming UI needs the total
# up front, and a list that drifts from run_all() would misreport it.
PROBE_NAMES = [
    "websocket", "chat_endpoint", "vendor_platform", "vendor_asset",
    "generic_chat_asset", "vendor_fingerprint", "vendor_global", "fixed_launcher",
    "iframe", "aria", "page_text", "consent_gate",
]


@dataclass
class ProbeResult:
    name: str
    description: str                 # plain language, goes in the report
    confidence: str                  # strong | medium | weak
    fired: bool = False
    findings: list[str] = field(default_factory=list)
    note: str = ""                   # why it could not run, if it could not

    def as_dict(self) -> dict:
        return dict(self.__dict__)


# ------------------------------------------------------------------- JS helpers

WALK_FIXED = r"""
() => {
  // Kept in step with CHATTY_TEXT and NOT_CHAT in this module. A cookie banner
  // and an accessibility overlay both sit fixed in a corner and both matched the
  // loose version of this, which is how tchibo.de's consent notice was reported
  // as a chat launcher.
  const CHATTY = /\bchat|chatbot|\bbot\b|messenger|\bnachricht|\bassistent\b|\bassistant\b|\bberater\b|\bhilfe-?chat\b|\bfrage stellen\b|schreiben sie uns|write to us|\bKI\b|\bAI\b|künstliche intelligenz|launcher|vfrc|voiceflow|webchat|web-chat/i;
  const NOT_CHAT = /eye-?able|accessibility|barrierefrei|assistenztechnik|usercentrics|cookiebot|onetrust|sourcepoint|borlabs|klaro|consent|cookie|datenschutz|privatsph|einwillig|newsletter|rabatt|gutschein|trustbadge|trustedshops|back-?to-?top|scroll-?to-?top/i;
  // Shadow roots are walked because innerText and querySelectorAll both stop at
  // the boundary, and westwing.de keeps its launcher text inside one.
  const all = root => {
    let out = [...root.querySelectorAll('div,button,a,iframe,[role=button]')];
    for (const el of root.querySelectorAll('*'))
      if (el.shadowRoot) out = out.concat(all(el.shadowRoot));
    return out;
  };
  const fixedAncestor = el => {
    for (let n = el, i = 0; n && i < 4; n = n.parentElement, i++)
      if (getComputedStyle(n).position === 'fixed') return n;
    return null;
  };
  const seen = new Set(), out = [];
  for (const el of all(document)) {
    const host = fixedAncestor(el);
    if (!host || seen.has(host)) continue;
    const cs = getComputedStyle(host);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) continue;
    const r = host.getBoundingClientRect();
    if (r.width < 24 || r.height < 24) continue;
    // Size is a WEAK guess and must not overrule a label that names the thing.
    //
    // westwing.de's Voiceflow container is 960x810 and its label reads
    // "Shopping Assistant (BETA)" — we threw it away for being wider than 560,
    // which is how a site whose bot announces itself in plain German came back
    // as "widget present, launcher says nothing". The cap exists to reject
    // page-sized overlays, so keep it tight when we are guessing from shape
    // alone, and relax it when the element tells us what it is. Anything
    // covering essentially the whole viewport is still out: that is a modal,
    // not a launcher.
    const lbl = [host.getAttribute('aria-label'), host.getAttribute('title'),
                 host.id, ((host.className || '') + ''),
                 (host.innerText || '').slice(0, 200)].filter(Boolean).join(' ');
    const named = CHATTY.test(lbl) && !NOT_CHAT.test(lbl);
    const nearlyFullscreen = r.width > innerWidth * 0.96 && r.height > innerHeight * 0.9;
    if (nearlyFullscreen) continue;
    if (!named && (r.width > 560 || r.height > 760)) continue;
    if (r.bottom < innerHeight * 0.45) continue;
    const visible = [host.getAttribute('aria-label'), host.getAttribute('title'),
                     (host.innerText || '').slice(0, 200)]
                    .filter(Boolean).join(' — ').slice(0, 400);
    const technical = [host.id, host.className].filter(Boolean)
                      .join(' ').toString().slice(0, 200);
    seen.add(host);
    // Tagged so the caller can click the ELEMENT rather than a screen position.
    // A consent backdrop covers coordinates; it does not remove the button.
    host.setAttribute('data-llmantis-launcher', String(out.length));
    const blob = visible + ' ' + technical;
    out.push({visible, technical, tag: out.length,
              chatty: CHATTY.test(blob) && !NOT_CHAT.test(blob),
              excluded: NOT_CHAT.test(blob),
              box: {x: r.x + r.width / 2, y: r.y + r.height / 2}});
  }
  return out.slice(0, 14);
}
"""

IFRAME_ATTRS = r"""
() => [...document.querySelectorAll('iframe')].map(f => ({
  src: f.getAttribute('src') || '', title: f.getAttribute('title') || '',
  name: f.getAttribute('name') || '', id: f.id || '',
  cls: (f.className || '').toString().slice(0, 120)
})).slice(0, 30)
"""

# Accessibility metadata. A widget that is usable by a screen reader announces
# itself, and that announcement is semi-standardised where markup is not.
ARIA_ROLES = r"""
() => {
  const out = [];
  const sel = '[role=dialog],[role=log],[role=complementary],[role=region],[aria-live]';
  const all = root => {
    let a = [...root.querySelectorAll(sel)];
    for (const el of root.querySelectorAll('*'))
      if (el.shadowRoot) a = a.concat(all(el.shadowRoot));
    return a;
  };
  for (const el of all(document)) {
    const label = [el.getAttribute('aria-label'), el.getAttribute('title'),
                   el.getAttribute('aria-roledescription')].filter(Boolean).join(' — ');
    if (label) out.push({role: el.getAttribute('role') || 'aria-live', label: label.slice(0, 160)});
  }
  return out.slice(0, 20);
}
"""

CONSENT_PRESENT = r"""
() => {
  const re = /cookie|consent|einwillig|zustimm|akzeptier|accept all|alle akzeptieren/i;
  for (const el of document.querySelectorAll('div,section,aside,dialog')) {
    const cs = getComputedStyle(el);
    if (cs.position !== 'fixed' && cs.position !== 'sticky') continue;
    const r = el.getBoundingClientRect();
    if (r.width < 200 || r.height < 60) continue;
    const t = (el.innerText || '').slice(0, 400);
    if (re.test(t)) return t.slice(0, 200);
  }
  return '';
}
"""

# Page copy, used only as a weak hint. Searching page text was how the passive
# checker passed a blog for mentioning AI, so this can never decide a verdict.
PAGE_TEXT = "() => (document.body.innerText || '').slice(0, 200000)"


# ----------------------------------------------------------------------- probes

async def run_all(page, requests: list[str], websockets: list[str],
                  signatures: dict) -> list[ProbeResult]:
    """
    Every probe, in order, none skipped. Returns one ProbeResult each so the
    report can list what was tried as well as what was found.
    """
    joined = "\n".join(requests)
    out: list[ProbeResult] = []

    def add(name, desc, conf):
        p = ProbeResult(name=name, description=desc, confidence=conf)
        out.append(p)
        return p

    # ---- strong: it happened or it did not -------------------------------
    p = add("websocket", "A live chat connection was opened (WebSocket)", "strong")
    for u in websockets:
        if NOT_CHAT.search(u):
            continue
        if CHATTY_TEXT.search(u) or CHAT_ENDPOINT.search(u):
            p.fired = True
            p.findings.append(u[:160])
    if websockets and not p.fired:
        p.note = f"{len(websockets)} socket(s) opened, none chat-related"
    elif not websockets:
        p.note = "no WebSocket was opened"

    p = add("chat_endpoint", "The page called a conversation endpoint", "strong")
    for u in requests:
        if CHAT_ENDPOINT.search(u) and not NOT_CHAT.search(u):
            p.fired = True
            p.findings.append(u[:160])
    p.findings = p.findings[:6]

    p = add("vendor_platform",
            "A support platform that also sells chat loaded something chat-shaped",
            "medium")
    for m in VENDOR_PLATFORM.finditer(joined):
        p.fired = True
        # The whole URL, not m.group(0). The pattern is non-greedy, so the raw
        # span reads as "ZendeskMesseng" — a word cut in half, which looks like a
        # bug in a report a customer is meant to trust.
        line_start = joined.rfind("\n", 0, m.start()) + 1
        line_end = joined.find("\n", m.end())
        url = joined[line_start:line_end if line_end != -1 else None]
        p.findings.append(url.strip()[:150])
    p.findings = sorted(set(p.findings))[:6]
    if not p.fired:
        p.note = ("hubspot/salesforce/zendesk alone is not a chat signal — those "
                  "names appear for CRM and analytics too")

    p = add("vendor_asset", "A chat-only vendor's name appears in a loaded file",
            "strong")
    for m in VENDOR_ASSET.finditer(joined):
        if NOT_CHAT.search(joined[max(0, m.start() - 60):m.end() + 20]):
            continue
        p.fired = True
        p.findings.append(m.group(1).lower())
    p.findings = sorted(set(p.findings))[:8]

    p = add("generic_chat_asset", "A loaded file is named chat…", "strong")
    for m in GENERIC_ASSET.finditer(joined):
        p.fired = True
        p.findings.append(m.group(0)[:120])
    p.findings = sorted(set(p.findings))[:6]

    p = add("vendor_fingerprint",
            "A chat vendor's own domain served a script (Wappalyzer signatures)",
            "strong")
    if not signatures:
        p.note = "fingerprint database not present; run fetch_signatures.py"
    else:
        for name, spec in signatures.items():
            pats = spec.get("scriptSrc") or []
            pats = pats if isinstance(pats, list) else [pats]
            for pat in pats:
                try:
                    if re.search(pat.split("\\;")[0], joined, re.I):
                        p.fired = True
                        p.findings.append(name)
                        break
                except re.error:
                    pass
        if not p.fired:
            p.note = (f"{len(signatures)} vendor signatures checked, none matched — "
                      "sites now bundle widgets into their own build")

    # ---- medium: rendered, therefore timing-dependent --------------------
    p = add("vendor_global",
            "A chat vendor's script installed a global object", "medium")
    if not signatures:
        p.note = "fingerprint database not present"
    else:
        for name, spec in signatures.items():
            for key in (spec.get("js") or {}):
                root = re.split(r"[.\[]", key)[0]
                try:
                    import json as _json
                    if await page.evaluate(
                            f"() => typeof window[{_json.dumps(root)}] !== 'undefined'"):
                        p.fired = True
                        p.findings.append(f"{name} (window.{root})")
                        break
                except Exception:
                    pass
        p.findings = p.findings[:8]

    p = add("fixed_launcher",
            "A chat-like button is pinned to a corner of the page", "medium")
    try:
        elements = await page.evaluate(WALK_FIXED)
    except Exception as e:
        elements = []
        p.note = f"could not query the page ({type(e).__name__})"
    launchers = [e for e in elements if e.get("chatty")]
    if launchers:
        p.fired = True
        for e in launchers[:4]:
            p.findings.append((e["visible"] or e["technical"])[:140])
    elif elements:
        p.note = f"{len(elements)} pinned elements found, none chat-like"
    else:
        p.note = "no pinned elements found at all"

    p = add("iframe", "A chat widget is embedded in an iframe", "medium")
    try:
        frames = await page.evaluate(IFRAME_ATTRS)
    except Exception:
        frames = []
    for f in frames:
        blob = " ".join(f.values())
        if CHATTY_TEXT.search(blob) and not NOT_CHAT.search(blob):
            p.fired = True
            p.findings.append((f["title"] or f["src"] or f["id"])[:140])
    if frames and not p.fired:
        p.note = f"{len(frames)} iframe(s), none chat-related"
    elif not frames:
        p.note = "no iframes on the page"

    p = add("aria", "Accessibility metadata announces a chat surface", "medium")
    try:
        roles = await page.evaluate(ARIA_ROLES)
    except Exception:
        roles = []
    for r in roles:
        if CHATTY_TEXT.search(r["label"]) and not NOT_CHAT.search(r["label"]):
            p.fired = True
            p.findings.append(f"{r['role']}: {r['label'][:110]}")
    if roles and not p.fired:
        p.note = f"{len(roles)} labelled regions, none chat-related"

    # ---- weak: a word. Never decides a verdict. -------------------------
    p = add("page_text", "The page's own copy mentions a chat assistant", "weak")
    try:
        text = await page.evaluate(PAGE_TEXT)
    except Exception:
        text = ""
    for m in re.finditer(r"[^\n]{0,60}(KI-Assistent|Chatbot|chat mit uns|"
                         r"chat with us|virtueller Assistent|AI assistant)[^\n]{0,60}",
                         text, re.I):
        p.fired = True
        p.findings.append(m.group(0).strip()[:140])
    p.findings = p.findings[:4]
    if p.fired:
        p.note = ("weak by construction: page copy is not the widget, and this is "
                  "how a blog mentioning AI used to pass")

    # ---- context, not detection -----------------------------------------
    p = add("consent_gate", "A cookie banner is covering the page", "weak")
    try:
        banner = await page.evaluate(CONSENT_PRESENT)
    except Exception:
        banner = ""
    if banner:
        p.fired = True
        p.findings.append(banner.replace("\n", " ")[:160])
        p.note = ("many widgets do not load until consent is given. We do not click "
                  "it — accepting on someone's behalf is a legal act and it changes "
                  "what is being measured")

    # Nothing that ran silently stays silent. Five probes were returning an empty
    # detail when they simply found nothing — and in a list that exists to prove
    # every method was tried, a blank cell reads as "did not run" rather than
    # "ran, found nothing".
    for probe in out:
        if not probe.fired and not probe.note and not probe.findings:
            probe.note = "checked, nothing matched"

    return out


def launchers_from(probe_results: list[ProbeResult]) -> bool:
    """Did any probe find something worth calling a widget?"""
    return any(p.fired for p in probe_results
               if p.name != "consent_gate" and p.confidence in ("strong", "medium"))


def weak_only(probe_results: list[ProbeResult]) -> bool:
    """Only a name or a word fired — enough to look closer, never to judge."""
    strong_medium = any(p.fired for p in probe_results
                        if p.name != "consent_gate"
                        and p.confidence in ("strong", "medium"))
    weak = any(p.fired for p in probe_results
               if p.name != "consent_gate" and p.confidence == "weak")
    return weak and not strong_medium
