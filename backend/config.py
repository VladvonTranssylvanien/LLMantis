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
# "mock"      fake responses, no API key, no cost - use this while developing
# "mistral"   real Mistral (France/EU), needs MISTRAL_API_KEY - REQUIRED for production
PROVIDER = os.getenv("PROVIDER", "mock").lower()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")



# The model that judges whether an answer was a security failure.
# CRITICAL: This processes customer trade secrets. Must be EU-only (CLOUD Act compliance).
# Mistral (France) is the only provider. No US models allowed.
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "mistral-small")


# --- Scan behaviour ------------------------------------------------------
# How many attacks run at the same time. Higher = faster scan, but you may
# hit the provider's rate limit. 5 is safe.
CONCURRENCY = int(os.getenv("CONCURRENCY", "5"))

# Caps on response length, so one runaway answer cannot cost us 10 EUR.
MAX_TOKENS_TARGET = 600
MAX_TOKENS_JUDGE = 400


# --- Where things live ---------------------------------------------------
ATTACKS_DIR = ROOT / "attacks"
DEMO_DIR = ROOT / "demo"
FRONTEND_DIR = ROOT / "frontend"


# --- Database ----------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://llmantis:llmantis_dev_password@localhost:5432/llmantis")


# --- Auth ------------------------------------------------------------------
# Signs login tokens (JWT). MUST be set explicitly outside dev — if it isn't,
# we generate a random one on every startup so the app still runs, but that
# also means every token becomes invalid (everyone logged out) on restart.
# That's a deliberately annoying default: it forces a real secret before this
# is ever mistaken for production-ready auth.
JWT_SECRET = os.getenv("JWT_SECRET", "")
if not JWT_SECRET:
    JWT_SECRET = secrets.token_hex(32)
    print(
        "WARNING: JWT_SECRET not set in .env - using a random one-time secret. "
        "Every login token will stop working on the next restart. "
        "Set JWT_SECRET in .env before anything but local dev."
    )

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


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
        f"{key_label}={key_state}"
    )
