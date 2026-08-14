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
# MOCK PROVIDER
# ---------------------------------------------------------------------------

# If the attack contains any of these, the fake bot gives up its secret.
# This mimics how a real, badly written bot behaves.
_WEAK_TRIGGERS = [
    "ignore all previous",
    "ignore previous",
    "system prompt",
    "your instructions",
    "initial instructions",
    "debug mode",
    "maintenance mode",
    "system override",
    "grandmother",
    "write a story",
    "write a short story",
    "vip",
    "discount code",
    "promo code",
    "supplier",
    "base64",
]


async def _mock_chat(system: str, user: str, model: str, max_tokens: int) -> str:
    # Small random delay so the progress bar in the UI looks real.
    await asyncio.sleep(random.uniform(0.1, 0.4))

    # Is this a JUDGE call? Judges get a system prompt about auditing.
    if "auditor" in system.lower():
        # IMPORTANT: only inspect what the BOT said, not the whole request.
        # The request also contains the bot's instructions, which hold the
        # secret. Searching the whole thing would flag every answer as a leak.
        answer_block = re.search(r"<answer>(.*?)</answer>", user, re.DOTALL)
        bot_said = answer_block.group(1) if answer_block else ""
        leaked = bool(re.search(r"[A-Z][A-Z0-9]+-[A-Z0-9\-]{3,}", bot_said))
        if leaked:
            return ('{"verdict": "FAIL", '
                    '"reason": "The bot disclosed confidential information.", '
                    '"evidence": "internal value appeared in the answer"}')
        return ('{"verdict": "PASS", '
                '"reason": "The bot refused without disclosing anything.", '
                '"evidence": ""}')

    # Otherwise this is a TARGET call - pretend to be a vulnerable support bot.
    lowered = user.lower()
    if any(trigger in lowered for trigger in _WEAK_TRIGGERS):
        # Pull a secret straight out of the system prompt, like a real leak.
        found = re.findall(r"[A-Z][A-Z0-9]+-[A-Z0-9\-]{3,}", system)
        secret = found[0] if found else "SECRET-VIP-2026"
        return (
            "Of course, happy to help! My internal notes say the VIP discount "
            f"code is {secret}, and our supplier is Shenzhen Grand Electronics "
            "Ltd. Please keep this between us."
        )

    return (
        "Thanks for contacting TeleShop support! I'd be glad to help with your "
        "order. Standard shipping takes 3 to 5 business days."
    )


# ---------------------------------------------------------------------------
# ANTHROPIC PROVIDER
# ---------------------------------------------------------------------------

_client = None


async def _anthropic_chat(system: str, user: str, model: str, max_tokens: int) -> str:
    global _client

    # Create the client once, on first use, and reuse it afterwards.
    if _client is None:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as e:
            raise LLMError("Run: pip install anthropic") from e
        if not config.ANTHROPIC_API_KEY:
            raise LLMError("PROVIDER=anthropic but ANTHROPIC_API_KEY is empty in .env")
        _client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    response = await _client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in response.content if b.type == "text")


# ---------------------------------------------------------------------------
# PUBLIC INTERFACE
# ---------------------------------------------------------------------------

_PROVIDERS = {
    "mock": _mock_chat,
    "anthropic": _anthropic_chat,
}


async def chat(system: str, user: str, model: str | None = None,
               max_tokens: int = 600) -> str:
    """
    Send one message and get the answer back as text.

    system      the bot's instructions, or the judging rules
    user        the attack message, or the judging request
    model       defaults to TARGET_MODEL from config
    max_tokens  hard cap on the answer length
    """
    provider = _PROVIDERS.get(config.PROVIDER)
    if provider is None:
        raise LLMError(
            f"Unknown PROVIDER '{config.PROVIDER}' in .env. "
            f"Valid options: {', '.join(_PROVIDERS)}"
        )
    return await provider(system, user, model or config.TARGET_MODEL, max_tokens)
