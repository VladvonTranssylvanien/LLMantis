#!/usr/bin/env python3
"""
art50check.py — LLMantis hypothesis check, 20 minutes.

What it does: visits German company websites AS AN ORDINARY VISITOR and looks at
whether there is a chat widget and whether it discloses that it is AI
(Art. 50(1) EU AI Act, in force since 2 August 2026).

🔴 PASSIVE ONLY. We send the bot no messages and attack nothing.
   One GET of a public page — exactly what any visitor's browser does.

Usage:
    pip install httpx beautifulsoup4
    python tools/art50check.py sites.txt

sites.txt — one domain per line, 20-24 of them.

Output is the number for the landing page and the pitch:
    "X von 24 deutschen Unternehmens-Chatbots weisen nicht darauf hin,
     dass sie KI sind."
"""

import asyncio          # for concurrent-but-polite requests
import csv
import re
import sys
from dataclasses import dataclass, asdict

import httpx
from bs4 import BeautifulSoup

# Identifiable User-Agent pointing at an explanation page — required by our
# playbook. A site administrator must be able to find out who visited them.
UA = "LLMantis-Checker/0.1 (+https://llmantis.de/scanner)"

PAUSE_SECONDS = 2.0     # pause between sites — politeness, not a technical need
TIMEOUT = 15.0

# Known chat widget vendors. We look for their scripts in the page HTML.
# Extend this list as we find more.
WIDGET_SIGNATURES = {
    "Intercom":    [r"intercom", r"widget\.intercom\.io"],
    "Tidio":       [r"tidio", r"code\.tidio\.co"],
    "Userlike":    [r"userlike", r"userlike-cdn"],
    "Crisp":       [r"crisp\.chat", r"client\.crisp"],
    "Zendesk":     [r"zdassets", r"zendesk.*widget"],
    "HubSpot":     [r"js\.hs-scripts", r"hubspot.*conversations"],
    "Freshchat":   [r"freshchat", r"wchat\.freshchat"],
    "LiveChat":    [r"livechatinc"],
    "Drift":       [r"js\.driftt"],
    "Chatbase":    [r"chatbase\.co"],
    "Voiceflow":   [r"voiceflow"],
    "Botpress":    [r"botpress"],
    "Generic-AI":  [r"ai[-_]?chat", r"chatbot", r"kundenservice[-_]?bot"],
}

# Words indicating the widget DISCLOSES its nature (Art. 50(1)).
# German and English, because many sites mix both.
AI_DISCLOSURE = [
    r"\bKI\b", r"künstliche intelligenz", r"KI-Assistent", r"KI-gestützt",
    r"\bAI\b", r"artificial intelligence", r"AI assistant",
    r"virtueller assistent", r"automatisiert", r"chatbot", r"bot\b",
]


@dataclass
class Result:
    domain: str
    reachable: bool = False
    has_widget: bool = False
    widget_vendor: str = ""
    discloses_ai: bool = False      # ⭐ the field that matters — this IS Art. 50
    privacy_link_near: bool = False
    impressum: bool = False
    note: str = ""


def find_widget(html: str) -> tuple[bool, str]:
    """Look for known chat widget signatures in the page HTML."""
    low = html.lower()
    for vendor, patterns in WIDGET_SIGNATURES.items():
        for p in patterns:
            if re.search(p, low, re.I):
                return True, vendor
    return False, ""


def discloses_ai(html: str) -> bool:
    """
    Does the page contain text disclosing the assistant's AI nature?

    ⚠️ This is a COARSE heuristic. It gives a lower bound, not a precise answer:
    a widget's actual first message is often loaded by JavaScript and is not in
    the HTML at all. Therefore:
      - True  → almost certainly discloses (strong signal)
      - False → MUST BE CHECKED BY HAND before counting it as a violation
    That is why the CSV below has a manual_check column.
    """
    for p in AI_DISCLOSURE:
        if re.search(p, html, re.I):
            return True
    return False


async def check(client: httpx.AsyncClient, domain: str) -> Result:
    r = Result(domain=domain)
    url = domain if domain.startswith("http") else f"https://{domain}"

    try:
        resp = await client.get(url, timeout=TIMEOUT, follow_redirects=True)
        r.reachable = resp.status_code < 400
        html = resp.text
    except Exception as e:
        r.note = f"{type(e).__name__}: {e}"
        return r

    r.has_widget, r.widget_vendor = find_widget(html)

    # Only look for disclosure if a widget exists at all — otherwise the word
    # "KI" somewhere in the page copy produces a false result.
    if r.has_widget:
        r.discloses_ai = discloses_ai(html)

    soup = BeautifulSoup(html, "html.parser")
    links = " ".join(a.get_text(" ", strip=True).lower() for a in soup.find_all("a"))
    r.privacy_link_near = "datenschutz" in links
    r.impressum = "impressum" in links

    return r


async def main(path: str):
    domains = [d.strip() for d in open(path) if d.strip() and not d.startswith("#")]

    results: list[Result] = []
    async with httpx.AsyncClient(headers={"User-Agent": UA}) as client:
        for d in domains:
            res = await check(client, d)
            results.append(res)
            flag = "🤖" if res.has_widget else "  "
            ok = "✅" if res.discloses_ai else ("🔴" if res.has_widget else "  ")
            print(f"{flag} {ok} {d:<40} {res.widget_vendor or res.note[:30]}")
            await asyncio.sleep(PAUSE_SECONDS)   # polite pause

    # ---- The number this whole script exists for ----
    reachable = [r for r in results if r.reachable]
    with_bot = [r for r in reachable if r.has_widget]
    silent = [r for r in with_bot if not r.discloses_ai]

    print("\n" + "=" * 60)
    print(f"Sites checked:                  {len(results)}")
    print(f"  reachable:                    {len(reachable)}")
    print(f"  with a chat widget:           {len(with_bot)}")
    print(f"  🔴 with NO clear AI notice:   {len(silent)}")
    if with_bot:
        print(f"\n  → {len(silent)} of {len(with_bot)} bots do not disclose they are AI")
        print(f"    Art. 50(1) EU AI Act has applied since 02.08.2026")
    print("=" * 60)
    print("\n⚠️  CHECK EVERY 🔴 ROW BY HAND before putting the number in a pitch.")
    print("    The widget may load its text via JavaScript.")
    print("    A number you did not verify is the number you get caught on.\n")

    with open("art50-results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(results[0]).keys()) + ["manual_check"])
        w.writeheader()
        for r in results:
            row = asdict(r)
            row["manual_check"] = "TODO" if (r.has_widget and not r.discloses_ai) else ""
            w.writerow(row)
    print("→ art50-results.csv")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "sites.txt"))
