"""Story-pack discovery and normalization layer.

This module is the main guardrail for data-driven content. It loads raw story
files, validates required shapes, and hands the engine a normalized structure
plus a runtime object that implements `StoryRuntime`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .story_interface import StoryRuntime
from .story_runtime import StoryPackRuntime


class ContentError(RuntimeError):
    """Raised when a story pack cannot be discovered or normalized."""

    pass


class StoryRepository:
    """Discover, validate, normalize, and expose story packs."""

    def __init__(self, root: Path | None = None) -> None:
        backend_root = Path(__file__).resolve().parents[1]
        self.root = root or (backend_root / "stories")
        self._stories: dict[str, dict[str, Any]] = {}
        self._runtimes: dict[str, StoryRuntime] = {}
        self._default_story_id: str | None = None
        self.reload()

    def reload(self) -> None:
        """Rescan the stories directory and rebuild runtime objects."""
        stories: dict[str, dict[str, Any]] = {}
        runtimes: dict[str, StoryRuntime] = {}

        if not self.root.exists():
            raise ContentError(f"stories directory not found: {self.root}")

        for pack_dir in sorted(self.root.iterdir()):
            if not pack_dir.is_dir():
                continue

            story_file = self._find_story_file(pack_dir)
            if not story_file:
                continue

            data = self._load_story_file(story_file)
            story_id = str(data.get("id") or pack_dir.name).strip()
            if not story_id:
                raise ContentError(f"invalid story id in {story_file}")
            if story_id in stories:
                raise ContentError(f"duplicate story id: {story_id}")

            normalized = self._normalize_story(data, story_id)
            stories[story_id] = normalized
            runtimes[story_id] = StoryPackRuntime(normalized)

        if not stories:
            raise ContentError(f"no story pack found in {self.root}")

        self._stories = stories
        self._runtimes = runtimes
        self._default_story_id = sorted(stories.keys())[0]

    def _find_story_file(self, pack_dir: Path) -> Path | None:
        """Return the canonical story file for one pack directory."""
        for name in ("story.json", "story.yaml", "story.yml"):
            candidate = pack_dir / name
            if candidate.exists() and candidate.is_file():
                return candidate
        return None

    def _load_story_file(self, file_path: Path) -> dict[str, Any]:
        """Parse a JSON or YAML story file into a dictionary."""
        raw_text = file_path.read_text(encoding="utf-8")
        suffix = file_path.suffix.lower()

        if suffix == ".json":
            parsed = json.loads(raw_text)
        elif suffix in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore
            except Exception as exc:  # pragma: no cover
                raise ContentError("yaml story requires PyYAML installed") from exc
            parsed = yaml.safe_load(raw_text)
        else:
            raise ContentError(f"unsupported story format: {file_path}")

        if not isinstance(parsed, dict):
            raise ContentError(f"story root must be object: {file_path}")
        return parsed

    def _normalize_story(self, data: dict[str, Any], story_id: str) -> dict[str, Any]:
        """Validate required fields and fill in system defaults."""
        world = data.get("world")
        stat_meta = data.get("stat_meta")
        professions = data.get("professions")
        items = data.get("items")
        statuses = data.get("statuses")
        endings = data.get("endings")
        nodes = data.get("nodes")
        encounters = data.get("encounters", {})

        if not isinstance(world, dict):
            raise ContentError(f"story[{story_id}] missing world")
        if not isinstance(stat_meta, dict):
            raise ContentError(f"story[{story_id}] missing stat_meta")
        if not isinstance(professions, list):
            raise ContentError(f"story[{story_id}] missing professions")
        if not isinstance(items, dict):
            raise ContentError(f"story[{story_id}] missing items")
        if not isinstance(statuses, dict):
            raise ContentError(f"story[{story_id}] missing statuses")
        if not isinstance(endings, dict) or not endings:
            raise ContentError(f"story[{story_id}] missing endings")
        if not isinstance(nodes, dict) or not nodes:
            raise ContentError(f"story[{story_id}] missing nodes")
        if not isinstance(encounters, dict):
            raise ContentError(f"story[{story_id}] encounters must be object")

        world.setdefault("id", story_id)
        world.setdefault("title", story_id)
        world.setdefault("chapter_title", "")
        world.setdefault("intro", "")
        world.setdefault("start_node", "arrival")
        world.setdefault("start_log", "你开始了冒险。")
        world.setdefault("default_shillings", 0)
        world.setdefault("corruption_limit", 10)
        world.setdefault("doom_texts", [])
        world.setdefault("corruption_penalties", [])

        start_node = world["start_node"]
        if start_node not in nodes:
            raise ContentError(f"story[{story_id}] start_node not found: {start_node}")

        ending_ids = [str(key) for key in endings.keys()]
        default_ending_id = str(world.get("default_ending_id") or ending_ids[0])
        if default_ending_id not in endings:
            default_ending_id = ending_ids[0]
        world["default_ending_id"] = default_ending_id

        world.setdefault(
            "fatal_rules",
            {
                "on_hp_zero": {"ending": default_ending_id, "summary": "你的生命归零。"},
                "on_corruption_limit": {"ending": default_ending_id, "summary": "腐化吞没了你的意志。"},
            },
        )

        if "resolve_victory" not in world:
            world["resolve_victory"] = {
                "default": {"ending": default_ending_id, "summary": "你完成了最终对抗。"},
                "rules": [],
            }

        # Profession normalization stays conservative on purpose: the engine
        # should reject malformed packs early instead of hiding bad data.
        normalized_professions: list[dict[str, Any]] = []
        for profession in professions:
            if not isinstance(profession, dict):
                continue
            if "id" not in profession or "name" not in profession:
                continue
            profession.setdefault("summary", "")
            profession.setdefault("max_hp", 10)
            profession.setdefault("stats", {})
            profession.setdefault("starting_items", [])
            profession.setdefault("perks", [])
            profession.setdefault("check_bonus", [])
            normalized_professions.append(profession)

        if not normalized_professions:
            raise ContentError(f"story[{story_id}] has no valid professions")

        return {
            "id": story_id,
            "world": world,
            "stat_meta": stat_meta,
            "professions": normalized_professions,
            "items": items,
            "statuses": statuses,
            "endings": endings,
            "nodes": nodes,
            "encounters": encounters,
        }

    def default_story_id(self) -> str:
        """Return the default story id used when callers omit one."""
        assert self._default_story_id is not None
        return self._default_story_id

    def get(self, story_id: str) -> dict[str, Any]:
        """Return normalized story data or raise if the id is unknown."""
        story = self._stories.get(story_id)
        if not story:
            raise KeyError(f"story_not_found:{story_id}")
        return story

    def runtime(self, story_id: str) -> StoryRuntime:
        """Return the runtime adapter for a specific story id."""
        runtime = self._runtimes.get(story_id)
        if runtime is None:
            raise KeyError(f"story_not_found:{story_id}")
        return runtime

    def default_runtime(self) -> StoryRuntime:
        """Return the runtime for the default story pack."""
        return self.runtime(self.default_story_id())

    def list_story_briefs(self) -> list[dict[str, Any]]:
        """Return lightweight metadata for story selection UIs."""
        return [self._runtimes[story_id].story_brief() for story_id in sorted(self._runtimes.keys())]

    def find_story_id_by_world_id(self, world_id: str) -> str | None:
        """Map a saved world id back to a story id when possible."""
        for story_id, runtime in self._runtimes.items():
            if runtime.world_id == world_id:
                return story_id
        return None
