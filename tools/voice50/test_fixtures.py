"""
Five recordings, five expected verdicts. Run it before believing anything.

Modelled on tools/art50v2/test_fixtures.py, and for the same reason: a checker
whose only proof is "it worked on a site I tried" is a demo. These five are
generated locally by make_fixtures.sh, at 8 kHz mono — telephone quality, which
is what Twilio's Media Streams actually deliver, not studio audio that flatters
the transcriber.

    venv/bin/python tools/voice50/test_fixtures.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.voice50.engine import check_audio  # noqa: E402

FIX = Path(__file__).parent / "fixtures"

CASES = [
    # file,                  expected verdict,   what it is
    ("discloses-de.wav",     "disclosed",
     "German line that says it is a KI-System and not a human"),
    ("silent-de.wav",        "not_disclosed",
     "German line that greets and starts, saying nothing about AI"),
    ("impersonates-de.wav",  "not_disclosed",
     "German line introducing itself as 'Lisa vom Kundenservice'"),
    ("discloses-en.wav",     "disclosed",
     "English line stating it is an automated assistant"),
    ("silent-en.wav",        "not_disclosed",
     "English line that greets and starts, saying nothing about AI"),

    # The rails. Everything above proves the checker speaks when it should;
    # these prove it stays quiet when it must, which is the half that keeps a
    # compliance report from becoming a liability.
    ("ivr-menu-de.wav",      "no_ai_system",
     "German keypad menu — no AI system, so Art. 50 requires nothing of it"),
    ("ivr-menu-en.wav",      "no_ai_system",
     "English keypad menu — same, in the other lexicon"),
    ("too-short-de.wav",     "not_determinable",
     "A line that says 'Hallo?' and waits — not a first statement"),
]


def main() -> int:
    missing = [f for f, _, _ in CASES if not (FIX / f).exists()]
    if missing:
        print("fixtures missing — run tools/voice50/make_fixtures.sh first:")
        for m in missing:
            print("   ", m)
        return 2

    bad = 0
    for name, want, what in CASES:
        rep = check_audio(FIX / name, authorized=True)
        ok = rep.verdict == want
        bad += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {name:22} got={rep.verdict:18} "
              f"want={want}")
        print(f"        {what}")
        print(f"        heard [{rep.language}]: {rep.transcript[:96]!r}")
        if rep.evidence and rep.verdict == "disclosed":
            print(f"        evidence: {rep.evidence!r}")
        if rep.impersonation:
            print(f"        impersonation flagged: {rep.impersonation!r}")
        for n in rep.notes:
            print(f"        note: {n}")

    print()
    print("all fixtures behave as specified" if not bad
          else f"{bad} of {len(CASES)} wrong")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
