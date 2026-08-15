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

    response = _mistral_client.chat.complete(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


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
