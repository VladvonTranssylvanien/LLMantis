"""
Loads and validates the attack library from attacks/attacks.yaml.

WHY VALIDATE
    The attack file is edited by hand, often in a hurry. A typo in a category
    name or a duplicated id must blow up at startup with a clear message,
    not silently skew the score during a demo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

import yaml

from . import config

VALID_SEVERITIES = {"critical", "high", "medium", "low"}


@dataclass
class Attack:
    """One attack, loaded from YAML."""
    id: str
    category: str
    severity: str
    message: str
    fix: str
    fail_if: dict = field(default_factory=dict)
    judge_hint: str = ""


@dataclass
class Library:
    """The whole attack library plus its category metadata."""
    attacks: list[Attack]
    categories: dict
    version: str = "1.0"  # Library version, incremented when attacks are added

    def by_category(self, name: str) -> list[Attack]:
        return [a for a in self.attacks if a.category == name]

    def label(self, category: str) -> str:
        """Human-readable name, e.g. prompt_injection -> Prompt Injection"""
        return self.categories.get(category, {}).get("label", category)

    def counts_by_category(self) -> dict:
        out = {}
        for a in self.attacks:
            out[a.category] = out.get(a.category, 0) + 1
        return out


def _validate(raw: dict) -> None:
    """Raise a clear error on the first problem found."""
    if not isinstance(raw, dict) or "attacks" not in raw:
        raise ValueError("attacks.yaml is missing the top-level 'attacks:' key")

    declared_categories = set(raw.get("categories") or {})
    if not declared_categories:
        raise ValueError("attacks.yaml is missing the top-level 'categories:' key")

    seen_ids = set()

    for index, a in enumerate(raw["attacks"], start=1):
        where = f"attack #{index} (id={a.get('id', 'MISSING')})"

        for required in ("id", "category", "severity", "message", "fix"):
            if not a.get(required):
                raise ValueError(f"{where}: missing required field '{required}'")

        if a["id"] in seen_ids:
            raise ValueError(f"{where}: duplicate id '{a['id']}'")
        seen_ids.add(a["id"])

        if a["category"] not in declared_categories:
            raise ValueError(
                f"{where}: category '{a['category']}' is not declared under 'categories:'. "
                f"Valid: {sorted(declared_categories)}"
            )

        if a["severity"] not in VALID_SEVERITIES:
            raise ValueError(
                f"{where}: severity '{a['severity']}' is invalid. "
                f"Valid: {sorted(VALID_SEVERITIES)}"
            )


@lru_cache(maxsize=1)
def load_library() -> Library:
    """
    Read the YAML file and return a validated Library.

    Cached, so we parse the file once, not on every scan.
    """
    path = config.ATTACKS_DIR / "attacks.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Attack library not found at {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    _validate(raw)

    attacks = [
        Attack(
            id=a["id"],
            category=a["category"],
            severity=a["severity"],
            message=a["message"],
            fix=a["fix"],
            fail_if=a.get("fail_if") or {},
            judge_hint=a.get("judge_hint", ""),
        )
        for a in raw["attacks"]
    ]

    return Library(
        attacks=attacks,
        categories=raw["categories"],
        version=raw.get("version", "1.0")
    )


def reload_library() -> Library:
    """Clear the cache and re-read the file, after editing attacks.yaml."""
    load_library.cache_clear()
    return load_library()
