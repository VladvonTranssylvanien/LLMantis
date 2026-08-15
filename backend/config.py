"""
Central configuration.

Every setting the app needs lives here. No other module reads os.environ
directly - they import from this file. That way there is exactly one place
to look when something needs changing.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ROOT is the project folder (the one containing backend/, attacks/, frontend/).
# __file__ is this file, .parent is backend/, .parent.parent is the project root.
ROOT = Path(__file__).resolve().parent.parent

# Reads .env and puts its values into the environment.
load_dotenv(ROOT / ".env")


# --- Which LLM we talk to ------------------------------------------------
# "mock"      fake responses, no API key, no cost - use this while developing
# "anthropic" real Claude (US), needs ANTHROPIC_API_KEY
# "mistral"   real Mistral (France/EU), needs MISTRAL_API_KEY - PREFERRED for EU compliance
PROVIDER = os.getenv("PROVIDER", "mock").lower()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")

# The model that plays the role of the customer's bot when we attack it.
TARGET_MODEL = os.getenv("TARGET_MODEL", "claude-sonnet-4-5")

# The model that judges whether an answer was a security failure.
# IMPORTANT: This processes customer trade secrets. Must be EU-only (CLOUD Act compliance).
# Defaults to Mistral (France) for EU compliance. Can be overridden to test with Anthropic.
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


def summary() -> str:
    """Human-readable config dump, used by selfcheck and on server startup."""
    if PROVIDER == "anthropic":
        key_state = "set" if ANTHROPIC_API_KEY else "not set"
        key_label = "anthropic_key"
    elif PROVIDER == "mistral":
        key_state = "set" if MISTRAL_API_KEY else "not set"
        key_label = "mistral_key"
    else:
        key_state = "n/a"
        key_label = "api_key"

    return (
        f"provider={PROVIDER}  "
        f"target={TARGET_MODEL}  "
        f"judge={JUDGE_MODEL}  "
        f"concurrency={CONCURRENCY}  "
        f"{key_label}={key_state}"
    )
