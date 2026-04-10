"""Regression tests for backend debug-trace diagnostics."""

from __future__ import annotations

import unittest

from backend.game.engine import GameEngine


class EngineDebugTests(unittest.TestCase):
    """Validate debug trace generation and retrieval from engine sessions."""

    def test_meta_exposes_story_interface_version_and_capabilities(self) -> None:
        """Engine meta should expose normalized story interface contract fields."""
        engine = GameEngine()
        meta = engine.meta()
        self.assertIn("story_interface_version", meta)
        self.assertIn("capabilities", meta)
        self.assertIsInstance(meta.get("capabilities"), dict)
        self.assertEqual(meta.get("story_interface_version"), "1.1")

        stories = meta.get("stories", [])
        self.assertIsInstance(stories, list)
        self.assertTrue(stories)
        for story in stories:
            self.assertIsInstance(story, dict)
            self.assertIn("story_interface_version", story)
            self.assertIn("capabilities", story)
            self.assertIsInstance(story.get("capabilities"), dict)
            self.assertEqual(story.get("story_interface_version"), "1.1")
            self.assertIn("setup_summary", story)
            self.assertIn("setup_details", story)
            self.assertIsInstance(story.get("setup_details"), list)

        self.assertIn("world", meta)
        self.assertIsInstance(meta.get("world"), dict)
        self.assertIn("ui", meta.get("world", {}))
        self.assertIsInstance(meta.get("world", {}).get("ui"), dict)

    def test_engine_debug_trace_api_surface(self) -> None:
        """Engine should expose recent structured debug entries per session."""
        engine = GameEngine()
        meta = engine.meta()
        stories = meta.get("stories", [])
        if isinstance(stories, list) and len(stories) > 1:
            self.assertNotEqual(meta.get("default_story_id"), "demo")
        professions = meta.get("professions", [])
        self.assertTrue(professions)
        profession_id = str(professions[0].get("id", ""))
        self.assertTrue(profession_id)

        view = engine.new_game("DebugTester", profession_id, story_id=meta.get("active_story_id"))
        session_id = str(view.get("session_id", ""))
        self.assertTrue(session_id)

        # Trigger one action request to generate extra debug entries.
        scene_actions = view.get("scene", {}).get("actions", [])
        if scene_actions:
            first_action = scene_actions[0]
            engine.act(session_id, str(first_action.get("id", "")))

        trace = engine.debug_trace(session_id, limit=50)
        entries = trace.get("entries", [])
        self.assertTrue(entries)
        self.assertGreaterEqual(trace.get("total_entries", 0), len(entries))
        self.assertTrue(any(entry.get("event") == "session.created" for entry in entries if isinstance(entry, dict)))
        self.assertTrue(any(entry.get("event") == "action.start" for entry in entries if isinstance(entry, dict)))


if __name__ == "__main__":
    unittest.main()
