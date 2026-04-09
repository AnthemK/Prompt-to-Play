"""Regression tests for story repository normalization and validation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.game.content import ContentError, StoryRepository


def minimal_story_payload(*, interface_version: str | None = None) -> dict:
    """Return a minimal valid story pack payload for repository tests."""
    payload = {
        "id": "test_story",
        "world": {
            "id": "test_world",
            "title": "测试故事",
            "chapter_title": "测试章节",
            "intro": "测试 intro",
            "start_node": "start",
        },
        "stat_meta": {"will": {"label": "意志"}},
        "professions": [
            {
                "id": "tester",
                "name": "测试者",
                "stats": {"will": 3},
            }
        ],
        "items": {},
        "statuses": {},
        "endings": {
            "end_ok": {"id": "end_ok", "title": "结束", "text": "结束。"},
        },
        "nodes": {
            "start": {
                "title": "起点",
                "text": "测试文本。",
                "actions": [],
            }
        },
        "encounters": {},
    }
    if interface_version is not None:
        payload["story_interface_version"] = interface_version
    return payload


class ContentRepositoryTests(unittest.TestCase):
    """Validate story-interface normalization and version checks."""

    def _write_story(self, root: Path, payload: dict) -> None:
        """Write one story.json pack inside a temporary repository root."""
        pack_dir = root / "test_story"
        pack_dir.mkdir(parents=True, exist_ok=True)
        (pack_dir / "story.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_repository_defaults_interface_and_capabilities(self) -> None:
        """Stories without explicit interface fields should be normalized to v1.1."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_story(root, minimal_story_payload())
            repository = StoryRepository(root=root)
            story = repository.get("test_story")
            self.assertEqual(story.get("story_interface_version"), "1.1")
            capabilities = story.get("capabilities")
            self.assertIsInstance(capabilities, dict)
            self.assertIn("checks", capabilities)
            self.assertIn("encounters", capabilities)
            self.assertFalse(bool(capabilities.get("encounters")))

    def test_repository_rejects_unsupported_interface_version(self) -> None:
        """Unsupported story_interface_version should fail fast at load time."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_story(root, minimal_story_payload(interface_version="2.0"))
            with self.assertRaises(ContentError):
                StoryRepository(root=root)


if __name__ == "__main__":
    unittest.main()

