"""Checks for snapshot severity and BPC-derived access classification."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from unittest.mock import Mock, patch
from urllib.request import Request

import collect
from inspect_access import classify_access
from validate_snapshot import validate


class PipelineTests(unittest.TestCase):
    def report(self):
        now = datetime(2026, 10, 3, tzinfo=timezone.utc).isoformat()
        return {
            "schema_version": 5,
            "snapshot_as_of": now,
            "completed_at": now,
            "run_args": {"max_age_hours": 36, "limit": 15},
            "sources": [{"id": "example", "health_status": "ok", "contribution_status": "contributed", "emit_enabled": True, "retrieval_limit_reached": False}],
            "items": [{"publisher": "Example", "id": "one", "url": "https://example.com/one", "published_at": now}],
            "summary": {"candidate_items": 1},
        }

    def test_valid_snapshot_has_no_findings(self):
        self.assertEqual(validate(self.report()), [])

    def test_limit_reached_is_p1(self):
        report = self.report()
        report["sources"][0]["retrieval_limit_reached"] = True
        self.assertIn(("P1", "retrieval limit reached by 1 source(s); coverage may be incomplete"), validate(report))

    def test_out_of_window_is_p0(self):
        report = self.report()
        report["items"][0]["published_at"] = "2026-09-01T00:00:00+00:00"
        self.assertTrue(any(level == "P0" for level, _ in validate(report)))

    def test_invalid_snapshot_time_is_reported_as_p0(self):
        report = self.report()
        report["snapshot_as_of"] = "not-a-time"
        self.assertTrue(any(level == "P0" for level, _ in validate(report)))

    def test_access_levels_do_not_claim_full_text(self):
        self.assertEqual(classify_access(403, []), "authorization_or_request_blocked")
        self.assertEqual(classify_access(200, ["jsonld_article_body"]), "public_body_candidate")
        self.assertEqual(classify_access(200, ["jsonld_article_body", "piano_or_tinypass"]), "public_page_restricted_or_uncertain")

    def test_auto_network_mode_falls_back_without_disabling_tls(self):
        old_mode = collect._NETWORK_MODE
        collect._NETWORK_MODE = "auto"
        fallback = Mock()
        try:
            with patch("collect.urlopen", side_effect=OSError("system route failed")), patch.object(collect._IPV6_FIRST_OPENER, "open", return_value=fallback) as direct:
                result = collect.open_verified(Request("https://www.news.cn/"), timeout=3)
        finally:
            collect._NETWORK_MODE = old_mode
        self.assertIs(result, fallback)
        direct.assert_called_once()


if __name__ == "__main__":
    unittest.main()
