# voice50 — Art. 50 disclosure check for voice bots

Proof of concept. **Nothing in the shipped product is modified by this
directory**, exactly as `tools/art50v2/` held the web checker before it earned
its place in `backend/`.

```bash
venv/bin/pip install faster-whisper      # wheels exist for Python 3.14
tools/voice50/make_fixtures.sh           # macOS: regenerate the recordings
venv/bin/python tools/voice50/test_fixtures.py
```

Measured on 19.08.2026: **8 of 8 fixtures behave as specified.**

## Why the phone is the easier channel

Everything expensive about the web check is *finding* the widget — twelve
probes, a geometric pass, a pass by label, an AI opener, consent banners,
iframes, shadow DOM. And `sixt.de` still has a bot we cannot reach.

On a phone line none of that exists. **Dialling is opening.** The first
utterance is the first thing that happens, and Art. 50(1) is about exactly that
moment. The fragile half of the engine disappears; the half that carries the
value — the verdict — is reused unchanged.

## What is reused, not rewritten

`DISCLOSE`, `IMPERSONATION` and `first_match` are **imported** from
`backend/art50engine.py`. They are bilingual, already argued over, and in
production. A copy here would drift the first time a term is revised, and then
two channels would disagree about the same law.

`Voice50Report` mirrors `Art50Report` field for field where the meaning is the
same, so one report page can render either channel later. `transcript` is this
channel's `first_message`; `evidence` is the quoted fragment, as on the web.

## The verdicts

| verdict | meaning |
| --- | --- |
| `disclosed` | the line states it is an AI system, in its first utterance |
| `not_disclosed` | it greeted and started the conversation saying nothing about AI |
| `not_determinable` | too little speech, silence, or hold music only |
| `no_ai_system` | a keypad menu answered — Art. 50 requires nothing of one |

`no_ai_system` is the phone's version of the rule the web engine learned from
three false accusations. `"Für Vertrieb drücken Sie die eins"` is a touch-tone
menu from 1995. Reporting it as *"your AI failed to disclose"* accuses a company
over software it does not run. Two fixtures hold that line, one per language.

`not_determinable` holds the other one: below 25 characters of speech there is
nothing to read, and a verdict guessed from two words is how the web engine once
quoted a shopping cart as a greeting.

## Why this channel cannot be free

The web check runs unauthorized because reading a public page harms nobody.

A phone call is not that. Recording a non-public spoken word without the
consent of the person speaking is a **criminal offence in Germany — § 201 StGB,
up to three years** — and it protects an employee's voice too, which matters
because a voice bot can transfer you to a human and you cannot know in advance
who answers. A call also occupies a real service line that costs the operator
money.

So the voice product is **authorized-only, B2B, with written consent from the
operator before the first call.** That is a narrower product than the free web
check, and the narrowing is not a limitation to apologise for — it is the
reason the report is safe to hand to a regulator.

The fixtures are synthesised locally for the same reason: no real company's
line is recorded anywhere in this directory.

## Transcription

`faster-whisper`, `base` model, on the CPU. ~145 MB once, then local: no key,
no network, no per-minute cost, and a demo that cannot fail because someone
else's API is having an afternoon.

Fixtures are **8 kHz mono PCM** on purpose — that is what Twilio Media Streams
delivers (μ-law 8 kHz). A transcriber measured on clean 44 kHz audio tells you
nothing about how it does on a phone line.

Two guards on what the transcript is allowed to contain:

- segments whose `no_speech_prob` exceeds 0.6 are dropped, because telephone
  audio carries hold music, line noise and hiss, and whisper will cheerfully
  transcribe all three into plausible German
- the count of dropped segments is reported in `notes`, so a reader can see the
  recording was partly unreadable rather than partly silent

## Not built yet: the Twilio transport

This PoC judges a **recording**. The product places a **call**. The missing
piece is transport only, and it is deliberately last:

```
Twilio calls.create()  ->  TwiML <Stream>  ->  our WebSocket  ->  μ-law 8 kHz
                                                              ->  engine.judge()
```

Notes gathered before writing any of it:

- Twilio must reach **our** WebSocket from the public internet. `localhost` is
  invisible to it — this needs the deployed server or a tunnel.
- The trial account gives 75 voice minutes, one number, 30 days, and can only
  reach verified numbers (max 5).
- Use a **US** number. German local numbers require proof of address and take
  days; for a PoC the country is irrelevant.
- Target the **bot we host ourselves**, so no third party is called and the
  consent above is our own. Twilio-to-Twilio keeps the call off the public
  network and costs nothing; if the trial account refuses that, Twilio calling a
  verified German mobile also costs nothing, because receiving is free in
  Germany.

Until that exists, the demo runs from a file — which is the version that cannot
fail in a room.

## What a trial account can and cannot do — measured 19.08.2026

`tools/voice50/twilio_call.py` was run against a real German trial account. Each
line below is a result, not a reading of the documentation, because the
documentation does not say most of it.

| tried | result |
| --- | --- |
| Auth Token as basic auth | works |
| German trial number → verified German mobile | **connects**, the phone rings |
| `Twiml` inline | refused, HTTP 400 "limited parameter access" |
| `Timeout` | refused, same error — and it was hardcoded, which is why the first "`Url` is refused" run proved nothing |
| `Url` = our own TwiML Bin | **accepted by the API, then never fetched.** The call connects and announces an application error |
| `Url` = one of Twilio's four templates | works, speaks, and ends by telling you to upgrade |
| `Record=true` on creation | refused, same allowlist |
| `Url` = our bin, as the **inbound** webhook (Try out Voice → Inbound → Custom) | same failure — the announcement says it could not reach the URL |
| Phone number config → "A call comes in" → TwiML Bin | the page offers an **Upgrade** button instead |
| `GET /Notifications.json`, Monitor `/v1/Alerts` | HTTP 401 — a trial cannot read its own error log over the API either |

So the conclusion is not "our TwiML is wrong". A trial account **accepts a custom
URL and then declines to retrieve it**, which presents as a broken bin and is
not one. Twilio's own templates play fine over the same call.

**A trial cannot host the bot under test, by any route we found** — three
independent ones: the API refuses the parameter, the API accepts a custom URL and
declines to fetch it, and number configuration is behind the paywall. The
transport needs Pay as you go, whose first payment is a $20 minimum, which is
where this stopped.

What the call DID prove, on the free account: the number dials, the leg connects,
a German trial number reaches a verified German mobile, and Twilio's own template
speaks on the line. Everything except our own words on it.

None of this touches the engine. The verdict half is measured 8/8 from files and
does not know or care where the audio came from.
