"""
Place one call, record what the line says, judge it. The Twilio transport for
tools/voice50/engine.py.

    venv/bin/python tools/voice50/twilio_call.py

Still nothing in the shipped product is touched. This reads credentials from
.env and talks to Twilio's REST API with urllib — no SDK, no new dependency in
requirements.txt.

WHY RECORDING RATHER THAN MEDIA STREAMS

    The production design is Media Streams: audio arrives over a WebSocket, is
    transcribed in flight, and is never stored. That is better legally — nothing
    to keep, nothing to leak — and it is what the product should ship.

    It also needs a WebSocket that Twilio can reach from the public internet.
    localhost is invisible to Twilio, so it needs the deployed server or a
    tunnel, and that is infrastructure standing between us and knowing whether
    the idea works at all.

    Twilio's own call recording needs none of it: Record=true, then fetch the
    .wav over the API. The engine already judges recordings, so the PoC is one
    HTTP call away instead of one deployment away.

THE CONSENT GUARD

    Recording a non-public spoken word without the consent of the person
    speaking is a criminal offence in Germany (§ 201 StGB, up to three years).
    This script therefore refuses to dial ANY number except the one named in
    VOICE50_CONSENTED_TO, so it cannot be aimed at a stranger by editing an
    argument or fat-fingering a digit.

    It is the same shape as `allow_private=False` on the web checker: the
    dangerous thing is not reachable by accident, only by deliberately writing
    consent down first.
"""

from __future__ import annotations

import base64
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from dotenv import load_dotenv                       # noqa: E402
from tools.voice50.engine import check_audio         # noqa: E402

load_dotenv(_REPO / ".env")

API = "https://api.twilio.com/2010-04-01"

# The line under test. Deliberately non-compliant: it gives a human name, claims
# to be looking after you personally, and never says it is a machine — the voice
# twin of Bogdan's workshop bot, which is the one our web engine catches.
#
# Polly.Vicki is a German voice. <Pause> at the front matters: a call recording
# starts the instant the leg is answered, and without it the first syllable is
# clipped and whisper guesses at the rest.
TARGET_TWIML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Response>'
    '<Pause length="1"/>'
    '<Say language="de-DE" voice="Polly.Vicki">'
    'Guten Tag, hier ist Lisa vom Kundenservice. Mein Name ist Lisa und ich '
    'betreue Sie heute persönlich. Wie kann ich Ihnen helfen?'
    '</Say>'
    '<Pause length="2"/>'
    '</Response>'
)


def _auth_header(sid: str, token: str) -> str:
    return "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode()


def _post(path: str, data: dict, sid: str, token: str) -> dict:
    import json
    req = urllib.request.Request(
        f"{API}/Accounts/{sid}{path}",
        data=urllib.parse.urlencode(data).encode(),
        method="POST",
        headers={"Authorization": _auth_header(sid, token),
                 "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read())


def _get(path: str, sid: str, token: str) -> dict:
    import json
    req = urllib.request.Request(
        f"{API}/Accounts/{sid}{path}",
        headers={"Authorization": _auth_header(sid, token)})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read())


def _download(url: str, sid: str, token: str, dest: Path) -> Path:
    req = urllib.request.Request(
        url, headers={"Authorization": _auth_header(sid, token)})
    with urllib.request.urlopen(req, timeout=90) as r:
        dest.write_bytes(r.read())
    return dest


def main() -> int:
    sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    frm = os.getenv("TWILIO_NUMBER", "").strip()
    to = os.getenv("VOICE50_CONSENTED_TO", "").strip()

    missing = [n for n, v in (("TWILIO_ACCOUNT_SID", sid),
                              ("TWILIO_AUTH_TOKEN", token),
                              ("TWILIO_NUMBER", frm),
                              ("VOICE50_CONSENTED_TO", to)) if not v]
    if missing:
        print("missing in .env: " + ", ".join(missing))
        print()
        print("VOICE50_CONSENTED_TO is the ONLY number this script will dial.")
        print("Put your own verified mobile there and nothing else — see the")
        print("consent guard in this file's docstring.")
        return 2

    out = Path(os.getenv("VOICE50_OUT", "/tmp")) / "voice50-call.wav"

    # TWO WAYS TO PUT THE BOT ON THE LINE, AND THE TRIAL ONLY MIGHT ALLOW ONE.
    #
    # `Twiml` carries the greeting inline and is refused outright on a trial
    # account. `Url` points at a TwiML Bin — Twilio-hosted, no web server — and
    # whether a trial permits a CUSTOM url or only Twilio's four templates is
    # not stated anywhere we could find. So it is a setting, not a guess: set
    # VOICE50_TWIML_URL and this uses it.
    #
    # VOICE50_RECORD is separate for the same reason. `Record` is one of the
    # parameters a trial blocks, and blocking it does not tell us whether `Url`
    # is also blocked. One variable each, so a failure names its own cause.
    twiml_url = os.getenv("VOICE50_TWIML_URL", "").strip()
    want_record = os.getenv("VOICE50_RECORD", "true").strip().lower() == "true"

    # NOTHING EXTRA GOES IN THIS REQUEST BY DEFAULT.
    #
    # `Timeout` was hardcoded here, and it is not on the trial's allowlist
    # either — so the first "Url is refused" result proved nothing: two
    # candidate causes, one error message. Anything beyond To/From/the greeting
    # is now opt-in, so a refusal has exactly one possible cause.
    body_params = {"To": to, "From": frm}
    if os.getenv("VOICE50_TIMEOUT", "").strip():
        body_params["Timeout"] = os.getenv("VOICE50_TIMEOUT").strip()
    if twiml_url:
        body_params["Url"] = twiml_url
        how = f"TwiML Bin {twiml_url.rsplit('/', 1)[-1]}"
    else:
        body_params["Twiml"] = TARGET_TWIML
        how = "inline Twiml (blocked on trial accounts)"
    if want_record:
        body_params["Record"] = "true"

    print(f"  dialling      {to}   from {frm}")
    print(f"  bot           {how}")
    print(f"  recording     {'yes — consent is yours, recorded in .env' if want_record else 'NO (VOICE50_RECORD=false)'}")
    try:
        call = _post("/Calls.json", body_params, sid, token)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:400]
        except Exception:
            pass
        print(f"  Twilio refused the call: HTTP {e.code}")
        print(f"  {body}")
        print()
        # MEASURED 19.08.2026, so nobody has to rediscover it.
        #
        # A trial account authenticates fine, has a German number, and can reach
        # a verified German mobile — and still refuses this call, because it
        # allows only To, From, a Url from four fixed Twilio templates, and
        # StatusCallback. Both parameters this script needs are blocked:
        # `Twiml` (our own greeting) and `Record` (the thing we judge).
        #
        # So the trial cannot run this PoC at all, whatever the numbers say.
        if "limited parameter access" in body or "disallowed parameters" in body:
            print("  This is the trial's parameter allowlist, not your numbers.")
            print("  A trial permits only To, From, a Url from four Twilio")
            print("  templates, and StatusCallback — while this call needs Twiml")
            print("  (our own greeting) and Record (the thing we judge).")
            print()
            print("  Two ways on:")
            print("    - upgrade to Pay as you go. The free units survive the")
            print("      upgrade, so the call itself still costs nothing.")
            print("    - or go inbound: point the number's 'A call comes in' at a")
            print("      TwiML Bin holding the greeting plus <Record>, and dial it")
            print("      yourself. Number configuration is not an API parameter,")
            print("      so the allowlist does not apply.")
        elif "unverified" in body or "not verified" in body:
            print("  The trial reaches verified numbers only, in your own country.")
        print()
        print("  Either way the file-based demo needs none of this and is")
        print("  measured 8/8: venv/bin/python tools/voice50/test_fixtures.py")
        return 1

    call_sid = call["sid"]
    print(f"  call          {call_sid}  status={call['status']}")
    print("  answer it and stay SILENT — the bot is the thing under test, not you")

    # RECORD FROM THE SIDE, BECAUSE THE FRONT DOOR IS SHUT.
    #
    # `Record=true` on call creation is one of the parameters a trial refuses.
    # TwiML's <Record> is not a substitute: it records the CALLER, and the caller
    # here is a person who is supposed to stay silent — the thing under test is
    # the line's own greeting.
    #
    # Recordings are also their own REST resource, created against a call that is
    # already in progress, and that is a different endpoint with a different
    # allowlist. So: place the call, wait for it to be answered, then ask for a
    # recording. The 5-second <Pause> at the top of the TwiML exists for exactly
    # this window — the greeting must not start before we are listening.
    #
    # If this endpoint is refused too, the trial simply cannot capture audio and
    # the answer is Pay as you go. Either way the run says which.
    if not want_record:
        started = None
        for _ in range(20):
            time.sleep(1)
            st = _get(f"/Calls/{call_sid}.json", sid, token)
            if st.get("status") == "in-progress":
                try:
                    started = _post(f"/Calls/{call_sid}/Recordings.json", {}, sid, token)
                    print(f"  recording     started mid-call: {started['sid']}")
                except urllib.error.HTTPError as e:
                    detail = ""
                    try:
                        detail = e.read().decode()[:300]
                    except Exception:
                        pass
                    print(f"  recording     REFUSED mid-call too: HTTP {e.code}")
                    print(f"                {detail}")
                    print()
                    print("  So this account cannot capture call audio at all:")
                    print("  Record on creation is blocked, and so is the")
                    print("  Recordings resource. Pay as you go is the only way")
                    print("  to a real recording; the file-based demo needs none.")
                    return 1
                break
            if st.get("status") in ("failed", "busy", "no-answer", "canceled"):
                print(f"  call ended: {st['status']} — answer it next time")
                return 1
        if not started:
            print("  the call was never answered, so nothing was recorded")
            return 1

    # Poll for the recording. It appears only after the leg completes, and a
    # fixed sleep here would be the same mistake the web engine made twice.
    rec = None
    for _ in range(40):
        time.sleep(3)
        st = _get(f"/Calls/{call_sid}.json", sid, token)
        recs = _get(f"/Calls/{call_sid}/Recordings.json", sid, token)
        if recs.get("recordings"):
            rec = recs["recordings"][0]
            if int(rec.get("duration") or 0) > 0:
                break
        if st.get("status") in ("failed", "busy", "no-answer", "canceled"):
            print(f"  call ended: {st['status']} — nothing recorded")
            return 1

    if not rec:
        print("  no recording appeared within two minutes")
        return 1

    print(f"  recording     {rec['sid']}  {rec.get('duration')}s")
    _download(f"https://api.twilio.com{rec['uri'].replace('.json', '.wav')}",
              sid, token, out)
    print(f"  saved         {out}")

    print()
    report = check_audio(out, authorized=True)
    print(f"  VERDICT       {report.verdict.upper()}")
    print(f"  reason        {report.reason}")
    print(f"  heard [{report.language}]  {report.transcript[:150]!r}")
    if report.impersonation:
        print(f"  impersonation {report.impersonation!r}")
    for n in report.notes:
        print(f"  note          {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
