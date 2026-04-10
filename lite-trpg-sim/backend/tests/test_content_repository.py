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
            "ui": {
                "setup_summary": "测试开场摘要",
                "setup_details": [{"label": "时长", "value": "10 分钟"}],
                "resource_labels": {"hp": "体力", "doom": "压力"},
            },
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

    def test_repository_normalizes_world_ui_metadata(self) -> None:
        """Optional story-facing UI metadata should be normalized into the story payload."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_story(root, minimal_story_payload())
            repository = StoryRepository(root=root)
            story = repository.get("test_story")
            ui = story.get("world", {}).get("ui", {})
            self.assertEqual(ui.get("setup_summary"), "测试开场摘要")
            self.assertEqual(ui.get("setup_details"), [{"label": "时长", "value": "10 分钟"}])
            self.assertEqual(ui.get("resource_labels"), {"hp": "体力", "doom": "压力"})

    def test_repository_rejects_invalid_world_ui_resource_labels(self) -> None:
        """Story-facing UI metadata should fail fast when resource_labels is malformed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = minimal_story_payload()
            payload["world"]["ui"]["resource_labels"] = ["hp"]
            self._write_story(root, payload)
            with self.assertRaises(ContentError):
                StoryRepository(root=root)


if __name__ == "__main__":
    unittest.main()
