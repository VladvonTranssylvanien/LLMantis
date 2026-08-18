"""
The only place in the project that talks to an AI model.

Everything else calls chat() and gets text back. It does not know or care
which provider is behind it. Swap providers here, nowhere else.

There is no mock provider; _PROVIDERS below is the whole list. It holds
"mistral" and "azure", selected by PROVIDER in .env.

This module now serves the JUDGE only. The target is a real deployment reached
over HTTP by scanner.py and does not pass through here -- see the "model" mode
in scanner.py. Keeping mistral registered alongside azure is deliberate: the
recorded judge-agreement baseline (mean 94.3 %, range 26-30 of 30) was measured
on mistral-small, and deleting the provider would make that number
unreproducible.
"""

from __future__ import annotations

import asyncio
import random
import re

import httpx

from . import config


class LLMError(Exception):
    """Raised when we cannot reach the model or it is misconfigured."""


# ---------------------------------------------------------------------------
# MISTRAL PROVIDER (the only one registered today)
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
    Mistral AI provider.

    Registered because it is what the project was built against, not because a
    rule requires it -- the EU-only provider constraint was withdrawn on 18.08
    (PLAYBOOK.md §1). Adding a second provider means adding an entry to
    _PROVIDERS below; nothing else in the codebase needs to know.
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
# AZURE PROVIDER (any OpenAI-compatible chat-completions endpoint)
# ---------------------------------------------------------------------------


async def _azure_chat(system: str, user: str, model: str, max_tokens: int) -> str:
    """
    Azure AI Foundry, and anything else that speaks OpenAI chat completions.

    Deliberately raw httpx rather than an SDK: the same three lines then serve
    Azure OpenAI, Azure AI model inference and any OpenAI-compatible gateway,
    and the full url comes from config so we are not guessing a path format.
    """
    if not config.AZURE_URL or not config.AZURE_KEY:
        raise LLMError(
            "PROVIDER=azure but AZURE_URL or AZURE_KEY is empty in .env\n"
            "AZURE_URL is the full chat-completions url from the deployment page."
        )

    headers = {"Content-Type": "application/json"}
    if config.AZURE_AUTH == "bearer":
        headers["Authorization"] = f"Bearer {config.AZURE_KEY}"
    else:
        headers["api-key"] = config.AZURE_KEY

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=config.LLM_TIMEOUT_S) as client:
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = await client.post(config.AZURE_URL, headers=headers,
                                             json=payload)
            except httpx.RequestError as e:
                # A transport failure is retryable; the last one propagates.
                if attempt == RETRY_ATTEMPTS - 1:
                    raise LLMError(f"Azure request failed: {e}") from e
                last_error = e
                await asyncio.sleep(_retry_delay(attempt))
                continue

            if response.status_code in RETRY_STATUSES and attempt < RETRY_ATTEMPTS - 1:
                last_error = LLMError(f"Azure HTTP {response.status_code}")
                await asyncio.sleep(_retry_delay(attempt, response.headers))
                continue

            if response.status_code != 200:
                # Pass Azure's own message through. It distinguishes quota from
                # a wrong deployment name from a content-filter block, and
                # hiding it costs an hour of guessing.
                raise LLMError(
                    f"Azure HTTP {response.status_code}: {response.text[:400]}"
                )

            data = response.json()
            return (data["choices"][0]["message"].get("content") or "")

    raise LLMError(f"Azure unreachable after {RETRY_ATTEMPTS} attempts: {last_error}")


# ---------------------------------------------------------------------------
# PUBLIC INTERFACE
# ---------------------------------------------------------------------------

_PROVIDERS = {
    "mistral": _mistral_chat,
    "azure": _azure_chat,
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
