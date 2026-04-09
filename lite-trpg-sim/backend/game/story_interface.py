"""Abstract runtime contract between the engine and a story implementation.

The engine should only depend on this interface. Concrete story runtimes can be
JSON/YAML driven, database driven, or generated in other ways as long as they
produce the same behaviors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StoryRuntime(ABC):
    """Minimal runtime surface required by `GameEngine`."""

    @property
    @abstractmethod
    def story_id(self) -> str:
        """Return the stable story-pack id used by saves and the frontend."""
        raise NotImplementedError

    @property
    @abstractmethod
    def world_id(self) -> str:
        """Return the world id exposed to the player-facing view layer."""
        raise NotImplementedError

    @abstractmethod
    def story_brief(self) -> dict[str, Any]:
        """Return the lightweight metadata shown in the story selector."""
        raise NotImplementedError

    @abstractmethod
    def meta_payload(self) -> dict[str, Any]:
        """Return world/profession/item metadata needed before a run starts."""
        raise NotImplementedError

    @abstractmethod
    def create_new_state(self, session_id: str, player_name: str, profession_id: str, schema_version: int) -> dict[str, Any]:
        """Build a brand-new state snapshot for a new session."""
        raise NotImplementedError

    @abstractmethod
    def repair_loaded_state(self, state: dict[str, Any], schema_version: int) -> None:
        """Repair an old or partial state so the active engine can run it."""
        raise NotImplementedError

    @abstractmethod
    def world_view(self) -> dict[str, Any]:
        """Return the player-facing world header data."""
        raise NotImplementedError

    @abstractmethod
    def corruption_limit(self) -> int:
        """Return the resource cap for corruption-like failure pressure."""
        raise NotImplementedError

    @abstractmethod
    def scene_view(self, state: dict[str, Any]) -> dict[str, Any]:
        """Render the current story state into a frontend-friendly scene view."""
        raise NotImplementedError

    @abstractmethod
    def apply_action(self, state: dict[str, Any], action_id: str) -> None:
        """Mutate the current state by executing one player action."""
        raise NotImplementedError

    @abstractmethod
    def inventory_view(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        """Return a normalized list view of inventory entries."""
        raise NotImplementedError

    @abstractmethod
    def statuses_view(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        """Return a normalized list view of active statuses."""
        raise NotImplementedError
