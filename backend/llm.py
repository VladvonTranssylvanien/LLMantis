"""
The only place in the project that talks to an AI model.

Everything else calls chat() and gets text back. It does not know or care
which provider is behind it. Swap providers here, nowhere else.

MOCK MODE
    PROVIDER=mock returns canned answers instead of calling an API.
    The fake bot is deliberately LEAKY, so the scanner produces realistic
    failures. This lets the whole team build and test with no API key
    and no cost.
"""

from __future__ import annotations

import asyncio
import random
import re

from . import config


class LLMError(Exception):
    """Raised when we cannot reach the model or it is misconfigured."""


# ---------------------------------------------------------------------------
# MISTRAL PROVIDER (EU-COMPLIANT, ONLY PROVIDER)
# ---------------------------------------------------------------------------

_mistral_client = None

# Retry on rate limiting and transient server errors.
#
# WHY THIS EXISTS — measured, not theoretical.
# Running two 21-attack scans back to back against the lab, Mistral began
# answering 429 and 17 of 21 judge calls failed in a single scan. Every one
# became verdict ERROR, the error rate hit 86%, and the grade was suppressed
# entirely. The suppression is correct (PLAYBOOK §9, a failed check cannot be
# invisible) but the cause was ours: we fired judge calls with no backoff and
# gave up on the first refusal. On stage that is a scan that silently returns
# no grade right after the one before it worked.
#
# The limit is on TOKENS, not requests: 25 tiny requests fired at once all
# succeeded, while two 21-attack scans in a row did not. So backing off for a
# couple of seconds is useless — we have to wait for the budget to refill,
# which takes tens of seconds. Hence 5 attempts and delays of roughly
# 2/4/8/16 s rather than the 1/2/4 s a burst limit would need.
#
# A scan that takes a minute longer is worth far more than a scan that
# returns no grade, which is what the customer got before this existed.
RETRY_ATTEMPTS = 5
RETRY_STATUSES = {429, 500, 502, 503, 504}


def _retry_delay(attempt: int, headers=None) -> float:
    """
    Seconds to wait before the next attempt.

    Honours Retry-After when the API sends one — it knows better than our
    guess. Mistral did not send one in any 429 observed here, so the fallback
    is what actually runs: 2/4/8/16 s with jitter, so concurrent workers that
    all got 429 together do not retry in lockstep and rebuild the same spike.
    """
    if headers:
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), 60.0)
            except ValueError:
                pass
    return (2 ** (attempt + 1)) + random.uniform(0, 1.0)


async def _mistral_chat(system: str, user: str, model: str, max_tokens: int) -> str:
    """
    Mistral AI provider (France-based, EU-compliant).

    WHY MISTRAL?
        The judge processes customer system prompts (trade secrets).
        CLOUD Act (US) contradicts EU data protection. We use Mistral (France)
        to guarantee that customer data stays in the EU.
    """
    global _mistral_client

    # Create the client once, on first use, and reuse it afterwards.
    if _mistral_client is None:
        try:
            from mistralai.client import Mistral
        except ImportError as e:
            raise LLMError(
                "Run: pip install mistralai\n"
                "Then get API key from https://console.mistral.ai"
            ) from e
        if not config.MISTRAL_API_KEY:
            raise LLMError(
                "PROVIDER=mistral but MISTRAL_API_KEY is empty in .env\n"
                "Get key from: https://console.mistral.ai → API Keys → Generate New Key"
            )
        _mistral_client = Mistral(api_key=config.MISTRAL_API_KEY)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    last_error: Exception | None = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = await _mistral_client.chat.complete_async(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:  # SDK raises MistralError subclasses
            status = getattr(e, "status_code", None)
            if status not in RETRY_STATUSES or attempt == RETRY_ATTEMPTS - 1:
                raise
            last_error = e
            await asyncio.sleep(_retry_delay(attempt, getattr(e, "headers", None)))

    raise last_error  # unreachable: the loop either returns or raises


# ---------------------------------------------------------------------------
# PUBLIC INTERFACE
# ---------------------------------------------------------------------------

_PROVIDERS = {
    "mistral": _mistral_chat,
}


async def chat(system: str, user: str, model: str | None = None,
               max_tokens: int = 600) -> str:
    """
    Send one message and get the answer back as text.

    system      the bot's instructions, or the judging rules
    user        the attack message, or the judging request
    model       the model to use (required)
    max_tokens  hard cap on the answer length
    """
    if not model:
        raise LLMError("model parameter is required for chat()")
    provider = _PROVIDERS.get(config.PROVIDER)
    if provider is None:
        raise LLMError(
            f"Unknown PROVIDER '{config.PROVIDER}' in .env. "
            f"Valid options: {', '.join(_PROVIDERS)}"
        )
    return await provider(system, user, model, max_tokens)
