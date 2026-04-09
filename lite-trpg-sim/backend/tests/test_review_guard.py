"""Regression tests for repository review-guard checks."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.tools import review_guard


class _CompletedProcess:
    """Small stand-in object for subprocess.run test doubles."""

    def __init__(self, *, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class ReviewGuardTests(unittest.TestCase):
    """Validate doc-sync guard behavior under different git change sets."""

    def test_doc_sync_passes_when_code_and_docs_changed(self) -> None:
        """Guard should pass when tracked code and doc paths both changed."""
        git_output = " M backend/game/rules.py\n M README.md\n"
        with patch("backend.tools.review_guard.subprocess.run", return_value=_CompletedProcess(returncode=0, stdout=git_output)):
            result = review_guard.run_doc_sync_check()
        self.assertEqual(result, 0)

    def test_doc_sync_fails_when_only_code_changed(self) -> None:
        """Guard should fail when code changed without any tracked doc updates."""
        git_output = " M backend/game/rules.py\n M frontend/app.js\n"
        with patch("backend.tools.review_guard.subprocess.run", return_value=_CompletedProcess(returncode=0, stdout=git_output)):
            result = review_guard.run_doc_sync_check()
        self.assertEqual(result, 1)

    def test_doc_sync_skips_when_no_tracked_code_changed(self) -> None:
        """Guard should skip/pass if only non-tracked files changed."""
        git_output = " M backend/stories/grimweave/story.json\n"
        with patch("backend.tools.review_guard.subprocess.run", return_value=_CompletedProcess(returncode=0, stdout=git_output)):
            result = review_guard.run_doc_sync_check()
        self.assertEqual(result, 0)

    def test_doc_sync_handles_monorepo_prefixed_paths(self) -> None:
        """Guard should normalize git paths prefixed with project folder name."""
        git_output = " M lite-trpg-sim/backend/game/rules.py\n M lite-trpg-sim/README.md\n"
        with patch("backend.tools.review_guard.subprocess.run", return_value=_CompletedProcess(returncode=0, stdout=git_output)):
            result = review_guard.run_doc_sync_check()
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
