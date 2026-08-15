"""
Tests for the PromptGuard governance framework.

Uses only the Python standard library (unittest) so these tests run without
installing project dependencies — consistent with governance/scripts/
run_governance.py, which also has zero hard dependencies.

Run with:
    python -m unittest governance/tests/test_governance.py -v
or, if pytest is available in the environment:
    pytest governance/tests/test_governance.py -v
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DIR = ROOT / "governance"

EXPECTED_CONTROL_IDS = {
    "GOV-01", "GOV-02", "GOV-03", "GOV-04", "GOV-05",
    "GOV-06", "GOV-07", "GOV-08", "GOV-09", "GOV-10",
    "LOG-01", "LOG-02",
}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return ""


class TestGovernanceDirectoryStructure(unittest.TestCase):
    """GOVERNANCE-IMPLEMENTATION.md 'Required Structure'."""

    def test_governance_readme_exists(self):
        self.assertTrue((GOVERNANCE_DIR / "README.md").is_file())

    def test_controls_file_exists(self):
        self.assertTrue((GOVERNANCE_DIR / "controls" / "controls.yaml").is_file())

    def test_evidence_directory_exists(self):
        self.assertTrue((GOVERNANCE_DIR / "evidence").is_dir())

    def test_reports_directory_exists(self):
        self.assertTrue((GOVERNANCE_DIR / "reports").is_dir())

    def test_script_exists(self):
        self.assertTrue((GOVERNANCE_DIR / "scripts" / "run_governance.py").is_file())

    def test_tests_directory_exists(self):
        self.assertTrue((GOVERNANCE_DIR / "tests" / "test_governance.py").is_file())


class TestEvidenceStructure(unittest.TestCase):
    """Per-control supplementary evidence folders (screenshots, EVIDENCE.md)."""

    def test_every_control_has_an_evidence_folder(self):
        for control_id in EXPECTED_CONTROL_IDS:
            folder = GOVERNANCE_DIR / "evidence" / control_id
            self.assertTrue(folder.is_dir(), f"missing governance/evidence/{control_id}/")

    def test_every_evidence_folder_documents_itself(self):
        # Either a real screenshot capture note or a "what to capture" placeholder.
        for control_id in EXPECTED_CONTROL_IDS:
            folder = GOVERNANCE_DIR / "evidence" / control_id
            has_doc = (folder / "EVIDENCE.md").is_file() or (folder / "README.md").is_file()
            self.assertTrue(has_doc, f"governance/evidence/{control_id}/ has no EVIDENCE.md or README.md")

    def test_no_screenshot_filename_looks_like_it_contains_a_secret(self):
        # A cheap guard against obviously-named leaks (e.g. "api-key-sk-ant-....png").
        for control_id in EXPECTED_CONTROL_IDS:
            folder = GOVERNANCE_DIR / "evidence" / control_id
            if not folder.is_dir():
                continue
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
                    self.assertNotRegex(f.name.lower(), r"sk-ant-|akia[0-9a-z]{16}|password|secret-key")


class TestLegalDocumentation(unittest.TestCase):
    """GOVERNANCE-IMPLEMENTATION.md Step 8 — Legal and Claims Governance."""

    LEGAL_DIR = ROOT / "docs" / "legal"

    def test_legal_map_exists(self):
        self.assertTrue((self.LEGAL_DIR / "LEGAL-MAP.md").is_file())

    def test_hooks_doc_exists(self):
        self.assertTrue((self.LEGAL_DIR / "HOOKS.md").is_file())

    def test_disclaimers_doc_exists(self):
        self.assertTrue((self.LEGAL_DIR / "DISCLAIMERS.md").is_file())

    def test_forbidden_words_doc_exists(self):
        self.assertTrue((self.LEGAL_DIR / "FORBIDDEN-WORDS.md").is_file())

    def test_forbidden_words_includes_required_minimum(self):
        text = read(self.LEGAL_DIR / "FORBIDDEN-WORDS.md")
        required = [
            "zertifiziert", "Zertifikat", "AI-Act-konform", "DSGVO-konform",
            "gesetzlich vorgeschrieben", "Pflichtprüfung", "garantiert",
            "100 % sicher", "als Einzige", "niemand sonst",
        ]
        missing = [w for w in required if w not in text]
        self.assertEqual(missing, [], f"FORBIDDEN-WORDS.md is missing required terms: {missing}")

    def test_legal_map_uses_governance_status_vocabulary(self):
        text = read(self.LEGAL_DIR / "LEGAL-MAP.md")
        for status in ("VERIFIED", "UNDER REVIEW", "UNCLEAR"):
            self.assertIn(status, text)

    def test_legal_map_does_not_claim_certification_body(self):
        text = read(self.LEGAL_DIR / "LEGAL-MAP.md").lower()
        # The one place "certif*" may legitimately appear is to explain what
        # PromptGuard is NOT, alongside a negation. A bare, unqualified claim
        # of being a certification body must not appear.
        self.assertNotIn("promptguard is a certification body", text)
        self.assertNotIn("llmantis is a certification body", text)


class TestControlsDefinition(unittest.TestCase):
    """GOVERNANCE-IMPLEMENTATION.md Step 7 — Control Definitions."""

    @classmethod
    def setUpClass(cls):
        cls.text = read(GOVERNANCE_DIR / "controls" / "controls.yaml")

    def test_controls_file_not_empty(self):
        self.assertTrue(len(self.text) > 0)

    def test_all_twelve_control_ids_present(self):
        found_ids = set(re.findall(r"- id:\s*(\S+)", self.text))
        missing = EXPECTED_CONTROL_IDS - found_ids
        self.assertEqual(missing, set(), f"controls.yaml is missing control ids: {missing}")

    def test_each_control_has_a_name(self):
        # every "- id: XXX" block should be followed (within a few lines) by a name: field
        blocks = re.split(r"\n(?=  - id: )", self.text)
        control_blocks = [b for b in blocks if re.search(r"- id:\s*(GOV|LOG)-\d+", b)]
        self.assertGreaterEqual(len(control_blocks), 12)
        for block in control_blocks:
            self.assertIn("name:", block)
            self.assertIn("description:", block)
            self.assertIn("reference_standards:", block)
            self.assertIn("automated_checks:", block)
            self.assertIn("manual_checks:", block)
            self.assertIn("expected_evidence:", block)
            self.assertIn("assessment_criteria:", block)

    def test_controls_file_parses_with_pyyaml_if_available(self):
        try:
            import yaml  # type: ignore
        except ImportError:
            self.skipTest("PyYAML not installed in this environment")
        data = yaml.safe_load(self.text)
        self.assertIn("controls", data)
        ids = {c["id"] for c in data["controls"]}
        self.assertEqual(EXPECTED_CONTROL_IDS - ids, set())


class TestGovernanceScript(unittest.TestCase):
    """GOVERNANCE-IMPLEMENTATION.md Step 5 — Automated Governance Checks."""

    def test_script_is_importable_as_a_module(self):
        # Import rather than exec, so a syntax error surfaces as a normal
        # test failure with a traceback instead of a subprocess exit code.
        sys.path.insert(0, str(GOVERNANCE_DIR / "scripts"))
        try:
            import run_governance  # type: ignore
            self.assertTrue(hasattr(run_governance, "main"))
            self.assertTrue(hasattr(run_governance, "CHECKS"))
            self.assertEqual(len(run_governance.CHECKS), 12)
        finally:
            sys.path.pop(0)

    def test_script_runs_end_to_end_and_writes_a_report(self):
        result = subprocess.run(
            [sys.executable, str(GOVERNANCE_DIR / "scripts" / "run_governance.py")],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, f"script exited non-zero:\n{result.stderr}")
        self.assertIn("Governance assessment complete", result.stdout)

        report_path = GOVERNANCE_DIR / "reports" / "GOVERNANCE_REPORT.md"
        self.assertTrue(report_path.is_file())
        report_text = read(report_path)
        self.assertIn("| ID | Control | Reference | Status | Evidence | Gap |", report_text)
        for control_id in EXPECTED_CONTROL_IDS:
            self.assertIn(control_id, report_text)

    def test_report_contains_no_obvious_secret_value(self):
        # The report must describe findings without leaking a secret VALUE,
        # per GOV-06 ("do not expose secret values in governance reports").
        report_path = GOVERNANCE_DIR / "reports" / "GOVERNANCE_REPORT.md"
        if not report_path.is_file():
            self.skipTest("report has not been generated yet")
        text = read(report_path)
        self.assertNotRegex(text, r"sk-ant-[A-Za-z0-9\-_]{10,}")
        self.assertNotRegex(text, r"AKIA[0-9A-Z]{16}")
        self.assertNotIn("-----BEGIN", text)

    def test_report_does_not_claim_certification(self):
        report_path = GOVERNANCE_DIR / "reports" / "GOVERNANCE_REPORT.md"
        if not report_path.is_file():
            self.skipTest("report has not been generated yet")
        text = read(report_path).lower()
        self.assertRegex(text, r"not\*{0,2}\s+a certification")


class TestGovernanceScriptChecksAreEvidenceBased(unittest.TestCase):
    """
    Repository-safe, non-destructive checks on the checker's own logic:
    every individual control-check function must return a status drawn from
    the five allowed values, and must not return PASS with zero evidence.
    """

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(GOVERNANCE_DIR / "scripts"))
        import run_governance  # type: ignore
        cls.module = run_governance

    @classmethod
    def tearDownClass(cls):
        sys.path.pop(0)

    def test_every_check_returns_a_valid_status(self):
        for check in self.module.CHECKS:
            finding = check()
            self.assertIn(finding.status, self.module.VALID_STATUSES)

    def test_no_check_marks_pass_with_no_evidence(self):
        for check in self.module.CHECKS:
            finding = check()
            if finding.status == "PASS":
                self.assertTrue(
                    len(finding.evidence) > 0,
                    f"{finding.control_id} was marked PASS with no evidence",
                )

    def test_every_check_id_is_declared_in_controls_yaml(self):
        text = read(GOVERNANCE_DIR / "controls" / "controls.yaml")
        declared_ids = set(re.findall(r"- id:\s*(\S+)", text))
        for check in self.module.CHECKS:
            finding = check()
            self.assertIn(finding.control_id, declared_ids)


if __name__ == "__main__":
    unittest.main()
