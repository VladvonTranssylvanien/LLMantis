"""
Central configuration.

Every setting the app needs lives here. No other module reads os.environ
directly - they import from this file. That way there is exactly one place
to look when something needs changing.
"""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

# ROOT is the project folder (the one containing backend/, attacks/, frontend/).
# __file__ is this file, .parent is backend/, .parent.parent is the project root.
ROOT = Path(__file__).resolve().parent.parent

# Reads .env and puts its values into the environment.
load_dotenv(ROOT / ".env")


# --- Which LLM we talk to ------------------------------------------------
# "mistral" is the only value llm.py currently registers. Needs MISTRAL_API_KEY.
# That is what is wired up today, not a constraint: there is no vendor
# restriction on this project any more (PLAYBOOK.md §1, withdrawn 18.08).
#
# "mock" was removed from _PROVIDERS during the Mistral migration but stayed
# the default here, so a scan run by anyone following SETUP.md returned
# 21 errors out of 21 and no grade - under HTTP 200, which is why neither a
# status code nor a grep showed it.
PROVIDER = os.getenv("PROVIDER", "mistral").lower()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")



# The model that judges whether an answer was a security failure.
# It processes customer system prompts, which are trade secrets -- that governs
# retention and who may read them, and no longer restricts which vendor runs it.
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "mistral-small")


# --- Scan behaviour ------------------------------------------------------
# How many attacks run at the same time.
#
# Was 5, described as "safe" — but it never actually ran 5 at once. llm.py
# called Mistral's *synchronous* client from inside an async function, which
# blocks the event loop, so the semaphore let 5 tasks in and they queued up
# behind each other anyway. Switching to complete_async made the concurrency
# real for the first time, and 5 immediately exceeded our Mistral tier:
# three back-to-back 21-attack scans produced enough 429s to exhaust the
# retries and suppress a grade entirely.
#
# Measured against the lab, three consecutive scans each time:
#     5 -> 12s per scan, but 429s and a scan with no grade
#     3 -> ~15s per scan, zero rate-limit errors
#     2 -> ~23s per scan, zero rate-limit errors
# 3 is the point where it stops costing anything. Raise it only after
# checking what the Mistral plan actually allows.
CONCURRENCY = int(os.getenv("CONCURRENCY", "3"))

# Caps on response length, so one runaway answer cannot cost us 10 EUR.
MAX_TOKENS_TARGET = 600
MAX_TOKENS_JUDGE = 400


# --- Where things live ---------------------------------------------------
ATTACKS_DIR = ROOT / "attacks"
DEMO_DIR = ROOT / "demo"
FRONTEND_DIR = ROOT / "frontend"


# --- Which attack library a scan runs ------------------------------------
# The file in attacks/ used when a scan request does not name one.
#
# attacks_short.yaml (21 attacks, v1.4) is the default rather than
# attacks.yaml (78, v2.0), and that is a measured decision, not caution —
# PITCH-PLAN.md §5 has the numbers:
#
#   * 21 attacks take ~21 s. 78 take ~96 s, and the pace degrades as Mistral
#     backoff engages (20 in 13 s, 40 in 29 s, 60 in 86 s).
#   * The free Mistral tier allows 50 requests/minute. A 21-attack scan costs
#     ~34; a 78-attack scan needs ~121 and cannot complete inside one window,
#     which is how the same bot came back ungraded / C / A on three identical
#     runs (technical debt #12).
#   * The 78-attack set makes a leaking bot score BETTER — same bot, same
#     prompt, D/52 on 21 attacks becomes C/80 on 78, because attacks it
#     passes dilute the result (technical debt #15, undecided).
#
# Until #15 is decided, the short library is the one whose grades we can
# defend. Set ATTACK_LIBRARY=attacks.yaml to run the full corpus, or pass
# "library" in the scan request per call.
DEFAULT_ATTACK_LIBRARY = os.getenv("ATTACK_LIBRARY", "attacks_short.yaml")


def available_libraries() -> list[str]:
    """
    Every attack library the caller is allowed to ask for, by bare filename.

    This is also the whitelist that makes a caller-supplied library name safe:
    a name is only accepted if it appears in this list, so no request can walk
    out of attacks/ with "../../etc/passwd" or an absolute path. Derived from
    the directory rather than hardcoded, so adding a corpus needs no code.
    """
    if not ATTACKS_DIR.is_dir():
        return []
    return sorted(p.name for p in ATTACKS_DIR.glob("*.yaml") if p.is_file())


# --- Database ----------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://llmantis:llmantis_dev_password@localhost:5432/llmantis")


# --- Auth ------------------------------------------------------------------
# Signs login tokens (JWT). MUST be set explicitly outside dev — if it isn't,
# we generate a random one on every startup so the app still runs, but that
# also means every token becomes invalid (everyone logged out) on restart.
# That's a deliberately annoying default: it forces a real secret before this
# is ever mistaken for production-ready auth.
#
# MULTI-WORKER WARNING: this file runs once per process. With no JWT_SECRET
# set and more than one uvicorn worker (`--workers N`), each worker generates
# its OWN random secret independently — a token issued by worker A then
# fails to validate on worker B, so logins appear to randomly fail depending
# on which worker handles the request. This is exactly the "log in, get
# logged out again for no reason" bug a multi-worker deploy would hit if
# JWT_SECRET is still unset by then. Always set a real JWT_SECRET before
# running more than one worker, for correctness as much as for security.
JWT_SECRET = os.getenv("JWT_SECRET", "")
if not JWT_SECRET:
    JWT_SECRET = secrets.token_hex(32)
    print(
        "WARNING: JWT_SECRET not set in .env - using a random one-time secret. "
        "Every login token will stop working on the next restart, and with "
        "more than one uvicorn worker, logins will randomly fail depending on "
        "which worker handles the request. Set JWT_SECRET in .env before "
        "anything but single-worker local dev."
    )

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


# --- Scan targets on the local network ---------------------------------------
# An api-mode scan POSTs attacks to a URL the caller supplies. Normally that
# URL must be a public domain whose ownership they have proven by DNS TXT
# (PLAYBOOK §5). A loopback or private-network target cannot clear that bar:
# there is no DNS record to publish for 127.0.0.1, and no way to "own" it.
#
# That blocks the lab in lab/runner.py, which is the only way to exercise
# api mode end to end before a paying customer exists. So this flag exists to
# let a private target skip *ownership verification only* — login and org
# membership are still required, and the target is still recorded against
# that org.
#
# It defaults to OFF because turning it on is exactly an SSRF hole on a
# deployed instance: a logged-in user could aim a scan at the cloud metadata
# endpoint or anything else inside our own network. Turn it on for local
# development, never on a shared or public host.
ALLOW_PRIVATE_SCAN_TARGETS = os.getenv("ALLOW_PRIVATE_SCAN_TARGETS", "").lower() in ("1", "true", "yes")


def summary() -> str:
    """Human-readable config dump, used by selfcheck and on server startup."""
    if PROVIDER == "mistral":
        key_state = "set" if MISTRAL_API_KEY else "not set"
        key_label = "mistral_key"
    else:
        key_state = "n/a"
        key_label = "api_key"

    return (
        f"provider={PROVIDER}  "
        f"judge={JUDGE_MODEL}  "
        f"concurrency={CONCURRENCY}  "
        f"library={DEFAULT_ATTACK_LIBRARY}  "
        f"{key_label}={key_state}"
    )
