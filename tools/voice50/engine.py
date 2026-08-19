"""
Art. 50 disclosure check for VOICE bots. Proof of concept.

Nothing in the shipped product is touched by this file. It lives in tools/ for
the same reason the web checker lived in tools/art50v2/ before it earned its
place in backend/: a second channel is a claim until it is measured, and a claim
does not belong in an app that has a deadline.

WHY THE PHONE IS THE EASIER CHANNEL, NOT THE HARDER ONE

    Everything expensive about the web check is FINDING the widget. Twelve
    probes, a geometric pass, a pass by label, an AI opener, consent banners,
    iframes, shadow DOM — and sixt.de still has a bot we cannot reach.

    On a phone line none of that exists. Dialling IS opening. The first
    utterance is the first thing that happens, and Art. 50(1) is about exactly
    that moment. The fragile half of the engine disappears.

WHAT IS REUSED, AND WHY IT IS IMPORTED RATHER THAN COPIED

    DISCLOSE, IMPERSONATION and first_match come from backend/art50engine.py by
    import. They are bilingual, argued over, and in production. A copy here
    would drift the first time Kwabena revises a term, and then two channels
    would disagree about the same law.

THE RULE THIS FILE INHERITS

    Do not accuse without evidence you reached the thing being judged. On the
    web that rule is "a message box, or no verdict" — it was learned from three
    false accusations, one of which quoted a cookie banner as a greeting.

    The phone has its own version of that trap, and it is IVR. "Für Vertrieb
    drücken Sie die 1" is a touch-tone menu from 1995. There is no AI system in
    it, so Art. 50 does not apply to it, and reporting it as "your AI failed to
    disclose" would accuse a company of breaking a law about software it does
    not run. See IVR_MENU.
"""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# Read-only borrow. This file adds to the project; it changes nothing in it.
from backend.art50engine import DISCLOSE, IMPERSONATION, first_match  # noqa: E402


# A MENU IS NOT AN ASSISTANT.
#
# Matched against the first utterance. If the line answers with a keypad menu,
# the honest verdict is that there is no AI system on it — not that an AI failed
# to identify itself. Kept narrow: "drücken Sie" and "press N" are the actual
# tells, and a real assistant offering "sagen Sie mir, wie ich helfen kann" must
# not trip them.
IVR_MENU = [
    r"drücken sie (die )?\b(eins|zwei|drei|vier|null|\d)\b",
    r"wählen sie (die )?\b(eins|zwei|drei|vier|null|\d)\b",
    r"\bpress\b\s+\b(one|two|three|four|zero|\d)\b",
    r"\bfor (sales|support|billing|english|german)\b.{0,20}\bpress\b",
    r"taste\s*\d",
]

VERDICTS = ("disclosed", "not_disclosed", "not_determinable", "no_ai_system")

# Below this many characters of speech there is nothing to judge. A line that
# says "Hallo?" and waits has not made a first statement in the sense Art. 50
# means, and guessing from two words is how the web engine once quoted a
# shopping cart.
MIN_SPEECH_CHARS = 25

# faster-whisper's own estimate that a segment is silence. Above this the
# segment is dropped: telephone audio carries hold music, line noise and
# hiss, and whisper will cheerfully transcribe all three into plausible words.
MAX_NO_SPEECH = 0.6


@dataclass
class Voice50Report:
    """Deliberately shaped like backend.art50engine.Art50Report.

    Same field names where the meaning is the same, so one report page can
    render either channel later without a translation layer. `transcript` is
    this channel's `first_message`; `evidence` is the quoted fragment, exactly
    as on the web.
    """
    source: str                          # the number dialled, or the wav path
    verdict: str = "not_determinable"
    reason: str = ""
    evidence: str = ""
    transcript: str = ""
    impersonation: str = ""
    language: str = ""
    speech_seconds: float = 0.0
    duration_s: float = 0.0
    authorized: bool = False
    segments: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "source": self.source, "verdict": self.verdict,
            "reason": self.reason, "evidence": self.evidence,
            "transcript": self.transcript, "impersonation": self.impersonation,
            "language": self.language, "speech_seconds": self.speech_seconds,
            "duration_s": self.duration_s, "authorized": self.authorized,
            "segments": self.segments, "notes": self.notes,
        }


_MODEL = None


def _model(size: str = "base"):
    """Loaded once, on first use.

    "base" is the smallest model that handles German telephone audio at 8 kHz
    without inventing words. It is a ~145 MB download on first run and then
    local: no key, no network, no per-minute cost, and a demo that cannot fail
    because someone else's API is having an afternoon.
    """
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel(size, device="cpu", compute_type="int8")
    return _MODEL


def transcribe(path: str | Path, *, language: str | None = None,
               size: str = "base") -> dict:
    """
    Audio file -> text, with the parts we are not confident about thrown away.

    `language=None` lets whisper decide, which is the right default: the market
    is German but a German company's line can answer in English, and the web
    engine learned that gating on a detected language is its own failure mode.
    """
    segs, info = _model(size).transcribe(
        str(path), language=language, vad_filter=True,
        beam_size=5, condition_on_previous_text=False)

    kept, dropped = [], 0
    for s in segs:
        if getattr(s, "no_speech_prob", 0.0) > MAX_NO_SPEECH:
            dropped += 1
            continue
        kept.append({"start": round(s.start, 2), "end": round(s.end, 2),
                     "text": s.text.strip()})

    return {
        "text": " ".join(k["text"] for k in kept).strip(),
        "segments": kept,
        "dropped": dropped,
        "language": getattr(info, "language", "") or "",
        "speech_seconds": round(kept[-1]["end"] - kept[0]["start"], 2) if kept else 0.0,
    }


def judge(text: str) -> tuple[str, str, str, str]:
    """
    Transcript -> (verdict, reason, evidence, impersonation).

    The order matters and is the whole argument of this function:

      1. Too little speech      -> not_determinable. Nothing to read.
      2. A keypad menu          -> no_ai_system. Art. 50 is about AI systems.
      3. Discloses              -> disclosed.
      4. Speech, no disclosure  -> not_disclosed. Only here do we accuse.
    """
    said = (text or "").strip()

    if len(said) < MIN_SPEECH_CHARS:
        return ("not_determinable",
                "The line was answered but said too little to judge — we do not "
                "read a verdict out of a few words. Nothing is claimed either "
                "way.", "", "")

    menu = first_match(IVR_MENU, said, context=45)
    if menu:
        return ("no_ai_system",
                "This line answers with a keypad menu, not an AI assistant. "
                "Art. 50(1) applies to AI systems that interact with people, so "
                "there is nothing here for it to require. If you also run a "
                "voice assistant behind this menu, it has to be checked "
                "separately.", menu, "")

    impersonation = first_match(IMPERSONATION, said, context=30)
    hit = first_match(DISCLOSE, said, context=60)
    if hit:
        return ("disclosed",
                "Your line states that the caller is speaking to an AI system, "
                "in its first utterance — which is when Art. 50(1) requires it.",
                hit, impersonation)

    reason = ("Your line greeted the caller and began the conversation without "
              "stating that it is an AI system, which is what Art. 50(1) "
              "requires at first interaction.")
    if impersonation:
        reason += (" It introduces itself as a named person, which is the "
                   "opposite of disclosure.")
    return ("not_disclosed", reason, said[:300], impersonation)


def check_audio(path: str | Path, *, authorized: bool = False,
                language: str | None = None, size: str = "base") -> Voice50Report:
    """
    One recording of a line answering -> one report.

    `authorized` is carried for the same reason the web report carries it, but
    it means something stricter here. Reading a public web page harms nobody, so
    the web check can run unauthorized and free. A phone call cannot: recording
    a non-public spoken word without consent is a criminal offence in Germany
    (§ 201 StGB, up to three years), and a call occupies a real service line
    that costs the operator money. So the voice product is authorized-only, and
    a report that says otherwise would be advertising something we must not do.
    """
    t0 = time.time()
    rep = Voice50Report(source=str(path), authorized=authorized)

    try:
        out = transcribe(path, language=language, size=size)
    except Exception as e:
        rep.reason = (f"The recording could not be transcribed "
                      f"({type(e).__name__}). Nothing is claimed about this "
                      f"line.")
        rep.duration_s = round(time.time() - t0, 1)
        return rep

    rep.transcript = out["text"]
    rep.segments = out["segments"]
    rep.language = out["language"]
    rep.speech_seconds = out["speech_seconds"]
    if out["dropped"]:
        rep.notes.append(
            f"{out['dropped']} segment(s) dropped as probable silence or line "
            f"noise rather than speech")

    if not rep.transcript:
        rep.verdict = "not_determinable"
        rep.reason = ("Nothing we could read as speech came back from this "
                      "line — no answer, silence, or hold music only. Nothing "
                      "is claimed either way.")
        rep.duration_s = round(time.time() - t0, 1)
        return rep

    (rep.verdict, rep.reason, rep.evidence,
     rep.impersonation) = judge(rep.transcript)
    rep.duration_s = round(time.time() - t0, 1)
    return rep
