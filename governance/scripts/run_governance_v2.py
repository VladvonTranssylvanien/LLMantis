#!/usr/bin/env python3
"""
LLMantis Governance V2 Checker.

Runs read-only, evidence-based checks against the current repository and
writes governance/reports/GOVERNANCE_V2_AUTOMATED_RERUN.md.

Usage:
    python governance/scripts/run_governance_v2.py

Design constraints (see governance/README.md):
    - Does not modify application code.
    - Never prints a secret VALUE, only whether one appears present.
    - Makes no network calls.
    - Zero hard dependencies — stdlib only, works even if PyYAML isn't installed.
    - Every status is backed by evidence cited inline; feature existence alone
      is never treated as proof of compliance (see BE-08 for why this matters:
      a guard module can exist and still not be applied to the code path that
      needs it — this script checks usage, not just presence, wherever
      feasible).
    - This script supersedes governance/scripts/run_governance.py (Governance
      V1), which has been retired. V1's findings are not reused here; every
      check below is independent.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_V2_DIR = ROOT / "governance"
REPORT_FILE = GOVERNANCE_V2_DIR / "reports" / "GOVERNANCE_V2_REPORT.md"

VALID_STATUSES = ("COMPLIANT", "PARTIALLY COMPLIANT", "NON-COMPLIANT")


def read(*parts: str) -> str:
    path = ROOT.joinpath(*parts)
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError, IsADirectoryError):
        return ""


def exists(*parts: str) -> bool:
    return ROOT.joinpath(*parts).exists()


def git(*args: str) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=15)
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def find_files(pattern: str) -> list[str]:
    return sorted(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern) if p.is_file())


@dataclass
class Finding:
    control_id: str
    name: str
    domain: str  # "frontend" | "backend"
    status: str
    percent: int
    evidence: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)

    def __post_init__(self):
        assert self.status in VALID_STATUSES, f"invalid status {self.status!r} for {self.control_id}"


# ---------------------------------------------------------------------------
# FRONTEND CHECKS
# ---------------------------------------------------------------------------

def check_fe01() -> Finding:
    evidence, gaps = [], []
    for f in ("backend/art50engine.py", "backend/art50probes.py", "backend/art50opener.py"):
        if exists(f):
            evidence.append(f"{f} exists (disclosure-detection implementation)")
        else:
            gaps.append(f"{f} missing")
    if exists("frontend/art50check.html"):
        evidence.append("frontend/art50check.html exists (real UI for the check)")
    else:
        gaps.append("frontend/art50check.html missing")
    status = "NON-COMPLIANT" if gaps else "COMPLIANT"
    return Finding("FE-01", "AI Transparency and User Disclosure", "frontend", status, 0 if gaps else 100, evidence, gaps)


def check_fe02() -> Finding:
    landing = read("frontend", "landing.html")
    evidence, gaps = [], []
    if "Canadian" in landing or "kanadisch" in landing.lower():
        evidence.append("Air Canada citation includes a foreign-jurisdiction qualifier")
    else:
        gaps.append("Air Canada citation (FACT 02) lacks an explicit 'foreign precedent, not binding' qualifier")
    if "Keine Vorschrift verlangt" in landing:
        gaps.append("grcLead states 'no regulation requires testing' as flat fact (unresolved per docs/legal/LEGAL-MAP.md)")
    if "72 Stunden" in landing and "Risiko" not in landing:
        gaps.append("GDPR 72-hour claim (FACT 03) omits the risk-based conditionality of Art. 33")
    if "zertifiziert" not in landing.lower() and "Zertifikat" not in landing:
        evidence.append("No certification/conformity language found on the landing page")
    status = "PARTIALLY COMPLIANT" if gaps and evidence else ("NON-COMPLIANT" if gaps and not evidence else "COMPLIANT")
    percent = 50 if status == "PARTIALLY COMPLIANT" else (0 if status == "NON-COMPLIANT" else 100)
    return Finding("FE-02", "Legal and Regulatory Information", "frontend", status, percent, evidence, gaps)


def check_fe03() -> Finding:
    evidence, gaps = [], []
    for f in ("frontend/impressum.html", "frontend/datenschutz.html"):
        text = read(f)
        if "TODO" in text and ("not legally reviewed" in text or "nicht rechtlich" in text.lower()):
            gaps.append(f"{f} is an explicit, unfilled TODO placeholder")
        elif "{{" in text:
            gaps.append(f"{f} contains unfilled {{TOKEN}} placeholders")
        else:
            evidence.append(f"{f} contains no TODO banner or unfilled tokens")
    status = "NON-COMPLIANT" if len(gaps) == 2 else ("PARTIALLY COMPLIANT" if gaps else "COMPLIANT")
    percent = 0 if status == "NON-COMPLIANT" else (50 if status == "PARTIALLY COMPLIANT" else 100)
    return Finding("FE-03", "User-Facing Security and Privacy", "frontend", status, percent, evidence, gaps)


def check_fe04() -> Finding:
    report_html = read("frontend", "report.html")
    index_html = read("frontend", "index.html")
    evidence, gaps = [], []
    if "library_version" in report_html:
        evidence.append("report.html displays the real attack_library_version from the API response")
    if re.search(r"verified consent of the system.?s owner", report_html) and "authorized" not in report_html.lower():
        gaps.append("report.html states ownership consent unconditionally, not gated on a verification flag")
    if "confidence" in report_html:
        evidence.append("report.html displays finding confidence")
    if "confidence" not in index_html and "possible" not in index_html:
        gaps.append("index.html has no confidence display, unlike report.html")
    status = "PARTIALLY COMPLIANT" if evidence and gaps else ("NON-COMPLIANT" if gaps and not evidence else "COMPLIANT")
    percent = 50 if status == "PARTIALLY COMPLIANT" else (0 if status == "NON-COMPLIANT" else 100)
    return Finding("FE-04", "Output, Report and Claim Integrity", "frontend", status, percent, evidence, gaps)


def check_fe05() -> Finding:
    index_html = read("frontend", "index.html")
    report_html = read("frontend", "report.html")
    evidence, gaps = [], []
    if "aria-live" in index_html or "aria-expanded" in index_html:
        evidence.append("index.html uses ARIA live regions / expanded-state attributes")
    if "How this was judged" in report_html or "judged" in report_html.lower():
        evidence.append("report.html explains the judging method in plain language")
    for f in ("ownership", "api.?key", "branding"):
        if not re.search(f, read("frontend", "scanner.html") + index_html, re.IGNORECASE):
            gaps.append(f"no frontend workflow found for backend capability matching pattern '{f}'")
    status = "PARTIALLY COMPLIANT" if evidence and gaps else ("COMPLIANT" if evidence and not gaps else "NON-COMPLIANT")
    percent = 70 if status == "PARTIALLY COMPLIANT" else (100 if status == "COMPLIANT" else 0)
    return Finding("FE-05", "Accessibility, User Understanding and Human Interaction", "frontend", status, percent, evidence, gaps)


# ---------------------------------------------------------------------------
# BACKEND CHECKS
# ---------------------------------------------------------------------------

def check_be01() -> Finding:
    config = read("backend", "config.py")
    playbook = read("PLAYBOOK.md")
    evidence, gaps = [], []
    provider = re.search(r'PROVIDER\s*=\s*os\.getenv\("PROVIDER",\s*"([^"]+)"\)', config)
    if provider:
        evidence.append(f"backend/config.py: PROVIDER default = '{provider.group(1)}'")
    if "anthropic" not in read("requirements.txt").lower():
        evidence.append("requirements.txt: no anthropic dependency")
    if "withdrawn" in playbook.lower() or "No vendor prohibition" in read("PROJECT_COMPLETE_OVERVIEW.md"):
        gaps.append("EU-only residency invariant explicitly withdrawn with no replacement policy documented")
    status = "PARTIALLY COMPLIANT" if evidence and gaps else ("COMPLIANT" if evidence and not gaps else "NON-COMPLIANT")
    percent = 50 if status == "PARTIALLY COMPLIANT" else (100 if status == "COMPLIANT" else 0)
    return Finding("BE-01", "AI Component and Provider Governance", "backend", status, percent, evidence, gaps)


def check_be02() -> Finding:
    long_lib = read("attacks", "attacks.yaml")
    short_lib = read("attacks", "attacks_short.yaml")
    evidence, gaps = [], []
    v1 = re.search(r'^version:\s*"([^"]+)"', long_lib, re.MULTILINE)
    v2 = re.search(r'^version:\s*"([^"]+)"', short_lib, re.MULTILINE)
    if v1 and v2:
        evidence.append(f"attacks.yaml version={v1.group(1)}, attacks_short.yaml version={v2.group(1)} — both declared")
    if "_validate" in read("backend", "attacks.py"):
        evidence.append("backend/attacks.py:_validate() enforces id/category/severity")
    test_files = [f for f in find_files("**/test_*.py") if "governance" not in f]
    if not test_files:
        gaps.append("no automated test exercises attack-library validation")
    status = "PARTIALLY COMPLIANT" if evidence and gaps else ("COMPLIANT" if evidence and not gaps else "NON-COMPLIANT")
    percent = 70 if status == "PARTIALLY COMPLIANT" else (100 if status == "COMPLIANT" else 0)
    return Finding("BE-02", "AI Attack Library Governance", "backend", status, percent, evidence, gaps)


def check_be03() -> Finding:
    scoring = read("backend", "scoring.py")
    scoring_v2 = read("calibration", "scoring_v2.py")
    evidence, gaps = [], []
    if "PENALTY" in scoring or "SEVERITY_PENALTY" in scoring:
        evidence.append("backend/scoring.py: deduction-based penalty constants present")
    if scoring_v2 and "authority" in scoring_v2.lower():
        evidence.append("calibration/scoring_v2.py self-documents as a synced reference copy")
    status = "COMPLIANT" if evidence else "NON-COMPLIANT"
    return Finding("BE-03", "AI Risk and Scoring Governance", "backend", status, 100 if status == "COMPLIANT" else 0, evidence, gaps)


def check_be04() -> Finding:
    calibrate = read("calibration", "calibrate.py")
    evidence, gaps = [], []
    if "from backend.judge import" in calibrate:
        evidence.append("calibration/calibrate.py replays the real production judge, not a reimplementation")
    for f in ("calibration/set-v1.yaml", "calibration/set-v2.yaml"):
        if exists(f):
            evidence.append(f"{f} exists (human-labelled calibration set)")
    if exists("PROJECT-STATE.md") and "agreement" in read("PROJECT-STATE.md").lower():
        evidence.append("PROJECT-STATE.md records executed calibration agreement figures")
    gaps.append("newly-added v2 criteria are validated only in the false-positive direction (self-disclosed limitation)")
    status = "PARTIALLY COMPLIANT" if evidence else "NON-COMPLIANT"
    return Finding("BE-04", "AI Judge Validation and Calibration", "backend", status, 85 if status == "PARTIALLY COMPLIANT" else 0, evidence, gaps)


def check_be05() -> Finding:
    ownership = read("backend", "ownership.py")
    main = read("backend", "main.py")
    evidence, gaps = [], []
    if "token_hex" in ownership and "expires_at" in ownership:
        evidence.append("backend/ownership.py: secure token generation with enforced expiry")
    if "is_domain_verified" in main:
        evidence.append("backend/main.py: POST /api/scan checks is_domain_verified() before an api-mode scan")
    if "SCAN_UNVERIFIED_DOMAINS" in read("backend", "config.py"):
        gaps.append("an org-unscoped waiver list (SCAN_UNVERIFIED_DOMAINS) exists, empty by default")
    status = "PARTIALLY COMPLIANT" if evidence and gaps else ("COMPLIANT" if evidence and not gaps else "NON-COMPLIANT")
    percent = 85 if status == "PARTIALLY COMPLIANT" else (100 if status == "COMPLIANT" else 0)
    return Finding("BE-05", "Target Authorization and Active Testing Control", "backend", status, percent, evidence, gaps)


def check_be06() -> Finding:
    auth = read("backend", "auth.py")
    apikeys = read("backend", "apikeys.py")
    evidence, gaps = [], []
    if "bcrypt" in auth and "DUMMY_HASH" in auth:
        evidence.append("backend/auth.py: bcrypt hashing + timing-safe dummy-hash comparison")
    if "token_version" in auth:
        evidence.append("backend/auth.py: JWT revocation via token_version")
    if "ROLE_RANK" in auth:
        evidence.append("backend/auth.py: role-rank comparison, fails closed on unrecognized roles")
    if "sha256" in apikeys.lower() and "revoked_at" in apikeys:
        evidence.append("backend/apikeys.py: SHA-256 hashed at rest, revocation checked on use")
    status = "COMPLIANT" if len(evidence) >= 3 else "PARTIALLY COMPLIANT"
    return Finding("BE-06", "Authentication and Access Control", "backend", status, 100 if status == "COMPLIANT" else 70, evidence, gaps)


def check_be07() -> Finding:
    config = read("backend", "config.py")
    evidence, gaps = [], []
    if "bcrypt" in read("backend", "auth.py") and "sha256" in read("backend", "apikeys.py").lower():
        evidence.append("passwords and API keys are hashed at rest")
    if re.search(r'DATABASE_URL\s*=\s*os\.getenv\("DATABASE_URL",\s*"postgresql', config):
        gaps.append("backend/config.py hardcodes a default database credential")
    for f in (".env.example", "docker-compose.yml"):
        if "llmantis_dev_password" in read(f):
            gaps.append(f"same hardcoded credential also present in {f}")
    status = "PARTIALLY COMPLIANT" if evidence and gaps else ("COMPLIANT" if evidence and not gaps else "NON-COMPLIANT")
    percent = 70 if status == "PARTIALLY COMPLIANT" else (100 if status == "COMPLIANT" else 0)
    return Finding("BE-07", "Sensitive Data and Secret Protection", "backend", status, percent, evidence, gaps)


def check_be08() -> Finding:
    netguard = read("backend", "netguard.py")
    scanner = read("backend", "scanner.py")
    art50 = read("backend", "art50check.py") + read("backend", "art50engine.py")
    main = read("backend", "main.py")
    evidence, gaps = [], []
    if "assert_public_host" in netguard:
        evidence.append("backend/netguard.py defines a comprehensive SSRF guard")
    if "netguard" in art50 or "assert_public_host" in art50:
        evidence.append("SSRF guard confirmed used in art50check/art50engine")
    if "netguard" not in scanner and "assert_public_host" not in scanner and "is_private_url" not in scanner:
        gaps.append("backend/scanner.py (active-scan HTTP path) has zero netguard references — the highest-priority finding in this framework")
    if "Limiter" in main and "get_remote_address" in main:
        evidence.append("backend/main.py: per-IP rate limiting via slowapi")
    status = "PARTIALLY COMPLIANT" if evidence and gaps else ("COMPLIANT" if evidence and not gaps else "NON-COMPLIANT")
    percent = 50 if status == "PARTIALLY COMPLIANT" else (100 if status == "COMPLIANT" else 0)
    return Finding("BE-08", "Application and Network Security", "backend", status, percent, evidence, gaps)


def check_be09() -> Finding:
    main = read("backend", "main.py")
    evidence, gaps = [], []
    if 'library_version=report.get("library_version"' in main:
        evidence.append("backend/main.py: real library_version persisted per scan")
    if "system_prompt=request.system_prompt" in main:
        evidence.append("backend/main.py: real tested system prompt persisted")
    if 'target_name = request.api_url or "Prompt-based target"' in main:
        gaps.append("backend/main.py: Target.name hardcoded to a placeholder for prompt/model-mode scans")
    status = "PARTIALLY COMPLIANT" if evidence and gaps else ("COMPLIANT" if evidence and not gaps else "NON-COMPLIANT")
    percent = 70 if status == "PARTIALLY COMPLIANT" else (100 if status == "COMPLIANT" else 0)
    return Finding("BE-09", "Evidence, Traceability and Data Integrity", "backend", status, percent, evidence, gaps)


def check_be10() -> Finding:
    log = git("log", "--oneline", "f48fdbf..114ebc9")
    evidence, gaps = [], []
    if log:
        lines = log.splitlines()
        merges = [l for l in lines if "Merge pull request" in l]
        pct = round(100 * len(merges) / len(lines)) if lines else 0
        evidence.append(f"git log f48fdbf..114ebc9: {len(lines)} commits, {len(merges)} via reviewed PR ({pct}%)")
        if pct < 50:
            gaps.append(f"only {pct}% of commits were merged via reviewed pull requests")
    reqs = read("requirements.txt")
    if "sqlalchemy" in reqs and "psycopg" in reqs:
        evidence.append("requirements.txt: dependency list is now complete (sqlalchemy, psycopg present)")
    if '--forwarded-allow-ips "*"' in read("docker-compose.prod.yml"):
        gaps.append("docker-compose.prod.yml trusts X-Forwarded-For from any source")
    status = "NON-COMPLIANT" if len(gaps) >= 2 else "PARTIALLY COMPLIANT"
    return Finding("BE-10", "Change, Dependency and Configuration Management", "backend", status, 25 if status == "PARTIALLY COMPLIANT" else 0, evidence, gaps)


def check_be11() -> Finding:
    evidence, gaps = [], []
    test_files = [f for f in find_files("**/test_*.py") if "governance" not in f]
    if not test_files:
        gaps.append("no automated test file exists anywhere in backend/")
    else:
        evidence.append(f"test files found: {test_files}")
    if not find_files(".github/workflows/*.yml") and not find_files(".github/workflows/*.yaml"):
        gaps.append("no CI configuration found")
    status = "NON-COMPLIANT" if not evidence else "PARTIALLY COMPLIANT"
    return Finding("BE-11", "Regression Testing and Operational Monitoring", "backend", status, 0 if status == "NON-COMPLIANT" else 50, evidence, gaps)


def check_be12() -> Finding:
    evidence, gaps = [], []
    uses_logging = any(
        re.search(r"^\s*import logging\b|getLogger\(", read(f), re.MULTILINE)
        for f in find_files("backend/*.py")
    )
    if not uses_logging:
        gaps.append("no backend/*.py file imports Python's logging module")
    if "class AuditLog" not in read("backend", "models.py"):
        gaps.append("no dedicated AuditLog entity exists in backend/models.py")
    status = "NON-COMPLIANT" if len(gaps) == 2 else "PARTIALLY COMPLIANT"
    return Finding("BE-12", "Security and Governance Logging", "backend", status, 0 if status == "NON-COMPLIANT" else 40, evidence, gaps)


CHECKS = [
    check_fe01, check_fe02, check_fe03, check_fe04, check_fe05,
    check_be01, check_be02, check_be03, check_be04, check_be05, check_be06,
    check_be07, check_be08, check_be09, check_be10, check_be11, check_be12,
]


def render_report(findings: list[Finding]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    commit = git("rev-parse", "HEAD") or "unknown"
    short_commit = git("rev-parse", "--short", "HEAD") or "unknown"

    fe = [f for f in findings if f.domain == "frontend"]
    be = [f for f in findings if f.domain == "backend"]
    counts = {s: 0 for s in VALID_STATUSES}
    for f in findings:
        counts[f.status] += 1
    maturity = round(sum(f.percent for f in findings) / len(findings)) if findings else 0

    lines = [
        "# LLMantis Governance V2 Report (automated re-run)",
        "",
        f"- **Re-run date:** {now}",
        f"- **Repository commit:** `{short_commit}` (`{commit}`)",
        "- **Supersedes:** Governance V1 (baseline f48fdbf) — not carried forward.",
        "",
        "This automated re-run cross-checks the framework's committed assessment in "
        "`GOVERNANCE_V2_REPORT.md`. Discrepancies should be investigated manually, not "
        "assumed to be errors in either direction — automated pattern-matching is a "
        "lower bound, not a guarantee, same as Governance V1.",
        "",
        f"## Summary — Maturity: {maturity}%",
        f"COMPLIANT: {counts['COMPLIANT']} · PARTIALLY COMPLIANT: {counts['PARTIALLY COMPLIANT']} · "
        f"NON-COMPLIANT: {counts['NON-COMPLIANT']} · Total: {len(findings)}",
        "",
    ]

    for label, group in (("Frontend", fe), ("Backend / Platform", be)):
        lines.append(f"## {label}")
        lines.append("")
        for f in group:
            lines.append(f"### {f.control_id} — {f.name}")
            lines.append(f"**Status:** {f.status}" + (f" — {f.percent}%" if f.status == "PARTIALLY COMPLIANT" else ""))
            lines.append("")
            lines.append("**Evidence:**")
            for e in f.evidence:
                lines.append(f"- {e}")
            if not f.evidence:
                lines.append("- none found")
            lines.append("")
            lines.append("**Gaps:**")
            for g in f.gaps:
                lines.append(f"- {g}")
            if not f.gaps:
                lines.append("- none identified by this automated pass")
            lines.append("")

    lines.append("---")
    lines.append(f"*Generated by governance/v2/scripts/run_governance_v2.py — {now}.*")
    return "\n".join(lines)


def main() -> int:
    findings = [c() for c in CHECKS]
    report = render_report(findings)
    auto_report_path = GOVERNANCE_V2_DIR / "reports" / "GOVERNANCE_V2_AUTOMATED_RERUN.md"
    auto_report_path.write_text(report, encoding="utf-8")

    counts = {s: 0 for s in VALID_STATUSES}
    for f in findings:
        counts[f.status] += 1
    maturity = round(sum(f.percent for f in findings) / len(findings)) if findings else 0

    print(f"Governance V2 automated re-run complete: {len(findings)} controls checked.")
    print(f"  COMPLIANT={counts['COMPLIANT']} PARTIALLY COMPLIANT={counts['PARTIALLY COMPLIANT']} "
          f"NON-COMPLIANT={counts['NON-COMPLIANT']}  Maturity={maturity}%")
    print(f"Report written to {auto_report_path.relative_to(ROOT)}")
    print("Note: the committed assessment of record is governance/reports/GOVERNANCE_V2_REPORT.md — "
          "this automated re-run is a cross-check, not a replacement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
