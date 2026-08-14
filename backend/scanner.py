"""
The scan engine. Runs every attack against a target and scores the result.

FLOW FOR ONE ATTACK
    1. send the attack message to the bot
    2. get the bot's answer
    3. judge it (deterministic first, then AI)
    4. record the result

All attacks run concurrently, capped by CONCURRENCY so we do not trip
rate limits. 21 attacks take about 8 seconds instead of 45.

TARGET MODES
    "prompt"  we hold a copy of the customer's instructions and attack a copy
              of their bot. Easy. But it tests a copy, not the live system.
    "api"     we POST attacks to the customer's own endpoint. Tests the real
              thing, including its data and its tools. This is the paid product.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field

import httpx

from . import config, scoring
from .attacks import Attack, load_library
from .judge import judge
from .llm import chat


@dataclass
class Target:
    """The bot we are attacking."""
    mode: str = "prompt"            # "prompt" or "api"
    system_prompt: str = ""         # used when mode == "prompt"
    api_url: str = ""               # used when mode == "api"
    api_headers: dict = field(default_factory=dict)
    canary: str | None = None       # planted secret, enables layer-1 detection


async def _ask_target(target: Target, message: str) -> str:
    """Send one attack to the bot and return its answer."""

    if target.mode == "prompt":
        return await chat(
            system=target.system_prompt,
            user=message,
            model=config.TARGET_MODEL,
            max_tokens=config.MAX_TOKENS_TARGET,
        )

    if target.mode == "api":
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                target.api_url,
                headers=target.api_headers,
                json={"message": message},
            )
            response.raise_for_status()
            data = response.json()
            # Accept several common response shapes so we work with more customers.
            for key in ("reply", "answer", "message", "response", "text", "output"):
                if isinstance(data.get(key), str):
                    return data[key]
            return str(data)

    raise ValueError(f"Unknown target mode: {target.mode}")


async def _run_one(attack: Attack, target: Target, limiter: asyncio.Semaphore) -> dict:
    """Run a single attack end to end. Never raises - errors become results."""

    async with limiter:
        started = time.time()
        base = {
            "attack_id": attack.id,
            "category": attack.category,
            "severity": attack.severity,
            "message": attack.message,
            "fix": attack.fix,
        }

        try:
            answer = await _ask_target(target, attack.message)
        except Exception as e:
            return {
                **base,
                "answer": "",
                "verdict": "ERROR",
                "reason": f"Could not reach the target: {e}",
                "evidence": "",
                "method": "none",
                "duration_ms": int((time.time() - started) * 1000),
            }

        try:
            verdict = await judge(attack, target.system_prompt, answer, target.canary)
        except Exception as e:
            verdict = {
                "verdict": "ERROR",
                "reason": f"Judge failed: {e}",
                "evidence": "",
                "method": "none",
            }

        return {
            **base,
            "answer": answer,
            **verdict,
            "duration_ms": int((time.time() - started) * 1000),
        }


async def run_scan(target: Target, categories: list[str] | None = None,
                   on_result=None) -> dict:
    """
    Run a full scan and return the report.

    categories  optional filter, e.g. ["data_leakage"] to run a subset
    on_result   optional async callback after each attack, for live progress
    """
    library = load_library()
    attacks = library.attacks
    if categories:
        attacks = [a for a in attacks if a.category in categories]

    if not attacks:
        raise ValueError("No attacks selected")

    scan_id = str(uuid.uuid4())[:8]
    started = time.time()
    limiter = asyncio.Semaphore(config.CONCURRENCY)

    results: list[dict] = []
    tasks = [asyncio.create_task(_run_one(a, target, limiter)) for a in attacks]

    # as_completed gives us each result the moment it finishes, so the UI
    # can show progress instead of freezing until everything is done.
    for finished in asyncio.as_completed(tasks):
        result = await finished
        results.append(result)
        if on_result:
            await on_result(result, len(results), len(attacks))

    # Sort for the report: failures first, worst severity first.
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    results.sort(key=lambda r: (
        0 if r["verdict"] == "FAIL" else 1,
        severity_rank.get(r["severity"], 9),
        r["attack_id"],
    ))

    return {
        "scan_id": scan_id,
        "duration_s": round(time.time() - started, 1),
        "target_mode": target.mode,
        "summary": scoring.compute(results),
        "results": results,
        "scoring_explanation": scoring.explain(),
    }
