"""Regression tests for story validation helpers and CLI behavior."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from backend.game.content import StoryRepository
from backend.game.story_validation import validate_repository


def make_story_payload(*, broken_goto: bool = False) -> dict:
    """Build a compact story pack payload for validation tests."""
    goto_target = "missing_node" if broken_goto else "end_node"
    return {
        "id": "validator_case",
        "story_interface_version": "1.1",
        "world": {
            "id": "validator_world",
            "title": "校验案例",
            "chapter_title": "测试章",
            "intro": "测试剧情",
            "start_node": "start",
            "default_ending_id": "ending_ok",
        },
        "stat_meta": {"will": {"label": "意志"}},
        "professions": [
            {
                "id": "tester",
                "name": "测试者",
                "stats": {"will": 3},
                "starting_items": ["medkit"],
            }
        ],
        "items": {
            "medkit": {"id": "medkit", "name": "急救包"},
        },
        "statuses": {},
        "endings": {
            "ending_ok": {"id": "ending_ok", "title": "结束", "text": "结束。"},
        },
        "nodes": {
            "start": {
                "title": "起点",
                "text": "你站在岔路口。",
                "actions": [
                    {
                        "id": "go_forward",
                        "label": "向前",
                        "kind": "story",
                        "effects": [{"op": "goto", "node": goto_target}],
                    }
                ],
            },
            "end_node": {
                "title": "终点",
                "text": "结束。",
                "actions": [],
            },
        },
        "encounters": {},
    }


class StoryValidationTests(unittest.TestCase):
    """Validate story reference checks and CLI exit semantics."""

    def _write_story(self, root: Path, payload: dict) -> None:
        """Write one story pack payload into a temporary repository root."""
        pack_dir = root / "validator_case"
        pack_dir.mkdir(parents=True, exist_ok=True)
        (pack_dir / "story.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_builtin_repository_validation_passes(self) -> None:
        """Current built-in story packs should pass reference validation."""
        project_root = Path(__file__).resolve().parents[2]
        repository = StoryRepository(root=project_root / "backend" / "stories")
        issues = validate_repository(repository)
        self.assertEqual(issues, [])

    def test_validation_reports_missing_goto_node(self) -> None:
        """Validator should report missing node references from goto effects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_story(root, make_story_payload(broken_goto=True))
            repository = StoryRepository(root=root)
            issues = validate_repository(repository)
            self.assertTrue(issues)
            self.assertTrue(any(issue.get("code") == "NODE_MISSING" for issue in issues))

    def test_validation_reports_unknown_effect_op(self) -> None:
        """Validator should reject effect ops outside the canonical DSL contract."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = make_story_payload()
            payload["nodes"]["start"]["actions"][0]["effects"][0]["op"] = "teleport_magic"
            self._write_story(root, payload)
            repository = StoryRepository(root=root)
            issues = validate_repository(repository)
            self.assertTrue(issues)
            self.assertTrue(any(issue.get("code") == "EFFECT_OP_INVALID" for issue in issues))

    def test_story_cli_validate_exit_code(self) -> None:
        """CLI should return non-zero when validation issues are detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_story(root, make_story_payload(broken_goto=True))
            script = Path(__file__).resolve().parents[2] / "backend" / "tools" / "story_cli.py"
            completed = subprocess.run(
                [sys.executable, str(script), "validate", "--root", str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("NODE_MISSING", completed.stdout + completed.stderr)

    def test_story_cli_scaffold_creates_loadable_story(self) -> None:
        """Scaffold command should generate a minimal story pack that loads and validates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script = Path(__file__).resolve().parents[2] / "backend" / "tools" / "story_cli.py"
            scaffold = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "scaffold",
                    "--root",
                    str(root),
                    "--id",
                    "new_story_case",
                    "--title",
                    "新故事模板",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(scaffold.returncode, 0, msg=scaffold.stdout + scaffold.stderr)

            repository = StoryRepository(root=root)
            story = repository.get("new_story_case")
            self.assertEqual(story.get("story_interface_version"), "1.1")

            issues = validate_repository(repository, story_id="new_story_case")
            self.assertEqual(issues, [])

    def test_validation_reports_missing_status_in_status_aware_check_config(self) -> None:
        """Validator should reject status-aware config that points at a missing status."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = make_story_payload()
            payload["nodes"]["start"]["actions"][0] = {
                "id": "brace",
                "label": "稳住",
                "kind": "save",
                "save": {
                    "stat": "will",
                    "dc": 10,
                    "extra_bonus_if_statuses": [
                        {"status": "missing_guard", "bonus": 2, "source": "状态：未知加成"}
                    ],
                },
                "on_success": {"effects": []},
                "on_failure": {"effects": []},
            }
            self._write_story(root, payload)
            repository = StoryRepository(root=root)
            issues = validate_repository(repository)
            self.assertTrue(any(issue.get("code") == "STATUS_MISSING" for issue in issues))


if __name__ == "__main__":
    unittest.main()
