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
# "anthropic" real Claude, needs ANTHROPIC_API_KEY
PROVIDER = os.getenv("PROVIDER", "mock").lower()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# The model that plays the role of the customer's bot when we attack it.
TARGET_MODEL = os.getenv("TARGET_MODEL", "claude-sonnet-4-5")

# The model that judges whether an answer was a security failure.
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "claude-sonnet-4-5")


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
    key_state = "set" if ANTHROPIC_API_KEY else "not set"
    return (
        f"provider={PROVIDER}  "
        f"target={TARGET_MODEL}  "
        f"judge={JUDGE_MODEL}  "
        f"concurrency={CONCURRENCY}  "
        f"api_key={key_state}"
    )
