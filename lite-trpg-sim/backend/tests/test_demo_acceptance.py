"""Regression tests for the built-in Demo acceptance routes."""

from __future__ import annotations

import unittest

from backend.tools import demo_acceptance


class DemoAcceptanceTests(unittest.TestCase):
    """Ensure demo routes stay runnable while engine rules evolve."""

    def test_acceptance_routes_cover_multiple_endings(self) -> None:
        """Acceptance runner should cover success and fatal endings."""
        results = demo_acceptance.run_acceptance()
        self.assertGreaterEqual(len(results), 6)
        endings = {str(result.get("ending_id", "")) for result in results if isinstance(result, dict)}
        self.assertIn("ending_escape", endings)
        self.assertIn("ending_compromise", endings)
        self.assertIn("ending_delay", endings)
        self.assertIn("ending_death", endings)
        self.assertIn("ending_corrupt", endings)


if __name__ == "__main__":
    unittest.main()
