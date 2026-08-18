"""
Run the Art.-50 engine over one or more sites and write a report you can look at.

    python tools/art50v2/cli.py westwing.de vattenfall.de tchibo.de
    python tools/art50v2/cli.py --authorized 127.0.0.1:8765/silent.html
    python tools/art50v2/cli.py --open westwing.de          # also open the report

The point of the HTML is the screenshot next to the verdict. A verdict on its own
is a claim; a verdict beside a picture of the thing it describes is checkable by
a human in two seconds, which is exactly what the customer is paying for and
exactly how we catch the engine being wrong.

Screenshots are inlined as data: URIs so the file works from file:// with nothing
else beside it, and can be sent to a colleague as one attachment.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import html
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.art50v2.engine import check, Art50Report            # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "report.html"

BADGE = {
    "disclosed":        ("#15803d", "#dcfce7", "Discloses AI"),
    "not_disclosed":    ("#b91c1c", "#fee2e2", "No disclosure"),
    "not_determinable": ("#a16207", "#fef9c3", "Not determinable"),
    "no_widget_found":  ("#475569", "#f1f5f9", "No widget found"),
}

CSS = """
*{box-sizing:border-box}
body{font:15px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
 margin:0;padding:32px;background:#f8fafc;color:#0f172a}
.wrap{max-width:980px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px}
.sub{color:#64748b;font-size:13px;margin:0 0 28px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;margin-bottom:20px;
 overflow:hidden}
.head{display:flex;align-items:center;gap:12px;padding:16px 20px;border-bottom:1px solid #eef2f6;
 flex-wrap:wrap}
.host{font-weight:600;font-size:16px}
.badge{font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
 padding:4px 10px;border-radius:999px;white-space:nowrap}
.body{padding:16px 20px}
dl{display:grid;grid-template-columns:150px 1fr;gap:8px 16px;margin:0}
dt{color:#64748b;font-size:12.5px;text-transform:uppercase;letter-spacing:.04em}
dd{margin:0;min-width:0;overflow-wrap:anywhere}
.quote{background:#f8fafc;border-left:3px solid #cbd5e1;padding:10px 14px;margin:0;
 font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;white-space:pre-wrap}
.warn{color:#b91c1c;font-weight:600}
.shot{display:block;width:100%;border-top:1px solid #eef2f6}
.shot-wrap{max-height:520px;overflow:auto;background:#f1f5f9}
.none{color:#94a3b8}
.tally{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;
 margin-bottom:24px;display:flex;gap:28px;flex-wrap:wrap}
.tally div b{display:block;font-size:22px}
.tally div span{color:#64748b;font-size:12.5px}
.probes{margin-top:16px;border-top:1px solid #eef2f6;padding-top:12px}
.probes summary{cursor:pointer;color:#475569;font-size:13px;font-weight:600}
.probes table{width:100%;border-collapse:collapse;margin-top:12px;font-size:12.5px}
.probes th{text-align:left;color:#64748b;font-weight:600;padding:4px 8px;
 border-bottom:1px solid #e2e8f0;white-space:nowrap}
.probes td{padding:4px 8px;border-bottom:1px solid #f1f5f9;vertical-align:top}
.probes tr.hit td{background:#f0fdf4}
.probes tr.miss{color:#94a3b8}
.probes .conf{white-space:nowrap}
.probes .det{color:#64748b;overflow-wrap:anywhere}
"""


def esc(x) -> str:
    return html.escape(str(x or ""))


def shot_uri(rep: Art50Report) -> str:
    if not rep.screenshot:
        return ""
    p = HERE / "shots" / rep.screenshot
    if not p.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def card(rep: Art50Report) -> str:
    fg, bg, label = BADGE[rep.verdict]
    host = rep.url.split("//")[-1]
    rows = [("Verdict reason", esc(rep.reason))]

    if rep.evidence:
        rows.append(("Evidence", f'<pre class="quote">{esc(rep.evidence)}</pre>'))
    if rep.launcher_label:
        rows.append(("Launcher text", f'<pre class="quote">{esc(rep.launcher_label)}</pre>'))
    elif rep.launcher_technical:
        rows.append(("Launcher", '<span class="none">no human-readable label; '
                     f'identified by markup only: <code>{esc(rep.launcher_technical)}</code>'
                     "</span>"))
    if rep.first_message:
        rows.append(("Assistant's first message",
                     f'<pre class="quote">{esc(rep.first_message[:900])}</pre>'))
    if rep.impersonation:
        rows.append(("Presents as a person",
                     f'<span class="warn">{esc(rep.impersonation)}</span> — the opposite '
                     "of disclosure"))
    hits = [p for p in rep.probe_log if p["fired"] and p["name"] != "consent_gate"]
    rows += [
        ("Detected by", ", ".join(f"<code>{esc(p['name'])}</code>" for p in hits)
         or '<span class="none">nothing fired</span>'),
        ("robots.txt", esc(rep.robots) + (
            ' <span class="none">— recorded, not enforced</span>'
            if rep.robots != "DISALLOWS" else
            ' <span class="warn">— we proceeded anyway (team decision 17.08)</span>')),
        ("Form factor", esc(rep.viewport) or '<span class="none">—</span>'),
        ("Widget opened", "yes" if rep.opened_widget else
         ("no — not authorised for this domain" if rep.verdict == "not_determinable"
          else "no")),
        ("Pages checked", "<br>".join(
            f'{esc(p["url"])} <span class="none">[{esc(p.get("viewport",""))}]</span> '
            f'→ {esc(p["http"] or p["error"] or "?")}'
            for p in rep.pages_tried) or '<span class="none">—</span>'),
    ]

    dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)

    # The full probe log, hits and misses alike. This is the part that makes a
    # negative result defensible: "no widget found" is a shrug on its own and a
    # Nachweis der Sorgfalt when it comes with the eleven things that were tried.
    probe_rows = "".join(
        f'<tr class="{"hit" if p["fired"] else "miss"}">'
        f'<td>{"✓" if p["fired"] else "·"}</td>'
        f'<td><code>{esc(p["name"])}</code></td>'
        f'<td class="conf">{esc(p["confidence"])}</td>'
        f'<td>{esc(p["description"])}</td>'
        f'<td class="det">{esc((p["findings"][0] if p["findings"] else p["note"])[:150])}</td>'
        f"</tr>"
        for p in rep.probe_log)
    probes_html = (
        f'<details class="probes"><summary>All {len(rep.probe_log)} detection '
        f'methods were run · {len(hits)} found something — show every one</summary>'
        f'<table><thead><tr><th></th><th>Method</th><th>Confidence</th>'
        f'<th>What it looks for</th><th>Result</th></tr></thead>'
        f"<tbody>{probe_rows}</tbody></table></details>") if rep.probe_log else ""

    uri = shot_uri(rep)
    img = (f'<div class="shot-wrap"><img class="shot" alt="Screenshot of {esc(host)}" '
           f'src="{uri}"></div>') if uri else ""
    return (f'<div class="card"><div class="head"><span class="host">{esc(host)}</span>'
            f'<span class="badge" style="color:{fg};background:{bg}">{label}</span></div>'
            f'<div class="body"><dl>{dl}</dl>{probes_html}</div>{img}</div>')


def render(reps: list[Art50Report], authorized: bool) -> str:
    counts = {k: sum(1 for r in reps if r.verdict == k) for k in BADGE}
    tally = "".join(
        f"<div><b>{counts[k]}</b><span>{BADGE[k][2]}</span></div>" for k in BADGE)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sweep = ("exhaustive: every candidate page and both form factors"
             if any(r.exhaustive for r in reps) else
             "stops once a widget is found")
    mode = ((f"AUTHORISED — the launcher was clicked and the greeting read · {sweep}")
            if authorized else
            ("Passive — the launcher was read but never opened, so no result here "
             f"can be a missing-disclosure finding · {sweep}"))
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>Art. 50 check — {len(reps)} site(s)</title><style>{CSS}</style></head>"
            f"<body><div class=wrap><h1>Art. 50 disclosure check</h1>"
            f"<p class=sub>{len(reps)} site(s) · {stamp} · {esc(mode)}</p>"
            f"<div class=tally>{tally}</div>"
            + "".join(card(r) for r in reps)
            + "</div></body></html>")


async def main() -> int:
    ap = argparse.ArgumentParser(description="Art.-50 check with a viewable report")
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--authorized", action="store_true",
                    help="open the widget and read the greeting. Only legitimate for a "
                         "domain whose ownership the caller has proven.")
    ap.add_argument("--open", action="store_true", help="open the report when done")
    ap.add_argument("--exhaustive", action="store_true",
                    help="never stop early: every candidate page AND both form "
                         "factors, even after a widget is found. Slower, and the "
                         "right default for a paid report, because the value of a "
                         "negative result is the list of things that were tried.")
    args = ap.parse_args()

    reps: list[Art50Report] = []
    for u in args.urls:
        print(f"checking {u} ...", flush=True)
        r = await check(u, authorized=args.authorized,
                        exhaustive=args.exhaustive)
        print(f"  {r.verdict:18} {r.evidence[:70]!r}")
        reps.append(r)

    OUT.write_text(render(reps, args.authorized), encoding="utf-8")
    print(f"\nreport: {OUT}")
    if args.open:
        webbrowser.open(OUT.as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
