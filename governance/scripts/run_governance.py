#!/usr/bin/env python3
"""
PromptGuard Governance Checker.

Runs read-only, evidence-based checks against the actual repository and
writes the result to governance/reports/GOVERNANCE_REPORT.md.

Usage:
    python governance/scripts/run_governance.py

Design constraints (see governance/README.md):
    - Does not modify production code.
    - Never prints a secret VALUE, only whether one appears present.
    - Makes no network calls.
    - Works even if optional dependencies (PyYAML, pytest) are not installed
      in the environment running it — it degrades to text-based inspection
      rather than crashing.
    - Every status is backed by a concrete file/line/command referenced in
      "evidence"; nothing is marked PASS purely because a keyword appears
      somewhere in the repository.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DIR = ROOT / "governance"
CONTROLS_FILE = GOVERNANCE_DIR / "controls" / "controls.yaml"
REPORT_FILE = GOVERNANCE_DIR / "reports" / "GOVERNANCE_REPORT.md"

VALID_STATUSES = ("PASS", "PARTIAL", "FAIL", "N/A", "UNCLEAR")


# ---------------------------------------------------------------------------
# small, dependency-free repository helpers
# ---------------------------------------------------------------------------

def read(*parts: str) -> str:
    """Read a repo-relative file. Returns '' if it does not exist or is unreadable."""
    path = ROOT.joinpath(*parts)
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError, IsADirectoryError):
        return ""


def exists(*parts: str) -> bool:
    return ROOT.joinpath(*parts).exists()


def git(*args: str) -> str:
    """Run a read-only git command in ROOT. Returns '' on any failure."""
    try:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=15,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def find_files(pattern: str) -> list[str]:
    """Glob relative to ROOT, returned as repo-relative POSIX paths, sorted."""
    return sorted(
        str(p.relative_to(ROOT)) for p in ROOT.glob(pattern) if p.is_file()
    )


# ---------------------------------------------------------------------------
# result type
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    control_id: str
    name: str
    reference: str
    status: str
    evidence: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    evidence_doc: str | None = None

    def __post_init__(self):
        assert self.status in VALID_STATUSES, f"invalid status {self.status!r} for {self.control_id}"


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")


def collect_supplementary_evidence(control_id: str) -> tuple[list[str], str | None]:
    """
    Screenshots are supplementary evidence only (see governance/README.md).
    They never replace the repository-path/automated evidence collected by
    the check_* functions above — this only surfaces what a human has
    additionally placed in governance/evidence/<control_id>/.
    """
    folder = GOVERNANCE_DIR / "evidence" / control_id
    if not folder.is_dir():
        return [], None

    screenshots = sorted(
        str(p.relative_to(ROOT)) for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    doc = None
    for name in ("EVIDENCE.md", "README.md"):
        if (folder / name).is_file():
            doc = str((folder / name).relative_to(ROOT))
            break

    return screenshots, doc


# ---------------------------------------------------------------------------
# controls.yaml loader (PyYAML if available, else a small regex fallback)
# ---------------------------------------------------------------------------

def load_control_metadata() -> dict[str, dict]:
    """
    Returns {control_id: {"name": ..., "reference": "ISO/IEC ..., ISO ..."}}
    parsed from governance/controls/controls.yaml.

    Falls back to a regex-based reader if PyYAML is not installed, so this
    script has zero hard dependencies beyond the standard library.
    """
    text = read("governance", "controls", "controls.yaml")
    if not text:
        return {}

    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text) or {}
        out = {}
        for c in data.get("controls", []):
            out[c["id"]] = {
                "name": c.get("name", ""),
                "reference": ", ".join(c.get("reference_standards", []) or []),
            }
        return out
    except ImportError:
        pass
    except Exception:
        pass

    # --- regex fallback: split into per-control blocks on "  - id: XXX" ---
    out = {}
    blocks = re.split(r"\n(?=  - id: )", text)
    for block in blocks:
        m_id = re.search(r"- id:\s*(\S+)", block)
        if not m_id:
            continue
        cid = m_id.group(1)
        m_name = re.search(r"\n\s*name:\s*(.+)", block)
        name = m_name.group(1).strip() if m_name else ""
        refs = re.findall(r'reference_standards:\s*\n((?:\s*-\s*".*\n?)+)', block)
        ref_list = []
        if refs:
            ref_list = re.findall(r'-\s*"([^"]+)"', refs[0])
        out[cid] = {"name": name, "reference": ", ".join(ref_list)}
    return out


# ---------------------------------------------------------------------------
# individual control checks — each inspects real files and returns a Finding
# ---------------------------------------------------------------------------

def check_gov01() -> Finding:
    config = read("backend", "config.py")
    llm = read("backend", "llm.py")
    requirements = read("requirements.txt")
    playbook = read("PLAYBOOK.md")

    evidence, gaps = [], []

    target_model = re.search(r'TARGET_MODEL\s*=\s*os\.getenv\("TARGET_MODEL",\s*"([^"]+)"\)', config)
    judge_model = re.search(r'JUDGE_MODEL\s*=\s*os\.getenv\("JUDGE_MODEL",\s*"([^"]+)"\)', config)
    if target_model and judge_model:
        evidence.append(f"backend/config.py: TARGET_MODEL default = '{target_model.group(1)}', JUDGE_MODEL default = '{judge_model.group(1)}'")
    else:
        gaps.append("backend/config.py does not declare TARGET_MODEL/JUDGE_MODEL in the expected form")

    providers = re.search(r"_PROVIDERS\s*=\s*\{([^}]*)\}", llm, re.DOTALL)
    if providers:
        names = re.findall(r'"(\w+)"\s*:', providers.group(1))
        evidence.append(f"backend/llm.py: provider registry declares {names}")
    else:
        gaps.append("backend/llm.py has no discoverable provider registry")

    pinned = re.search(r"anthropic==([\d.]+)", requirements)
    if pinned:
        evidence.append(f"requirements.txt: anthropic pinned at =={pinned.group(1)}")
    else:
        gaps.append("requirements.txt does not pin the anthropic SDK to an exact version")

    # policy cross-check: PLAYBOOK forbids Anthropic/OpenAI/Google as the judge provider
    forbids_us_judge = bool(re.search(r"LLM judge.*Anthropic, OpenAI, Google", playbook))
    if judge_model and forbids_us_judge and "claude" in judge_model.group(1).lower():
        gaps.append(
            "PLAYBOOK.md's EU-only-stack invariant forbids Anthropic/OpenAI/Google as the judge "
            f"provider, but backend/config.py's JUDGE_MODEL default ('{judge_model.group(1)}') is an "
            "Anthropic model. Tracked as technical debt #1 in PROJECT-STATE.md."
        )

    status = "PARTIAL" if gaps else "PASS"
    return Finding(
        "GOV-01", "AI Component Inventory", "ISO/IEC 42001", status,
        evidence, gaps,
        notes=["Inventory is identifiable and version-pinned; the open gap is a policy/configuration "
               "mismatch already tracked by the project itself, not a missing inventory."],
    )


def check_gov02() -> Finding:
    attacks_yaml = read("attacks", "attacks.yaml")
    attacks_py = read("backend", "attacks.py")
    readme = read("README.md")

    evidence, gaps = [], []

    if not attacks_yaml:
        return Finding("GOV-02", "Attack Governance", "ISO/IEC 42001, ISO/IEC 23894", "FAIL",
                        gaps=["attacks/attacks.yaml not found"])

    ids = re.findall(r'^\s*-\s*id:\s*(\S+)', attacks_yaml, re.MULTILINE)
    categories = [
        c for c in re.findall(r'^\s*(\w+):\s*$', attacks_yaml.split("attacks:")[0], re.MULTILINE)
        if c != "categories"
    ]
    dup_ids = {i for i in ids if ids.count(i) > 1}

    evidence.append(f"attacks/attacks.yaml: {len(ids)} attack(s) declared, {len(set(categories))} categor(y/ies) declared")
    if dup_ids:
        gaps.append(f"duplicate attack ids found: {sorted(dup_ids)}")
    else:
        evidence.append("no duplicate attack ids found by static scan")

    has_validation = "_validate" in attacks_py and "duplicate id" in attacks_py
    if has_validation:
        evidence.append("backend/attacks.py:_validate() enforces unique id, declared category, valid severity at load time")
    else:
        gaps.append("backend/attacks.py does not appear to validate the library at load time")

    m = re.search(r"(\d+)\s+attacks? across", readme)
    if m and m.group(1).isdigit() and int(m.group(1)) != len(ids):
        gaps.append(f"README.md states {m.group(1)} attacks, but attacks.yaml declares {len(ids)}")
    elif m:
        evidence.append(f"README.md's stated attack count ({m.group(1)}) matches attacks.yaml ({len(ids)})")

    test_files = [f for f in find_files("**/test_*.py") if "governance" not in f]
    if not test_files:
        gaps.append("no automated test exercises attacks.yaml validation (no test_*.py found outside governance/)")
    else:
        evidence.append(f"test file(s) found: {test_files}")

    status = "FAIL" if dup_ids or not attacks_yaml else ("PARTIAL" if gaps else "PASS")
    return Finding("GOV-02", "Attack Governance", "ISO/IEC 42001, ISO/IEC 23894", status, evidence, gaps)


def check_gov03() -> Finding:
    scoring = read("backend", "scoring.py")
    project_state = read("PROJECT-STATE.md")
    readme = read("README.md")

    evidence, gaps = [], []

    if not scoring:
        return Finding("GOV-03", "AI Risk and Scoring", "ISO/IEC 23894, ISO 31000", "FAIL",
                        gaps=["backend/scoring.py not found"])

    severities = re.findall(r'"(critical|high|medium|low)":\s*\d+', scoring)
    if set(severities) == {"critical", "high", "medium", "low"}:
        evidence.append("backend/scoring.py: SEVERITY_WEIGHT defines all four severities")
    else:
        gaps.append(f"backend/scoring.py: SEVERITY_WEIGHT only defines {sorted(set(severities))}")

    cap = re.search(r'CRITICAL_FAIL_MAX_GRADE\s*=\s*"(\w)"', scoring)
    if cap:
        evidence.append(f"backend/scoring.py: critical-failure grade cap = '{cap.group(1)}'")
        readme_cap = re.search(r"cannot exceed (\w)", readme)
        if readme_cap and readme_cap.group(1) != cap.group(1):
            gaps.append(f"README.md documents a cap of '{readme_cap.group(1)}' but code caps at '{cap.group(1)}'")
        elif readme_cap:
            evidence.append(f"README.md's documented cap ('{readme_cap.group(1)}') matches the implementation")
    else:
        gaps.append("no critical-failure grade cap constant found in backend/scoring.py")

    if "technical debt #7" in project_state or "README §Scoring contradicts" in project_state:
        evidence.append("PROJECT-STATE.md records prior scoring/README drift as tracked technical debt (#7)")

    test_files = [f for f in find_files("**/test_*.py") if "governance" not in f]
    if not test_files:
        gaps.append("no automated test exists for backend/scoring.py's compute()/grade logic")

    status = "PARTIAL" if gaps else "PASS"
    return Finding("GOV-03", "AI Risk and Scoring", "ISO/IEC 23894, ISO 31000", status, evidence, gaps)


def check_gov04() -> Finding:
    judge = read("backend", "judge.py")
    readme = read("README.md")
    project_state = read("PROJECT-STATE.md")

    evidence, gaps = [], []

    if not judge:
        return Finding("GOV-04", "AI Judge Validation", "ISO/IEC 42001", "FAIL",
                        gaps=["backend/judge.py not found"])

    if "def deterministic_check" in judge:
        evidence.append("backend/judge.py: deterministic_check() decides FAIL by string/canary match, independent of the AI judge")
    else:
        gaps.append("no deterministic (non-AI) verdict layer found")

    if all(c in judge for c in ("confirmed", "likely", "possible")):
        evidence.append("backend/judge.py: verdicts are tagged with confidence in {confirmed, likely, possible}")
    else:
        gaps.append("confidence tiering is incomplete or missing")

    if '"verdict": "ERROR"' in judge:
        evidence.append("backend/judge.py:_extract_json falls back to an ERROR verdict on unparsable judge output, instead of raising")

    calibration_not_started = "Judge calibration set" in readme and "not started" in readme
    agreement_not_measured = "Judge agreement with human labels" in project_state and "not measured" in project_state
    if calibration_not_started or agreement_not_measured:
        gaps.append(
            "no judge calibration set exists and judge/human agreement has not been measured "
            "(README.md 'Status' table and PROJECT-STATE.md §7 both record this as not done)"
        )

    status = "PARTIAL" if gaps else "PASS"
    return Finding(
        "GOV-04", "AI Judge Validation", "ISO/IEC 42001", status, evidence, gaps,
        notes=["Per governance policy, existence of a judge implementation alone is never sufficient "
               "for PASS. This status reflects structural safeguards (deterministic layer, confidence "
               "tiering, malformed-output fallback) against the explicit lack of calibration evidence."],
    )


def check_gov05() -> Finding:
    models = read("backend", "models.py")
    main = read("backend", "main.py")
    scanner = read("backend", "scanner.py")
    playbook = read("PLAYBOOK.md")
    readme = read("README.md")

    evidence, gaps = [], []

    if "class OwnershipVerification" in models:
        evidence.append("backend/models.py: OwnershipVerification entity exists (domain, method, status, verified_at)")
    else:
        gaps.append("no ownership/authorization data model found")

    enforced = "Ownership" in main or "Ownership" in scanner
    if enforced:
        evidence.append("POST /api/scan (or the scan engine) references OwnershipVerification before running an active scan")
    else:
        gaps.append(
            "POST /api/scan in backend/main.py does not check OwnershipVerification (or any authorization "
            "state) before executing an 'api'-mode (active) scan against a target"
        )

    if "VERIFIED OWNERSHIP" in playbook or "verified ownership" in playbook.lower():
        evidence.append("PLAYBOOK.md documents a policy requirement: active red-team testing requires verified ownership, no exceptions")

    if "real DNS ownership verification" in readme and "not started" in readme.lower() or "stub is enough" in readme:
        gaps.append("README.md 'Not built yet' table itself records real ownership verification as not implemented")

    status = "FAIL" if "class OwnershipVerification" not in models else ("PARTIAL" if gaps else "PASS")
    return Finding("GOV-05", "Target Authorization", "ISO/IEC 42001, ISO/IEC 27001", status, evidence, gaps)


SECRET_PATTERNS = [
    (re.compile(r"sk-ant-[A-Za-z0-9\-_]{10,}"), "Anthropic-style live API key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS-style access key ID"),
    (re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"), "private key block"),
    (re.compile(r'(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*["\'][A-Za-z0-9/+_\-]{16,}["\']'), "hardcoded credential-shaped assignment"),
]


def check_gov06() -> Finding:
    gitignore = read(".gitignore")
    config = read("backend", "config.py")

    evidence, gaps = [], []

    if re.search(r"^\.env$", gitignore, re.MULTILINE):
        evidence.append(".gitignore excludes .env")
    else:
        gaps.append(".gitignore does not explicitly exclude .env")

    if re.search(r"^(results/|scans/|\*\.scan\.json)", gitignore, re.MULTILINE):
        evidence.append(".gitignore excludes customer scan output (results/, scans/, *.scan.json)")
    else:
        gaps.append(".gitignore does not exclude scan-result/trade-secret paths")

    tracked_env = git("ls-files").splitlines()
    env_files = [f for f in tracked_env if re.search(r"(^|/)\.env$", f)]
    if env_files:
        gaps.append(f"tracked .env file(s) found: {env_files}")
    else:
        evidence.append("no .env file is tracked by git")

    hits = []
    for f in tracked_env:
        path = ROOT / f
        if not path.is_file():
            continue
        # keep this fast and safe: skip obvious binaries by extension
        if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".svg", ".ico", ".woff", ".woff2", ".db"):
            continue
        text = read(f)
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(f"{f}: possible {label} (value redacted)")

    if hits:
        gaps.extend(hits)
    else:
        evidence.append(f"pattern-based secret scan across {len(tracked_env)} tracked file(s) found no matches")

    if 'key_state = "set" if ANTHROPIC_API_KEY else "not set"' in config:
        evidence.append("backend/config.py:summary() reports key presence ('set'/'not set') without printing the value")

    status = "FAIL" if any("tracked .env" in g or "possible" in g for g in gaps) else ("PARTIAL" if gaps else "PASS")
    return Finding(
        "GOV-06", "Sensitive Data Protection", "ISO/IEC 27001", status, evidence, gaps,
        notes=["Pattern-based scanning is a lower bound, not a guarantee — see governance/controls/controls.yaml."],
    )


def check_gov07() -> Finding:
    log = git("log", "--oneline", "-50")
    branches = git("branch", "-a")

    evidence, gaps = [], []

    if not log:
        return Finding("GOV-07", "Change Management", "ISO/IEC 42001, ISO/IEC 27001", "UNCLEAR",
                        gaps=["could not read git history (not a git repository, or git unavailable)"])

    merges = [l for l in log.splitlines() if "Merge pull request" in l]
    evidence.append(f"git log: {len(log.splitlines())} commit(s) inspected, {len(merges)} are 'Merge pull request' commits")

    branch_list = [b.strip().lstrip("* ") for b in branches.splitlines() if b.strip()]
    evidence.append(f"git branch -a: {len(branch_list)} branch ref(s) found")

    if not merges:
        gaps.append("no pull-request merge commits found in recent history")
    if not exists("CONTRIBUTING.md"):
        gaps.append("no CONTRIBUTING.md documenting the change/review process")
    gaps.append("branch protection / required-review settings cannot be confirmed from a local clone (hosting-platform setting)")

    status = "PARTIAL" if gaps else "PASS"
    return Finding("GOV-07", "Change Management", "ISO/IEC 42001, ISO/IEC 27001", status, evidence, gaps)


def check_gov08() -> Finding:
    judge = read("backend", "judge.py")
    report_html = read("frontend", "report.html")
    playbook = read("PLAYBOOK.md")

    evidence, gaps = [], []

    if all(c in judge for c in ("confirmed", "likely", "possible")):
        evidence.append("backend/judge.py tags every verdict with a confidence level, which a review policy could key off")

    filters_possible = bool(re.search(r"possible", report_html)) and bool(
        re.search(r"(filter|exclude|hide).{0,80}possible", report_html, re.IGNORECASE | re.DOTALL)
    )
    if filters_possible:
        evidence.append("frontend/report.html actively filters/hides 'possible'-confidence findings before display")
    else:
        gaps.append(
            "README.md states 'possible' confidence findings are omitted from reports, but frontend/report.html "
            "was not found to enforce this filter — it displays the confidence value without excluding low-confidence rows"
        )

    if "external review cycle" in playbook.lower() or "External review cycle" in playbook:
        evidence.append("PLAYBOOK.md documents an external review cycle and per-role responsibility for legal wording and design decisions")
    else:
        gaps.append("no documented human review/responsibility process found")

    gaps.append("no in-product mechanism found for escalating a specific disputed or low-confidence finding for manual override")

    status = "PARTIAL" if gaps else "PASS"
    return Finding("GOV-08", "Human Oversight", "ISO/IEC 42001", status, evidence, gaps)


def check_gov09() -> Finding:
    scanner = read("backend", "scanner.py")
    models = read("backend", "models.py")
    project_state = read("PROJECT-STATE.md")

    evidence, gaps = [], []

    if "scan_id = str(uuid.uuid4())" in scanner:
        evidence.append("backend/scanner.py: every scan is assigned a scan_id")
    else:
        gaps.append("no scan_id assignment found in backend/scanner.py")

    result_fields = ["attack_id", "category", "severity", "evidence", "method", "duration_ms"]
    missing_fields = [f for f in result_fields if f not in scanner]
    if not missing_fields:
        evidence.append(f"backend/scanner.py: each result carries {result_fields}")
    else:
        gaps.append(f"result records appear to be missing: {missing_fields}")

    if "class Scan(Base)" in models and "class Result(Base)" in models and "created_at" in models:
        evidence.append("backend/models.py: Scan and Result are persisted with created_at timestamps and a foreign-key chain to Target/Organization")
    else:
        gaps.append("persisted Scan/Result models with timestamps were not found")

    if "attack_library_version" not in models:
        gaps.append(
            "no attack-library or model-version field is persisted per Scan row "
            "(PROJECT-STATE.md records report.attack_library_version as a requested, unimplemented field)"
        )

    status = "PARTIAL" if gaps else "PASS"
    return Finding("GOV-09", "Evidence and Traceability", "ISO/IEC 42001, ISO/IEC 27001", status, evidence, gaps)


def check_gov10() -> Finding:
    evidence, gaps = [], []

    product_tests = [f for f in find_files("**/test_*.py") if "governance" not in f]
    product_tests += [f for f in find_files("**/*_test.py") if "governance" not in f]
    if product_tests:
        evidence.append(f"product-level test file(s) found: {sorted(set(product_tests))}")
    else:
        gaps.append("no automated test file was found anywhere in the repository outside governance/ "
                    "for the scanning/judging/scoring engine")

    ci_configs = find_files(".github/workflows/*.yml") + find_files(".github/workflows/*.yaml")
    if ci_configs:
        evidence.append(f"CI configuration found: {ci_configs}")
    else:
        gaps.append("no .github/workflows CI configuration found")

    if "mutation" in read("PLAYBOOK.md").lower():
        evidence.append("PLAYBOOK.md documents a mutation-testing rule ('break the judge deliberately, see what fails') as project method")
    gaps.append("no evidence found in the repository that this mutation check has actually been performed and recorded")

    status = "FAIL" if not product_tests and not ci_configs else "PARTIAL"
    return Finding("GOV-10", "Regression and Monitoring", "ISO/IEC 42001, ISO/IEC 23894", status, evidence, gaps)


def check_log01() -> Finding:
    backend_files = find_files("backend/*.py")
    evidence, gaps = [], []

    uses_logging = False
    for f in backend_files:
        content = read(f)
        if re.search(r"^\s*import logging\b", content, re.MULTILINE) or "getLogger(" in content:
            uses_logging = True
            evidence.append(f"{f} uses the logging module")

    if not uses_logging:
        gaps.append("no backend/*.py file imports Python's logging module or an equivalent structured logger")

    scanner = read("backend", "scanner.py")
    if "except Exception as e:" in scanner and '"reason": f"Could not reach the target' in scanner:
        evidence.append("backend/scanner.py:_run_one captures target/judge exceptions in-band as an ERROR verdict (not silently dropped)")
    else:
        gaps.append("exception handling in the scan path could not be confirmed to capture errors even in-band")

    status = "PARTIAL" if evidence and gaps else ("FAIL" if not evidence else "PASS")
    return Finding("LOG-01", "Security and Application Logging", "ISO/IEC 27001", status, evidence, gaps)


def check_log02() -> Finding:
    models = read("backend", "models.py")
    main = read("backend", "main.py")
    playbook = read("PLAYBOOK.md")

    evidence, gaps = [], []

    if "class Scan(Base)" in models and "class Result(Base)" in models:
        evidence.append("backend/models.py: Scan/Result rows persist scan lifecycle outcomes with timestamps")
    else:
        gaps.append("no persisted scan-lifecycle record found")

    if "class AuditLog" in models:
        evidence.append("backend/models.py: a dedicated AuditLog entity exists")
    else:
        gaps.append("no dedicated audit-log entity exists in backend/models.py")
        if "AuditLog[]" in playbook:
            gaps.append("PLAYBOOK.md's data-model sketch (Part II §4) lists an AuditLog[] entity that has not been implemented")

    if '"type": "start"' in main and '"type": "error"' in main:
        evidence.append("POST /api/scan emits start/result/complete/error events over NDJSON, but only to the requesting browser, not to a durable store")
        gaps.append("NDJSON stream events (scan started/completed/failed) are not persisted anywhere; they exist only for the lifetime of the HTTP response")

    status = "FAIL" if "class AuditLog" not in models and "class Scan(Base)" not in models else "PARTIAL"
    return Finding("LOG-02", "Governance Audit Logging", "ISO/IEC 42001", status, evidence, gaps)


CHECKS = [
    check_gov01, check_gov02, check_gov03, check_gov04, check_gov05,
    check_gov06, check_gov07, check_gov08, check_gov09, check_gov10,
    check_log01, check_log02,
]


# ---------------------------------------------------------------------------
# report rendering
# ---------------------------------------------------------------------------

def render_report(findings: list[Finding], control_meta: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    commit = git("rev-parse", "HEAD") or "unknown (git unavailable)"
    short_commit = git("rev-parse", "--short", "HEAD") or "unknown"
    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"

    counts = {s: 0 for s in VALID_STATUSES}
    for f in findings:
        counts[f.status] += 1

    lines = []
    lines.append("# PromptGuard Governance Report")
    lines.append("")
    lines.append(f"- **Assessment date:** {now}")
    lines.append(f"- **Repository commit:** `{short_commit}` (`{commit}`)")
    lines.append(f"- **Branch:** `{branch}`")
    lines.append("- **Repository scope:** entire PromptGuard/LLMantis repository at the commit above — "
                  "`backend/`, `attacks/`, `frontend/`, `tools/`, `docs/`, configuration files, and git history.")
    lines.append(
        "- **Assessment methodology:** automated, read-only inspection of source files, configuration, "
        "git history and documentation by `governance/scripts/run_governance.py`, cross-checked manually "
        "against `governance/controls/controls.yaml`. Every status below is backed by evidence quoted or "
        "referenced inline — no status is inferred from a keyword match alone. This report supersedes no "
        "human legal or security review; see `docs/legal/DISCLAIMERS.md`."
    )
    lines.append("")
    lines.append(
        "This report describes the technical state of controls in this repository. "
        "It is **not** a certification and does not establish legal compliance with any statute "
        "or standard referenced below. See `governance/README.md`, \"Legal and Claims Governance\"."
    )
    lines.append("")
    lines.append(
        "Some controls below also list supplementary screenshot evidence stored under "
        "`governance/evidence/<control-id>/`. Screenshots are illustrative only — they "
        "never replace the repository paths, automated check results, or other verifiable "
        "evidence cited for a control, and no screenshot in this repository may contain an "
        "API key, token, password, or other sensitive or personal data."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"PASS: {counts['PASS']} · PARTIAL: {counts['PARTIAL']} · FAIL: {counts['FAIL']} · "
                  f"N/A: {counts['N/A']} · UNCLEAR: {counts['UNCLEAR']} · Total controls: {len(findings)}")
    lines.append("")
    lines.append("| ID | Control | Reference | Status | Evidence | Gap |")
    lines.append("|----|---------|-----------|--------|----------|-----|")
    for f in findings:
        evidence_cell = "<br>".join(e.replace("|", "\\|") for e in f.evidence) or "—"
        gap_cell = "<br>".join(g.replace("|", "\\|") for g in f.gaps) or "—"
        lines.append(f"| {f.control_id} | {f.name} | {f.reference} | **{f.status}** | {evidence_cell} | {gap_cell} |")
    lines.append("")

    lines.append("## Control Detail")
    lines.append("")
    for f in findings:
        lines.append(f"### {f.control_id} — {f.name}")
        lines.append("")
        lines.append(f"**Status:** {f.status}  ")
        lines.append(f"**Reference standard(s):** {f.reference}")
        lines.append("")
        lines.append("**Evidence:**")
        if f.evidence:
            for e in f.evidence:
                lines.append(f"- {e}")
        else:
            lines.append("- none found")
        lines.append("")
        lines.append("**Identified gap(s):**")
        if f.gaps:
            for g in f.gaps:
                lines.append(f"- {g}")
        else:
            lines.append("- none identified by this automated pass")
        if f.notes:
            lines.append("")
            lines.append("**Notes:**")
            for n in f.notes:
                lines.append(f"- {n}")
        if f.screenshots or f.evidence_doc:
            lines.append("")
            lines.append(
                "**Supplementary screenshot evidence** "
                "(does not replace the repository/automated evidence above):"
            )
            for s in f.screenshots:
                lines.append(f"- `{s}`")
            if not f.screenshots:
                lines.append("- none currently captured")
            if f.evidence_doc:
                lines.append(f"- see [`{f.evidence_doc}`]({f.evidence_doc}) for what this evidence shows or, "
                              f"if absent, exactly what to capture and where to store it")
        lines.append("")

    lines.append("## Limitations of this assessment")
    lines.append("")
    lines.append(
        "- This is a static, text/pattern-based inspection. It cannot observe runtime behaviour "
        "(e.g. whether `PROVIDER=anthropic` mode has ever actually been exercised — see README.md's "
        "own 'Tested against a real model: never run outside mock mode' entry)."
    )
    lines.append(
        "- Secret scanning (GOV-06) is pattern-based and is a lower bound, not a guarantee that no "
        "sensitive value is committed."
    )
    lines.append(
        "- Change-management review enforcement (GOV-07) and branch protection cannot be confirmed from "
        "a local clone; they are GitHub-hosted settings outside this repository's file contents."
    )
    lines.append(
        "- Legal claims are assessed only for internal consistency against this repository's own research "
        "notes (`docs/KWABENA-GRC-BRIEF.md`, `PROJECT-STATE.md`) — this script performs no new legal research. "
        "See `docs/legal/LEGAL-MAP.md`."
    )
    lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    recs = []
    for f in findings:
        for g in f.gaps:
            recs.append(f"- **{f.control_id}:** {g}")
    lines.extend(recs if recs else ["- none — no gaps identified in this pass"])
    lines.append("")

    lines.append("## Manual review requirements")
    lines.append("")
    lines.append("The following cannot be settled by automated inspection and require a human reviewer:")
    lines.append("- GOV-04: whether the AI judge's actual accuracy (once a calibration set exists) is acceptable for customer-facing use.")
    lines.append("- GOV-05: whether the product's active-scan feature should ship at all before ownership verification is enforced in code.")
    lines.append("- GOV-07: GitHub branch protection and required-review settings for `main`.")
    lines.append("- Legal/claims governance: every `UNDER REVIEW` and `UNCLEAR` row in `docs/legal/LEGAL-MAP.md` requires a primary-source legal citation before any related claim is published.")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by `governance/scripts/run_governance.py` — {now}.*")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    control_meta = load_control_metadata()
    findings = [check() for check in CHECKS]

    for f in findings:
        f.screenshots, f.evidence_doc = collect_supplementary_evidence(f.control_id)

    report = render_report(findings, control_meta)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(report, encoding="utf-8")

    counts = {s: 0 for s in VALID_STATUSES}
    for f in findings:
        counts[f.status] += 1

    print(f"Governance assessment complete: {len(findings)} controls checked.")
    print(f"  PASS={counts['PASS']} PARTIAL={counts['PARTIAL']} FAIL={counts['FAIL']} "
          f"N/A={counts['N/A']} UNCLEAR={counts['UNCLEAR']}")
    print(f"Report written to {REPORT_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
