"""Concrete `StoryRuntime` backed by normalized story-pack data."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from .adventure import StoryDirector
from .rules import get_profession, inventory_view, statuses_view
from .story_interface import StoryRuntime


class StoryPackRuntime(StoryRuntime):
    """Run one JSON/YAML story pack through the common engine contract."""

    def __init__(self, content: dict[str, Any]) -> None:
        self.content = content
        self.director = StoryDirector(content)

    @property
    def story_id(self) -> str:
        """Return the stable id of the mounted story pack."""
        return str(self.content.get("id", ""))

    @property
    def world_id(self) -> str:
        """Return the world identifier exposed in saves and views."""
        return str(self.content.get("world", {}).get("id", self.story_id))

    def story_brief(self) -> dict[str, Any]:
        """Return the short descriptor used by the setup overlay."""
        world = self.content.get("world", {})
        return {
            "id": self.story_id,
            "world_id": self.world_id,
            "title": world.get("title", self.story_id),
            "chapter_title": world.get("chapter_title", ""),
            "intro": world.get("intro", ""),
            "tone": world.get("tone", ""),
            "story_interface_version": str(self.content.get("story_interface_version", "1.1")),
            "capabilities": copy.deepcopy(self.content.get("capabilities", {})),
        }

    def meta_payload(self) -> dict[str, Any]:
        """Return setup-time metadata consumed by the frontend."""
        return {
            "world": self.content["world"],
            "stats": self.content["stat_meta"],
            "professions": self.content["professions"],
            "items": self.content["items"],
            "story_interface_version": str(self.content.get("story_interface_version", "1.1")),
            "capabilities": copy.deepcopy(self.content.get("capabilities", {})),
        }

    def _initial_inventory(self, profession: dict[str, Any]) -> dict[str, int]:
        """Expand a profession's starting item list into quantity counts."""
        inventory: dict[str, int] = {}
        for item_id in profession.get("starting_items", []):
            item_key = str(item_id)
            if not item_key:
                continue
            inventory[item_key] = int(inventory.get(item_key, 0)) + 1
        return inventory

    def create_new_state(self, session_id: str, player_name: str, profession_id: str, schema_version: int) -> dict[str, Any]:
        """Create a brand-new runtime state for one player run."""
        profession = get_profession(self.content, profession_id)
        if profession is None:
            raise ValueError("invalid_profession")

        clean_name = (player_name or "无名旅人").strip()[:24]
        if not clean_name:
            clean_name = "无名旅人"

        world = self.content.get("world", {})
        max_hp = int(profession.get("max_hp", 10))

        return {
            "schema_version": schema_version,
            "session_id": session_id,
            "story_id": self.story_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "player": {
                "name": clean_name,
                "profession_id": profession["id"],
                "profession_name": profession["name"],
                "stats": copy.deepcopy(profession.get("stats", {})),
                "max_hp": max_hp,
                "hp": max_hp,
                "shield": 0,
                "corruption": 0,
                "shillings": int(world.get("default_shillings", 0)),
                "inventory": self._initial_inventory(profession),
                "statuses": [],
            },
            "progress": {
                "chapter": str(world.get("chapter_title", "")),
                "node_id": str(world.get("start_node", "arrival")),
                "doom": 0,
                "turns": 0,
                "flags": {},
            },
            "log": [str(world.get("start_log", "你开始了冒险。"))],
            "encounter": None,
            "last_outcome": None,
            "game_over": False,
            "ending": None,
            "debug_trace": {
                "enabled": bool(world.get("debug_trace_enabled", True)),
                "max_entries": max(50, int(world.get("debug_trace_limit", 400))),
                "entries": [],
            },
        }

    def repair_loaded_state(self, state: dict[str, Any], schema_version: int) -> None:
        """Repair missing fields when loading older or external saves."""
        state.setdefault("schema_version", schema_version)
        state["story_id"] = self.story_id

        player = state.setdefault("player", {})
        progress = state.setdefault("progress", {})

        player.setdefault("name", "无名旅人")
        player.setdefault("profession_id", "")
        player.setdefault("profession_name", "")
        player.setdefault("stats", {})
        player.setdefault("max_hp", 10)
        player.setdefault("hp", player.get("max_hp", 10))
        player.setdefault("shield", 0)
        player.setdefault("corruption", 0)
        player.setdefault("shillings", int(self.content.get("world", {}).get("default_shillings", 0)))
        player.setdefault("inventory", {})
        player.setdefault("statuses", [])

        progress.setdefault("chapter", str(self.content.get("world", {}).get("chapter_title", "")))
        progress.setdefault("node_id", str(self.content.get("world", {}).get("start_node", "arrival")))
        progress.setdefault("doom", 0)
        progress.setdefault("turns", 0)
        progress.setdefault("flags", {})

        state.setdefault("log", [])
        state.setdefault("encounter", None)
        state.setdefault("last_outcome", None)
        state.setdefault("game_over", False)
        state.setdefault("ending", None)
        state.setdefault(
            "debug_trace",
            {
                "enabled": bool(self.content.get("world", {}).get("debug_trace_enabled", True)),
                "max_entries": max(50, int(self.content.get("world", {}).get("debug_trace_limit", 400))),
                "entries": [],
            },
        )

    def world_view(self) -> dict[str, Any]:
        """Return the frontend header fields for the current world."""
        world = self.content.get("world", {})
        return {
            "id": world.get("id", self.story_id),
            "title": world.get("title", self.story_id),
            "chapter_title": world.get("chapter_title", ""),
            "intro": world.get("intro", ""),
            "tone": world.get("tone", ""),
        }

    def corruption_limit(self) -> int:
        """Expose the configured corruption limit for the active story."""
        return int(self.content.get("world", {}).get("corruption_limit", 10))

    def scene_view(self, state: dict[str, Any]) -> dict[str, Any]:
        """Return either the ending scene or the active node scene."""
        if state.get("game_over") and state.get("ending"):
            ending = state["ending"]
            return {
                "id": "ending",
                "title": ending.get("title", "结局"),
                "text": ending.get("text", ""),
                "actions": [],
            }
        return self.director.scene_view(state)

    def apply_action(self, state: dict[str, Any], action_id: str) -> None:
        """Delegate action execution to the shared story director."""
        self.director.apply_action(state, action_id)

    def inventory_view(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        """Return a normalized list of inventory items for the frontend."""
        return inventory_view(state, self.content)

    def statuses_view(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        """Return a normalized list of statuses for the frontend."""
        return statuses_view(state, self.content)
