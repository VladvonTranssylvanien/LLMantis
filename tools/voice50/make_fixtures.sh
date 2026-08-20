#!/usr/bin/env bash
# Regenerate the five voice fixtures. Committed so the recordings can be rebuilt
# rather than trusted: anyone reviewing a verdict can see exactly what was said.
#
# macOS only (uses `say`). Deliberately not a downloaded corpus and deliberately
# not a recording of a real company's line — recording a non-public spoken word
# without consent is a criminal offence in Germany, § 201 StGB. Fixtures we
# synthesise ourselves have no such problem.
#
# 8 kHz mono PCM on purpose. That is what Twilio Media Streams delivers (μ-law
# 8 kHz), and a transcriber tested on clean 44 kHz audio tells you nothing about
# how it does on a phone line.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p fixtures
tmp="$(mktemp -t voice50).aiff"
trap 'rm -f "$tmp"' EXIT

gen() {  # gen <name> <voice> <text>
  say -v "$2" -o "$tmp" "$3"
  ffmpeg -y -loglevel error -i "$tmp" -ar 8000 -ac 1 -c:a pcm_s16le "fixtures/$1.wav"
  printf '  %s.wav\n' "$1"
}

gen discloses-de Anna \
  "Guten Tag. Sie sprechen mit dem digitalen Assistenten der Musterfirma. Ich bin ein KI-System und kein Mensch. Wie kann ich Ihnen helfen?"

gen silent-de Anna \
  "Guten Tag bei der Musterfirma. Wie kann ich Ihnen weiterhelfen?"

gen impersonates-de Anna \
  "Guten Tag, hier ist Lisa vom Kundenservice. Mein Name ist Lisa und ich betreue Sie heute persönlich."

gen discloses-en Samantha \
  "Hello, you are speaking with an automated assistant. I am an AI system, not a human. How can I help you today?"

gen silent-en Samantha \
  "Hello and welcome to Example Company. How may I help you today?"

# The two rails. These exist to prove the checker STAYS QUIET where it must, and
# they are fixtures rather than a paragraph because that is the only form of
# proof that survives the next change to the patterns.
#
# A keypad menu is not an AI system, so Art. 50 has nothing to require of it.
# Reporting one as "your AI failed to disclose" accuses a company over software
# it does not run — the phone's version of quoting a cookie banner as a greeting.
gen ivr-menu-de Anna \
  "Willkommen bei der Musterfirma. Für Vertrieb drücken Sie die eins, für Support drücken Sie die zwei."

gen ivr-menu-en Samantha \
  "Welcome to Example Company. For sales press one, for support press two."

# Two words are not a first statement. Nothing is claimed from them.
gen too-short-de Anna "Hallo?"

echo
echo "done — now: venv/bin/python tools/voice50/test_fixtures.py"
