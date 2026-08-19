"""
Loads and validates an attack library from attacks/.

WHY VALIDATE
    The attack file is edited by hand, often in a hurry. A typo in a category
    name or a duplicated id must blow up at startup with a clear message,
    not silently skew the score during a demo.

WHY MORE THAN ONE LIBRARY
    There are two corpora with different properties, and which one ran is
    part of what a grade means: attacks_short.yaml (21, v1.4) and
    attacks.yaml (78, v2.0). The demo needs the short one — see
    config.DEFAULT_ATTACK_LIBRARY for the measurements. This used to be done
    by renaming files on disk before a demo, which is a manual step in the
    most fragile four minutes of the pitch.
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
    # Which file this came from. Stamped on every report: two corpora with
    # different sizes produce different grades for the same bot (technical
    # debt #15), so a report that names only the version is ambiguous the
    # moment a version number is ever reused.
    name: str = ""

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


def _validate(raw: dict, filename: str = "attacks.yaml") -> None:
    """Raise a clear error on the first problem found, naming the file."""
    if not isinstance(raw, dict) or "attacks" not in raw:
        raise ValueError(f"{filename} is missing the top-level 'attacks:' key")

    declared_categories = set(raw.get("categories") or {})
    if not declared_categories:
        raise ValueError(f"{filename} is missing the top-level 'categories:' key")

    seen_ids = set()

    for index, a in enumerate(raw["attacks"], start=1):
        where = f"{filename} attack #{index} (id={a.get('id', 'MISSING')})"

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


class UnknownLibraryError(ValueError):
    """Raised when a caller asks for a library that is not in attacks/."""


def resolve_library_name(name: str | None) -> str:
    """
    Turn an optional, possibly caller-supplied name into a safe filename.

    None means "whatever the deployment is configured for". Anything else
    must appear verbatim in config.available_libraries(), which lists bare
    filenames found in attacks/ — so a path, a traversal or a typo is
    rejected here rather than reaching the filesystem.
    """
    if not name:
        return config.DEFAULT_ATTACK_LIBRARY

    allowed = config.available_libraries()
    if name not in allowed:
        raise UnknownLibraryError(
            f"Unknown attack library '{name}'. Available: {', '.join(allowed) or 'none'}"
        )
    return name


@lru_cache(maxsize=8)
def _load(name: str) -> Library:
    """
    Read one YAML file and return a validated Library.

    Cached per filename, so each corpus is parsed once rather than on every
    scan. Only ever called with a name that resolve_library_name() has
    already whitelisted.
    """
    path = config.ATTACKS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Attack library not found at {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    _validate(raw, name)

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
        version=raw.get("version", "1.0"),
        name=name,
    )


def load_library(name: str | None = None) -> Library:
    """
    The validated library for this scan.

    name  a filename in attacks/, or None for config.DEFAULT_ATTACK_LIBRARY.
    Raises UnknownLibraryError if the name is not one we ship.
    """
    return _load(resolve_library_name(name))


def reload_library(name: str | None = None) -> Library:
    """
    Clear the cache and re-read from disk, after editing a library by hand.

    Clears every cached corpus, not just the one asked for — the point of
    this call is that the files on disk changed, and there is no way to know
    which ones.
    """
    _load.cache_clear()
    return load_library(name)
