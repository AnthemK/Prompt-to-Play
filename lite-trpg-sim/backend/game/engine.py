"""Session and save orchestration for the game backend.

`GameEngine` should stay story-agnostic: it owns in-memory sessions, delegates
story-specific work to `StoryRuntime`, and produces a stable view payload for
the frontend.
"""

from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .content import StoryRepository
from .rules import debug_event, ensure_debug_trace
from .story_interface import StoryRuntime

SAVE_SCHEMA_VERSION = 3


class GameEngine:
    """Coordinate story runtimes, sessions, and save/load behavior."""

    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}
        self.repository = StoryRepository()

    def _create_session_id(self) -> str:
        """Create a short local session id suitable for API paths."""
        return uuid.uuid4().hex[:10]

    def _runtime_for_story(self, story_id: str) -> StoryRuntime:
        """Resolve a story id to its runtime adapter."""
        return self.repository.runtime(story_id)

    def _state_or_error(self, session_id: str) -> dict[str, Any]:
        """Fetch a session state or raise the API-facing not-found error."""
        state = self.sessions.get(session_id)
        if not state:
            raise KeyError("session_not_found")
        return state

    def _story_id_from_save(self, save_data: dict[str, Any]) -> str:
        """Infer which story pack should own a loaded save snapshot."""
        story_id = save_data.get("story_id")
        if isinstance(story_id, str) and story_id.strip():
            return story_id

        raw_state = save_data.get("state")
        if isinstance(raw_state, dict):
            state_story_id = raw_state.get("story_id")
            if isinstance(state_story_id, str) and state_story_id.strip():
                return state_story_id

        world_id = save_data.get("world_id")
        if isinstance(world_id, str) and world_id.strip():
            mapped = self.repository.find_story_id_by_world_id(world_id)
            if mapped:
                return mapped

        return self.repository.default_story_id()

    def meta(self, story_id: str | None = None) -> dict[str, Any]:
        """Return story metadata for the setup screen."""
        active_story_id = story_id or self.repository.default_story_id()
        runtime = self._runtime_for_story(active_story_id)
        payload = runtime.meta_payload()

        return {
            "default_story_id": self.repository.default_story_id(),
            "active_story_id": active_story_id,
            "stories": self.repository.list_story_briefs(),
            **payload,
        }

    def new_game(self, player_name: str, profession_id: str, story_id: str | None = None) -> dict[str, Any]:
        """Create a new session and immediately return its rendered view."""
        chosen_story_id = story_id or self.repository.default_story_id()
        runtime = self._runtime_for_story(chosen_story_id)

        session_id = self._create_session_id()
        state = runtime.create_new_state(session_id, player_name, profession_id, SAVE_SCHEMA_VERSION)
        ensure_debug_trace(state)
        debug_event(
            state,
            event="session.created",
            message="Created new game session.",
            payload={
                "session_id": session_id,
                "story_id": chosen_story_id,
                "profession_id": profession_id,
            },
        )
        self.sessions[session_id] = state
        return self.view(session_id)

    def view(self, session_id: str) -> dict[str, Any]:
        """Project one session state into the frontend's view model."""
        runtime_state = self._state_or_error(session_id)
        story_id = str(runtime_state.get("story_id") or self.repository.default_story_id())
        runtime = self._runtime_for_story(story_id)

        scene_view = runtime.scene_view(runtime_state)

        player = runtime_state["player"]
        return {
            "session_id": session_id,
            "story_id": story_id,
            "world": runtime.world_view(),
            "scene": scene_view,
            "player": {
                "name": player["name"],
                "profession_id": player["profession_id"],
                "profession_name": player["profession_name"],
                "stats": player["stats"],
                "hp": player["hp"],
                "max_hp": player["max_hp"],
                "shield": int(player.get("shield", 0)),
                "corruption": player["corruption"],
                "corruption_limit": runtime.corruption_limit(),
                "shillings": player["shillings"],
            },
            "inventory": runtime.inventory_view(runtime_state),
            "statuses": runtime.statuses_view(runtime_state),
            "encounter": copy.deepcopy(runtime_state.get("encounter")),
            "progress": {
                "doom": runtime_state["progress"]["doom"],
                "turns": runtime_state["progress"]["turns"],
                "node_id": runtime_state["progress"]["node_id"],
            },
            "recent_log": runtime_state["log"][-12:],
            "last_outcome": runtime_state.get("last_outcome"),
            "game_over": runtime_state.get("game_over", False),
            "ending": runtime_state.get("ending"),
        }

    def act(self, session_id: str, action_id: str) -> dict[str, Any]:
        """Execute one action against a session and return the updated view."""
        state = self._state_or_error(session_id)
        story_id = str(state.get("story_id") or self.repository.default_story_id())
        runtime = self._runtime_for_story(story_id)
        debug_event(
            state,
            event="action.received",
            message="Engine received one action request.",
            payload={"session_id": session_id, "action_id": action_id},
        )
        runtime.apply_action(state, action_id)
        return self.view(session_id)

    def save(self, session_id: str) -> dict[str, Any]:
        """Serialize a session into the backend-owned save format."""
        state = self._state_or_error(session_id)
        story_id = str(state.get("story_id") or self.repository.default_story_id())
        runtime = self._runtime_for_story(story_id)
        return {
            "schema_version": SAVE_SCHEMA_VERSION,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "story_id": story_id,
            "world_id": runtime.world_id,
            "state": copy.deepcopy(state),
        }

    def load(self, save_data: dict[str, Any]) -> dict[str, Any]:
        """Load a save snapshot into a fresh in-memory session."""
        if not isinstance(save_data, dict):
            raise ValueError("invalid_save")

        schema_version = int(save_data.get("schema_version", 0))
        if schema_version not in (1, 2, SAVE_SCHEMA_VERSION):
            raise ValueError("unsupported_save_version")

        raw_state = save_data.get("state")
        if not isinstance(raw_state, dict):
            raise ValueError("invalid_save")

        story_id = self._story_id_from_save(save_data)
        runtime = self._runtime_for_story(story_id)

        # Round-trip through JSON to avoid sharing references from imported data.
        state = json.loads(json.dumps(raw_state, ensure_ascii=False))
        session_id = self._create_session_id()
        state["session_id"] = session_id
        state["story_id"] = story_id
        runtime.repair_loaded_state(state, SAVE_SCHEMA_VERSION)
        ensure_debug_trace(state)
        debug_event(
            state,
            event="session.loaded",
            message="Loaded save into a new in-memory session.",
            payload={"session_id": session_id, "story_id": story_id},
        )

        self.sessions[session_id] = state
        return self.view(session_id)

    def debug_trace(self, session_id: str, limit: int = 200) -> dict[str, Any]:
        """Return backend-only debug trace entries for diagnostics."""
        state = self._state_or_error(session_id)
        trace = ensure_debug_trace(state)
        safe_limit = max(1, min(2000, int(limit)))
        entries = [entry for entry in trace.get("entries", []) if isinstance(entry, dict)]
        return {
            "session_id": session_id,
            "story_id": str(state.get("story_id") or self.repository.default_story_id()),
            "node_id": str(state.get("progress", {}).get("node_id", "")),
            "turns": int(state.get("progress", {}).get("turns", 0)),
            "total_entries": len(entries),
            "entries": entries[-safe_limit:],
        }

    def delete(self, session_id: str) -> None:
        """Delete a session if it exists."""
        self.sessions.pop(session_id, None)
