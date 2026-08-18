"""
The probes, re-exported from the module the website actually runs.

There were briefly two copies of this file — this one and backend/art50probes.py
— and every pattern fix had to be applied twice. That is the setup where a probe
gets tightened in one place, the CLI keeps reporting the old behaviour, and the
numbers in a README stop describing the product. backend/ is the single source of
truth; this file exists so the CLI's imports keep working.

The prototype CLI (engine.py, cli.py, test_fixtures.py in this directory) is
where a new detection idea gets tried before it goes near backend/. It reads the
same probes, so an experiment measures the real thing.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.art50probes import *          # noqa: F401,F403,E402
from backend.art50probes import (          # noqa: F401,E402  explicit for linters
    ARIA_ROLES, CHATTY_TEXT, CHAT_ENDPOINT, CONSENT, CONSENT_PRESENT,
    GENERIC_ASSET, IFRAME_ATTRS, NOT_CHAT, PAGE_TEXT, PROBE_NAMES, ProbeResult,
    VENDOR_ASSET, VENDOR_PLATFORM, WALK_FIXED, launchers_from, run_all, weak_only,
)
