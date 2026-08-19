"""
Tests for the LLMantis Governance V2 framework.

Uses only the Python standard library so these tests run without installing
project dependencies.

Run with:
    python -m unittest governance.v2.tests.test_governance_v2 -v
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V2_DIR = ROOT / "governance"

EXPECTED_CONTROL_IDS = {
    "FE-01", "FE-02", "FE-03", "FE-04", "FE-05",
    "BE-01", "BE-02", "BE-03", "BE-04", "BE-05", "BE-06",
    "BE-07", "BE-08", "BE-09", "BE-10", "BE-11", "BE-12",
}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return ""


class TestGovernanceV2Structure(unittest.TestCase):
    def test_readme_exists(self):
        self.assertTrue((V2_DIR / "README.md").is_file())

    def test_control_files_exist(self):
        self.assertTrue((V2_DIR / "controls" / "frontend-controls.yaml").is_file())
        self.assertTrue((V2_DIR / "controls" / "backend-controls.yaml").is_file())

    def test_report_exists(self):
        self.assertTrue((V2_DIR / "reports" / "GOVERNANCE_V2_REPORT.md").is_file())

    def test_script_exists(self):
        self.assertTrue((V2_DIR / "scripts" / "run_governance_v2.py").is_file())

    def test_every_control_has_an_evidence_folder(self):
        for cid in EXPECTED_CONTROL_IDS:
            folder = V2_DIR / "evidence" / cid
            self.assertTrue(folder.is_dir(), f"missing governance/v2/evidence/{cid}/")
            self.assertTrue((folder / "EVIDENCE.md").is_file(), f"missing EVIDENCE.md for {cid}")

    def test_v1_is_not_present_in_working_tree(self):
        # Governance V1 was deliberately removed from the working tree (team
        # decision) — it remains recoverable via git history (commit 474b20e)
        # but must not silently reappear. V2 legitimately reuses some of the
        # same directory names (controls/, evidence/, reports/) under the
        # flat governance/ layout, so this checks for V1-specific filenames,
        # not directory presence.
        self.assertFalse((ROOT / "governance" / "controls" / "controls.yaml").exists())
        self.assertFalse((ROOT / "governance" / "reports" / "GOVERNANCE_REPORT.md").exists())
        self.assertFalse((ROOT / "governance" / "scripts" / "run_governance.py").exists())
        self.assertFalse((ROOT / "governance" / "tests" / "test_governance.py").exists())
        self.assertFalse((ROOT / "GOVERNANCE-IMPLEMENTATION.md").exists())


class TestControlsDefinitions(unittest.TestCase):
    def test_all_seventeen_ids_present(self):
        text = read(V2_DIR / "controls" / "frontend-controls.yaml") + read(V2_DIR / "controls" / "backend-controls.yaml")
        found = set(re.findall(r"- id:\s*(\S+)", text))
        missing = EXPECTED_CONTROL_IDS - found
        self.assertEqual(missing, set(), f"missing control ids: {missing}")

    def test_frontend_file_has_exactly_five(self):
        text = read(V2_DIR / "controls" / "frontend-controls.yaml")
        found = set(re.findall(r"- id:\s*(FE-\d+)", text))
        self.assertEqual(len(found), 5)

    def test_backend_file_has_exactly_twelve(self):
        text = read(V2_DIR / "controls" / "backend-controls.yaml")
        found = set(re.findall(r"- id:\s*(BE-\d+)", text))
        self.assertEqual(len(found), 12)

    def test_yaml_parses_if_pyyaml_available(self):
        try:
            import yaml  # type: ignore
        except ImportError:
            self.skipTest("PyYAML not installed in this environment")
        for fname in ("frontend-controls.yaml", "backend-controls.yaml"):
            data = yaml.safe_load(read(V2_DIR / "controls" / fname))
            self.assertIn("controls", data)
            self.assertEqual(data.get("baseline_commit"), "114ebc9")


class TestGovernanceV2Report(unittest.TestCase):
    def test_report_references_correct_baseline(self):
        text = read(V2_DIR / "reports" / "GOVERNANCE_V2_REPORT.md")
        self.assertIn("114ebc9", text)
        self.assertIn("f48fdbf", text)  # cited as the superseded V1 baseline, not reused as current

    def test_report_contains_all_seventeen_controls(self):
        text = read(V2_DIR / "reports" / "GOVERNANCE_V2_REPORT.md")
        for cid in EXPECTED_CONTROL_IDS:
            self.assertIn(cid, text)

    def test_report_does_not_claim_certification(self):
        text = read(V2_DIR / "reports" / "GOVERNANCE_V2_REPORT.md").lower()
        self.assertIn("not a certification", text)

    def test_report_contains_no_obvious_secret_value(self):
        text = read(V2_DIR / "reports" / "GOVERNANCE_V2_REPORT.md")
        self.assertNotRegex(text, r"sk-ant-[A-Za-z0-9\-_]{10,}")
        self.assertNotIn("llmantis_dev_password", text)  # gap is named, value is not reproduced verbatim as a live secret


class TestGovernanceV2Script(unittest.TestCase):
    def test_script_is_importable(self):
        sys.path.insert(0, str(V2_DIR / "scripts"))
        try:
            import run_governance_v2 as rg  # type: ignore
            self.assertTrue(hasattr(rg, "main"))
            self.assertEqual(len(rg.CHECKS), 17)
        finally:
            sys.path.pop(0)

    def test_script_runs_end_to_end(self):
        result = subprocess.run(
            [sys.executable, str(V2_DIR / "scripts" / "run_governance_v2.py")],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, f"script exited non-zero:\n{result.stderr}")
        self.assertIn("Governance V2 automated re-run complete", result.stdout)
        auto_report = V2_DIR / "reports" / "GOVERNANCE_V2_AUTOMATED_RERUN.md"
        self.assertTrue(auto_report.is_file())

    def test_every_check_returns_a_valid_status(self):
        sys.path.insert(0, str(V2_DIR / "scripts"))
        try:
            import run_governance_v2 as rg  # type: ignore
            for check in rg.CHECKS:
                finding = check()
                self.assertIn(finding.status, rg.VALID_STATUSES)
                self.assertIn(finding.control_id, EXPECTED_CONTROL_IDS)
        finally:
            sys.path.pop(0)


if __name__ == "__main__":
    unittest.main()
