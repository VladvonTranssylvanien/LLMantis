"""
Art.-50 disclosure engine — browser-driven. PROTOTYPE, not wired into backend/.

WHY THIS EXISTS
    backend/art50check.py does one passive GET and greps the whole page. Measured
    on 24 real German sites, that cannot do the job:

      * 6 of 24 never served a usable page to a non-browser client (403/429/401,
        a 202 with an empty body, an 11 KB app shell).
      * Widget vendors are no longer third-party domains. Sites bundle the widget
        into their own build: static.vattenfall.de/.../chatBot.js,
        myposter.de/_nuxt/ZendeskMessengerLauncher.css, and westwing.de's
        ChatOverlayContent-…js from a Shopify CDN.
      * Grepping page text produced false passes: "assistant" in a job ad, and
        otto.de matching "chatbot" inside a JSON feature-flag blob.

EVERY PROBE RUNS, EVERY TIME
    Detection lives in probes.py as ten named probes, and none of them
    short-circuits. A negative result is only worth something with the list of
    things that were tried, which is what a Nachweis der Sorgfalt is. Counting
    hits per probe is also what showed the borrowed Wappalyzer signatures firing
    ZERO times on 24 sites while three signals we wrote found everything.

THE VERDICT HAS FOUR VALUES AND ONE OF THEM IS GATED
    `disclosed`         the launcher or the greeting says it is AI
    `not_disclosed`     the greeting was READ and says nothing — authorised only
    `not_determinable`  a widget is there but we did not open it, or could not
    `no_widget_found`   nothing fired

    Measured: of 3 widgets found across 24 sites, only westwing.de could be
    judged from outside. A launcher that says nothing is not evidence of
    non-compliance, because Art. 50(1) governs what a person is told when the
    conversation starts, and that text is inside the widget. Claiming otherwise
    would be the § 5 UWG problem PLAYBOOK.md forbids everywhere else.

ROBOTS.TXT IS RECORDED, NOT ENFORCED
    Team decision, 17.08. RFC 9309 is a voluntary IETF standard, not law; the
    German case law that gives it force (§ 44b UrhG, OLG Hamburg 5 U 104/24)
    concerns text-and-data mining under copyright, not whether a page may be
    loaded. Recorded on every result anyway, because a report should say what the
    site asked for even where we proceeded. Measured: 0 of 24 disallowed us.
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

from tools.art50v2 import probes
from tools.art50v2.probes import ProbeResult

HERE = Path(__file__).parent

# A real browser UA. obi.de answers 404 to "LLMantis-Checker" and 200 to Chrome,
# so an honest-but-unusual UA loses pages for nothing. Identity is carried by the
# header instead, and navigator.webdriver is deliberately left visible: no
# stealth plugin, no proxy. A site that blocks us is a finding.
UA_DESKTOP = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")
UA_MOBILE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 "
             "Safari/604.1")
HEADERS = {"X-LLMantis-Checker": "1.0 (+https://llmantis.de/scanner)"}

VIEWPORTS = [
    ("desktop", UA_DESKTOP, {"width": 1280, "height": 900}),
    # Some widgets render only on one form factor, and a launcher hidden below
    # 768px is invisible to a desktop-only check. Tried second, and only when
    # desktop found nothing, so the common case still costs one page load.
    ("mobile", UA_MOBILE, {"width": 390, "height": 844}),
]

# German first, because the market is German. Both lexicons always run: a German
# site can carry an English bot, and gating on a detected language is its own
# failure mode. Extended from tools/art50check.py.
DISCLOSE = [
    r"\bKI\b", r"künstliche intelligenz", r"KI-Assistent", r"KI-gestützt",
    r"KI-Chat", r"KI-Bot", r"virtueller assistent", r"digitaler assistent",
    r"automatisierter assistent", r"automatisiert", r"\bchatbot\b", r"\bbot\b",
    r"kein mensch", r"nicht menschlich", r"maschine", r"KI-basiert",
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

# Pages a bot is likely to live on, tried in order after the entry page. The
# site's own navigation is preferred over these; guessed paths 404'd on two of
# two attempts (congstar.de/hilfe-und-service, check24.de/kontakt), which is why
# discovery comes first and these are only the fallback.
CANDIDATE_PATHS = ["/hilfe", "/kontakt", "/service", "/support", "/faq",
                   "/kundenservice", "/help", "/contact"]

VERDICTS = ("disclosed", "not_disclosed", "not_determinable", "no_widget_found")


@dataclass
class Art50Report:
    url: str
    verdict: str = "not_determinable"
    reason: str = ""
    evidence: str = ""                  # the exact words judged on
    launcher_label: str = ""            # human-visible text, safe to quote
    launcher_technical: str = ""        # ids/classes: detection only, never evidence
    first_message: str = ""
    impersonation: str = ""
    robots: str = ""
    authorized: bool = False
    opened_widget: bool = False
    screenshot: str = ""
    viewport: str = ""                  # which form factor found it
    exhaustive: bool = False            # every page and form factor, no early exit
    pages_tried: list[dict] = field(default_factory=list)
    probe_log: list[dict] = field(default_factory=list)

    @property
    def probes_fired(self) -> list[str]:
        return [p["name"] for p in self.probe_log if p["fired"]]

    @property
    def probes_attempted(self) -> int:
        return len(self.probe_log)

    def as_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()}
        assert d["verdict"] in VERDICTS, d["verdict"]
        d["probes_fired"] = self.probes_fired
        d["probes_attempted"] = self.probes_attempted
        return d


def _load_signatures() -> dict:
    """Wappalyzer live-chat fingerprints (category 52), if fetched.

    Optional on purpose: they have never once fired on a real German site, and
    the probes that do work are ours. A missing file must degrade the check, not
    break it.
    """
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

    Fetched with a browser UA, because an unreadable robots.txt is not a
    prohibition and 6 of 24 sites 403 a non-browser client on this file alone. An
    earlier version used RobotFileParser.read(), which treats a 403 as "disallow
    everything" — that turned bot protection into nine phantom refusals and is
    the worst measurement error made on this feature.
    """
    p = urlparse(url)
    try:
        body = urlopen(
            Request(f"{p.scheme}://{p.netloc}/robots.txt",
                    headers={"User-Agent": UA_DESKTOP}), timeout=10,
        ).read().decode("utf-8", "replace")
    except Exception:
        return "unreadable"
    rp = RobotFileParser()
    rp.parse(body.splitlines())
    return "allows" if rp.can_fetch("LLMantis-Checker", url) else "DISALLOWS"


def first_match(patterns: list[str], text: str, context: int = 0) -> str:
    """
    The first matching phrase, optionally widened to the words around it.

    context matters for the evidence field, which is what a Prüfbericht quotes.
    The bare match on westwing.de is "AI" — two letters prove nothing to a reader.
    Widened it is "Westwing AI (BETA)", checkable against the screenshot beside it.
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


# Text surfaces, main document plus iframes plus shadow roots. Snapshotted before
# the click and after, so only what the click PRODUCED counts as the greeting.
# innerText crosses neither an iframe nor a shadow boundary, and
# "Westwing AI (BETA)" was absent from document.body.innerText on 6 of 6 runs for
# exactly that reason.
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
  return chunks.join('\\n');
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
    fresh = [l.strip() for l in after.splitlines() if l.strip() and l.strip() not in seen]
    return "\n".join(fresh)[:4000]


async def _settle(page, budget_ms: int = 20000) -> None:
    """
    Scroll once, then wait for a chat-like pinned element rather than sleeping.

    WHY THIS IS NOT AN OPTIMISATION
        The first version slept, scrolled, slept, then looked once. Five runs
        against westwing.de gave `disclosed` three times and `no_widget_found`
        twice — the same site, the same code. The widget had not rendered yet.
        A verdict that changes between runs is worthless, and it is the exact
        defect this product exists to find in other people's systems.
    """
    deadline, step, scrolled = budget_ms, 700, False
    while deadline > 0:
        try:
            els = await page.evaluate(probes.WALK_FIXED)
            if any(e.get("chatty") for e in els):
                return
        except Exception:
            pass
        if not scrolled and deadline < budget_ms - 1500:
            try:
                for frac in (0.4, 0.8, 1.0):
                    await page.evaluate(
                        f"() => scrollTo(0, document.body.scrollHeight*{frac})")
                    await page.wait_for_timeout(450)
                await page.mouse.move(200, 400)
                await page.evaluate("() => scrollTo(0, 0)")
            except Exception:
                pass
            scrolled = True
        await page.wait_for_timeout(step)
        deadline -= step


def _merge(a: list[ProbeResult], b: list[ProbeResult]) -> list[ProbeResult]:
    """
    Union of two probe runs, by probe name.

    A probe that fired anywhere counts as fired, and its findings accumulate. In
    exhaustive mode the same twelve probes run on every page and every form
    factor, and the report has to say "this fired somewhere" rather than "this
    fired on whichever page happened to be last" — which is what the earlier
    code said, because it simply overwrote.
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
            prev.fired = True
            prev.note = p.note
        for f in p.findings:
            if f not in prev.findings:
                prev.findings.append(f)
        prev.findings = prev.findings[:8]
        if not prev.fired and p.note and not prev.note:
            prev.note = p.note
    return list(by_name.values())


async def _sweep(browser, url: str, label: str, ua: str, viewport: dict,
                 rep: Art50Report, authorized: bool, timeout_ms: int,
                 exhaustive: bool = False
                 ) -> tuple[list[ProbeResult], list[dict], object, object]:
    """
    One form factor: load the entry page, then candidate pages until a probe
    fires. Returns (probe results, launcher elements, page, context) with the
    page still open so the caller can click and screenshot.
    """
    ctx = await browser.new_context(user_agent=ua, extra_http_headers=HEADERS,
                                    viewport=viewport, locale="de-DE",
                                    is_mobile=(label == "mobile"),
                                    has_touch=(label == "mobile"))
    page = await ctx.new_page()
    requests: list[str] = []
    sockets: list[str] = []
    page.on("request", lambda q: requests.append(q.url))
    page.on("websocket", lambda ws: sockets.append(ws.url))

    async def visit(target: str) -> tuple[list[ProbeResult], list[dict], str]:
        try:
            r = await page.goto(target, wait_until="domcontentloaded",
                                timeout=timeout_ms)
        except Exception as e:
            return [], [], type(e).__name__
        st = r.status if r else None
        rep.pages_tried.append({"url": target, "viewport": label,
                                "http": st, "error": f"HTTP {st}" if st and st >= 400 else ""})
        if st and st >= 400:
            return [], [], f"HTTP {st}"
        await _settle(page)
        results = await probes.run_all(page, requests, sockets, SIGS)
        try:
            els = [e for e in await page.evaluate(probes.WALK_FIXED) if e.get("chatty")]
        except Exception:
            els = []
        return results, els, ""

    results, launchers, err = await visit(url)
    if err:
        return [], [], page, ctx
    merged = list(results)

    # Nothing yet? Try the site's own navigation, then guessed paths. Each is a
    # separate attempt and each is recorded, because "we looked on four pages"
    # is the difference between a negative result and a shrug.
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
            if t.rstrip("/") in tried:
                continue
            tried.add(t.rstrip("/"))
            r2, l2, e2 = await visit(t)
            if e2:
                continue
            merged = _merge(merged, r2)
            if probes.launchers_from(r2):
                results, launchers = r2, l2
                if not exhaustive:
                    break
            if len(tried) > (9 if exhaustive else 4):
                break

    # In exhaustive mode the caller wants the union of everything tried, not the
    # last page's view of the world.
    return (merged if exhaustive else results), launchers, page, ctx


async def check(url: str, *, authorized: bool = False, exhaustive: bool = False,
                shots_dir: Path | None = None, timeout_ms: int = 30000) -> Art50Report:
    """
    One Art.-50 check.

    authorized  the caller has proven this domain is theirs — the ownership
                checkbox AND the DNS TXT verification in backend/ownership.py, as
                a checkbox alone proves nothing. Only with this do we click the
                launcher and read the greeting, because opening a chat creates a
                conversation on someone's system. Without it the strongest
                available verdict is not_determinable.
    """
    from playwright.async_api import async_playwright

    if not url.startswith(("http://", "https://")):
        # https for anything real, http for loopback: nobody serves https on
        # 127.0.0.1, and defaulting a local address to https produced a
        # connection failure reported as "not determinable" — which reads as a
        # finding about the page rather than a mistake in the argument.
        host = url.split("/", 1)[0].split(":", 1)[0]
        local = host in ("localhost", "127.0.0.1", "::1") or host.startswith("127.")
        url = f"{'http' if local else 'https'}://{url}"

    rep = Art50Report(url=url, robots=robots_state(url), authorized=authorized)
    shots = shots_dir or (HERE / "shots")
    shots.mkdir(parents=True, exist_ok=True)
    host = urlparse(url).netloc or "page"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        results: list[ProbeResult] = []
        launchers: list[dict] = []
        page = ctx = None
        rep.exhaustive = exhaustive

        merged: list[ProbeResult] = []
        for label, ua, viewport in VIEWPORTS:
            if page is not None and (launchers or not exhaustive):
                await ctx.close()
            elif page is not None:
                await ctx.close()
            results, launchers_here, page, ctx = await _sweep(
                browser, url, label, ua, viewport, rep, authorized, timeout_ms,
                exhaustive)
            merged = _merge(merged, results)
            if launchers_here:
                launchers = launchers_here
                rep.viewport = label
            elif not rep.viewport:
                rep.viewport = label
            if probes.launchers_from(results) and not exhaustive:
                break
        results = merged

        rep.probe_log = [p.as_dict() for p in results]

        if not results:
            rep.verdict = "not_determinable"
            errs = [p["error"] for p in rep.pages_tried if p.get("error")]
            rep.reason = (
                "No page could be loaded"
                + (f" ({errs[0]})" if errs else "")
                + ". Nothing is claimed about this site in either direction.")
            await browser.close()
            return rep

        rep.launcher_label = " | ".join(
            l["visible"] for l in launchers if l["visible"])[:600]
        rep.launcher_technical = " | ".join(
            l["technical"] for l in launchers if l["technical"])[:400]

        fired = [p for p in results if p.fired and p.name != "consent_gate"]
        consent = next((p for p in results if p.name == "consent_gate" and p.fired), None)

        if not fired:
            rep.verdict = "no_widget_found"
            rep.reason = (
                f"All {len(results)} detection methods were run on "
                f"{len(rep.pages_tried)} page(s) and none found a chat widget.")
            if consent:
                rep.reason += (" A cookie banner was covering the page, and many "
                               "widgets do not load until consent is given — we do "
                               "not click it on your behalf.")
            else:
                rep.reason += (" A widget behind a login or a specific flow would "
                               "not be seen; this is not proof none exists.")
        elif probes.weak_only(results):
            rep.verdict = "not_determinable"
            names = ", ".join(p.name for p in fired)
            rep.reason = (
                f"Only weak signals fired ({names}) — a word in the page's own copy, "
                "not the widget itself. That is enough to look closer and not enough "
                "to judge, so nothing is claimed.")
        else:
            hit = first_match(DISCLOSE, rep.launcher_label, context=45)
            if hit:
                rep.verdict, rep.evidence = "disclosed", hit
                rep.reason = ("The chat launcher itself identifies the assistant as "
                              "AI, visible before any interaction.")

            if authorized and launchers and not hit:
                before = await page.evaluate(_TEXT_SURFACES)
                try:
                    await page.mouse.click(launchers[0]["box"]["x"],
                                           launchers[0]["box"]["y"])
                    await page.wait_for_timeout(4500)
                    rep.opened_widget = True
                    rep.first_message = _new_text(
                        before, await page.evaluate(_TEXT_SURFACES)).strip()
                except Exception as e:
                    rep.reason = ("The launcher was found but could not be opened "
                                  f"({type(e).__name__}).")

                if rep.opened_widget:
                    rep.impersonation = first_match(IMPERSONATION, rep.first_message,
                                                    context=30)
                    hit = first_match(DISCLOSE, rep.first_message, context=60)
                    if hit:
                        rep.verdict, rep.evidence = "disclosed", hit
                        rep.reason = ("The assistant's first message discloses that "
                                      "it is AI.")
                    elif rep.first_message:
                        rep.verdict = "not_disclosed"
                        rep.evidence = rep.first_message[:300]
                        rep.reason = (
                            "The assistant opened and greeted the visitor without "
                            "stating that it is an AI system, which is what "
                            "Art. 50(1) requires at first interaction.")
                        if rep.impersonation:
                            rep.reason += (" It presents itself as a person, which is "
                                           "the opposite of disclosure.")
                    else:
                        rep.verdict = "not_determinable"
                        rep.reason = ("The launcher was opened but produced no "
                                      "readable greeting, so nothing is claimed.")

            if rep.verdict == "not_determinable" and not rep.reason:
                found_by = ", ".join(p.name for p in fired)
                rep.reason = (
                    f"A chat widget is present (found by: {found_by}) but its "
                    "launcher says nothing about AI, and we did not open it. The "
                    "disclosure Art. 50(1) requires may well be in the assistant's "
                    "first message. Verify ownership of this domain to have the "
                    "assistant itself checked.")

        f = shots / f"{host}.png"
        try:
            await page.screenshot(path=str(f))
            rep.screenshot = f.name
        except Exception:
            pass

        await browser.close()
    return rep


async def check_many(urls: list[str], *, authorized: bool = False,
                     exhaustive: bool = False,
                     concurrency: int = 3) -> list[Art50Report]:
    sem = asyncio.Semaphore(concurrency)

    async def one(u):
        async with sem:
            try:
                return await asyncio.wait_for(
                    check(u, authorized=authorized, exhaustive=exhaustive),
                    600 if exhaustive else 240)
            except Exception as e:
                r = Art50Report(url=u, verdict="not_determinable")
                r.reason = f"The check did not finish ({type(e).__name__})."
                return r

    return list(await asyncio.gather(*(one(u) for u in urls)))
