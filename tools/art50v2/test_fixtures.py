"""
Validates engine.py against local pages whose correct verdict is known.

WHY FIXTURES AND NOT REAL SITES
    On 24 real German sites exactly one produced a provable verdict, so real
    traffic cannot tell us whether the engine is right — only whether the web
    cooperated. These pages are the opposite: four bots we wrote, each with one
    known-correct answer, so a wrong verdict is the engine's fault and nothing
    else. It is the same argument as calibration/set-v1.yaml.

    They also cover the step no third-party site may be used for: clicking the
    launcher and reading the greeting. Opening a stranger's chat creates a
    conversation on their system. Opening ours creates nothing.

RUN
    python tools/art50v2/test_fixtures.py
"""
from __future__ import annotations

import asyncio
import http.server
import socketserver
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.art50v2.engine import check                      # noqa: E402

HERE = Path(__file__).parent
WWW = HERE / "fixtures"
PORT = 8765

# A launcher plus a greeting that only appears after the click, so a checker that
# greps the page instead of opening the widget cannot accidentally pass.
PAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8"><title>{title}</title>
<style>
 body{{font:16px system-ui;margin:0;padding:40px;min-height:200vh}}
 #launch{{position:fixed;right:24px;bottom:24px;width:64px;height:64px;border-radius:50%;
   background:#2563eb;color:#fff;border:0;cursor:pointer;font-size:12px}}
 #panel{{position:fixed;right:24px;bottom:100px;width:340px;height:420px;
   background:#fff;border:1px solid #ccc;border-radius:12px;display:none;
   flex-direction:column}}
 #panel.on{{display:flex}}
 #panel header{{padding:12px 16px;border-bottom:1px solid #eee;font-weight:600}}
 #greeting{{flex:1;padding:16px;overflow:auto}}
 #panel footer{{padding:12px;border-top:1px solid #eee}}
 #panel input{{width:100%;padding:8px;border:1px solid #ccc;border-radius:6px}}
</style></head><body>
<h1>{title}</h1>
<p>Wir liefern Haushaltsgeräte in ganz Deutschland. Unser Team berät Sie gerne.</p>
<p>Bei uns arbeiten echte Menschen. Kein automatisiertes Callcenter.</p>
<footer><a href="/impressum">Impressum</a> · <a href="/datenschutz">Datenschutz</a></footer>
<button id="launch" aria-label="{launcher}">Chat</button>
<!-- Shaped like a real widget: a header, a message area, and a box you type in.
     The panel used to be a bare 320x60 div, which the panel detector rejected on
     height - and it was right to be suspicious of a box that small, because that
     is the shape of a cookie bar. A fixture that does not look like the real thing
     tests the wrong thing. -->
<div id="panel"><header>{title}</header><div id="greeting"></div>
<footer><input type="text" placeholder="Ihre Nachricht…" aria-label="Nachricht"></footer></div>
<script>
 document.getElementById('launch').addEventListener('click', () => {{
   document.getElementById('greeting').textContent = {greeting!r};
   document.getElementById('panel').classList.add('on');
 }});
</script>
</body></html>
"""

FIXTURES = {
    # Disclosure on the launcher itself — the westwing.de shape. Must pass
    # without the widget ever being opened.
    "launcher-discloses.html": dict(
        title="Haushalt24 — Startseite",
        launcher="Chat mit unserem KI-Assistenten",
        greeting="Hallo! Wie kann ich helfen?",
        expect_unauth="disclosed", expect_auth="disclosed",
    ),
    # Nothing on the launcher, disclosure in the greeting. This is the case that
    # makes not_determinable necessary: unauthorised we must NOT call it a
    # failure, authorised we can prove it is fine.
    "greeting-discloses.html": dict(
        title="Möbelwelt — Startseite",
        launcher="Chat",
        greeting="Guten Tag, ich bin ein automatisierter Assistent. "
                 "Wie kann ich Ihnen helfen?",
        expect_unauth="not_determinable", expect_auth="disclosed",
    ),
    # The real violation. Silent launcher, greeting that says nothing about AI.
    "silent.html": dict(
        title="Technikshop — Startseite",
        launcher="Chat",
        greeting="Guten Tag! Wie können wir Ihnen weiterhelfen?",
        expect_unauth="not_determinable", expect_auth="not_disclosed",
    ),
    # Worse than silent: the bot claims to be a named colleague. Must be
    # not_disclosed AND must flag the impersonation.
    "impersonates.html": dict(
        title="Elektro Meier — Startseite",
        launcher="Chat",
        greeting="Hallo, ich bin Lisa vom Kundenservice. Mein Name ist Lisa und "
                 "ich betreue Sie persönlich für Sie heute.",
        expect_unauth="not_determinable", expect_auth="not_disclosed",
        expect_impersonation=True,
    ),
    # No widget at all. Must not be reported as a failure.
    "no-widget.html": dict(
        title="Bäckerei Klein — Startseite", launcher=None, greeting=None,
        expect_unauth="no_widget_found", expect_auth="no_widget_found",
    ),
}


def write_fixtures() -> None:
    WWW.mkdir(exist_ok=True)
    for name, spec in FIXTURES.items():
        if spec["launcher"] is None:
            html = ("<!doctype html><html lang=de><head><meta charset=utf-8>"
                    f"<title>{spec['title']}</title></head><body style='min-height:200vh'>"
                    f"<h1>{spec['title']}</h1><p>Frisches Brot seit 1954. "
                    "Unser Team freut sich auf Sie.</p>"
                    "<footer><a href='/impressum'>Impressum</a></footer></body></html>")
        else:
            html = PAGE.format(title=spec["title"], launcher=spec["launcher"],
                               greeting=spec["greeting"])
        (WWW / name).write_text(html, encoding="utf-8")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(WWW), **kw)

    def log_message(self, *a):
        pass


def serve() -> socketserver.TCPServer:
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", PORT), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


async def main() -> int:
    write_fixtures()
    srv = serve()
    failures = 0
    try:
        for name, spec in FIXTURES.items():
            url = f"http://127.0.0.1:{PORT}/{name}"
            for authorized in (False, True):
                want = spec["expect_auth" if authorized else "expect_unauth"]
                rep = await check(url, authorized=authorized)
                ok = rep.verdict == want
                mode = "authorized  " if authorized else "unauthorized"
                print(f"{'PASS' if ok else 'FAIL'}  {name:26} {mode}  "
                      f"got={rep.verdict:18} want={want}")
                if not ok:
                    failures += 1
                    print(f"        reason: {rep.reason}")
                    print(f"        launcher: {rep.launcher_label[:110]}")
                    print(f"        greeting: {rep.first_message[:110]!r}")
                if ok and rep.evidence:
                    print(f"        evidence: {rep.evidence[:100]!r}")
                if authorized and spec.get("expect_impersonation"):
                    if rep.impersonation:
                        print(f"        impersonation flagged: {rep.impersonation!r}")
                    else:
                        failures += 1
                        print("        FAIL: impersonation was not flagged")
    finally:
        srv.shutdown()

    print("\n" + ("all fixtures behave as specified" if not failures
                  else f"{failures} fixture expectation(s) not met"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
