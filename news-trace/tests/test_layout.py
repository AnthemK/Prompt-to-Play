"""Regression checks for executing relocated scripts outside the project root."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import audit_candidates
import collect
from check_layout import check
from paths import CONFIG, ROOT, SCRIPTS


class LayoutTests(unittest.TestCase):
    def test_local_links_and_protected_originals(self):
        _, issues = check()
        self.assertEqual(issues, [])

    def test_collector_loads_all_config_from_other_working_directory(self):
        (ROOT / "tmp").mkdir(exist_ok=True)
        paths = [CONFIG / "sources.json", *sorted((CONFIG / "sources").glob("*.json"))]
        expected = [source["id"] for path in paths for source in json.loads(path.read_text())["feeds"]]
        self.assertEqual(len(expected), len(set(expected)))
        with tempfile.TemporaryDirectory(prefix="layout-", dir=ROOT / "tmp") as temporary:
            previous = Path.cwd()
            previous_mode = collect._NETWORK_MODE
            try:
                os.chdir(temporary)
                with patch.object(sys, "argv", ["collect.py", "--output", "report.json"]), patch.object(collect, "collect", return_value=[]) as fetch:
                    collect.main()
                report = json.loads(Path("report.json").read_text())
                self.assertEqual([source["id"] for source in report["sources"]], expected)
                self.assertEqual(fetch.call_count, len(expected))
                self.assertEqual(set(report["code_sha256"]), {"collect.py", "article_probe.py", "paths.py"})
                self.assertTrue(all(len(value) == 64 for value in report["code_sha256"].values()))
                self.assertFalse(any(source["health_status"] == "error" for source in report["sources"]))
            finally:
                collect._NETWORK_MODE = previous_mode
                os.chdir(previous)

    def test_candidate_audit_loads_config_from_other_working_directory(self):
        (ROOT / "tmp").mkdir(exist_ok=True)
        expected = json.loads((CONFIG / "candidate-endpoints.json").read_text())["feeds"]
        with tempfile.TemporaryDirectory(prefix="audit-", dir=ROOT / "tmp") as temporary:
            previous = Path.cwd()
            try:
                os.chdir(temporary)
                with patch.object(sys, "argv", ["audit_candidates.py", "--output", "audit.json"]), patch.object(audit_candidates, "audit", return_value={}) as fetch:
                    audit_candidates.main()
                report = json.loads(Path("audit.json").read_text())
                self.assertEqual([row["id"] for row in report["sources"]], [row["id"] for row in expected])
                self.assertEqual(fetch.call_count, len(expected))
            finally:
                os.chdir(previous)

    def test_access_probe_requires_explicit_input(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "inspect_access.py")], cwd=ROOT.parent, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--report", result.stderr)


if __name__ == "__main__":
    unittest.main()
