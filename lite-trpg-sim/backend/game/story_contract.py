"""Canonical story DSL contract constants used by runtime and validators.

This module centralizes action/effect vocabulary so engine behavior and story
validation stay aligned. Story packs should only rely on identifiers declared
here (directly or through docs), rather than hidden hardcoded branches.
"""

from __future__ import annotations

from typing import Final

# Action kinds that can appear in `nodes.*.actions` and `encounters.*.actions`.
ACTION_KINDS: Final[tuple[str, ...]] = (
    "move",
    "story",
    "check",
    "save",
    "contest",
    "damage",
    "healing",
    "drain",
    "utility",
)
ACTION_KIND_SET: Final[frozenset[str]] = frozenset(ACTION_KINDS)

# Kinds that require a config payload object with the same semantic name.
# Example: kind=check must provide action.check as an object.
ACTION_KIND_CONFIG_KEYS: Final[dict[str, str]] = {
    "check": "check",
    "save": "save",
    "contest": "contest",
    "damage": "damage",
    "healing": "healing",
    "drain": "drain",
}

# Branches that resolve via roll-like checks with success/failure branches.
ROLL_ACTION_KINDS: Final[frozenset[str]] = frozenset({"check", "save", "contest"})

# Branches that resolve via impact pipeline (damage/heal/drain).
IMPACT_ACTION_KINDS: Final[frozenset[str]] = frozenset({"damage", "healing", "drain"})

# All recognized effect operators across story actions and passive triggers.
EFFECT_OPS: Final[frozenset[str]] = frozenset(
    {
        "goto",
        "set_flag",
        "adjust",
        "add_item",
        "remove_first_item",
        "add_status",
        "remove_status",
        "remove_self",  # passive-trigger helper (used inside trigger_effects)
        "outcome",
        "log",
        "finish",
        "finish_if",
        "resolve_victory",
        "start_encounter",
        "adjust_encounter",
        "end_encounter",
        "set_encounter_flag",
        "clear_encounter_flag",
        "adjust_enemy_hp",
        "adjust_objective",
        "adjust_environment",
        "sync_encounter_phase",
        "damage",
        "healing",
        "drain",
    }
)

# Effect ops that reuse the impact resolution pipeline.
IMPACT_EFFECT_OPS: Final[frozenset[str]] = frozenset({"damage", "healing", "drain"})

# Passive trigger timings intentionally stay small so authors can reason about
# lifecycle order without learning a large event matrix.
PASSIVE_TRIGGER_KINDS: Final[tuple[str, ...]] = (
    "before_check",
    "after_check",
    "turn_end",
)
PASSIVE_TRIGGER_SET: Final[frozenset[str]] = frozenset(PASSIVE_TRIGGER_KINDS)

# Encounter exit strategy modes.
ENCOUNTER_EXIT_MODES: Final[frozenset[str]] = frozenset({"defeat", "escape", "negotiate", "delay"})
DEFAULT_ENCOUNTER_EXIT_MODE: Final[str] = "escape"


def action_kind_supported(kind: str) -> bool:
    """Return whether one action kind belongs to the canonical contract."""
    return str(kind).strip() in ACTION_KIND_SET


def required_action_config_key(kind: str) -> str | None:
    """Return required config key for one action kind, when applicable."""
    normalized = str(kind).strip()
    return ACTION_KIND_CONFIG_KEYS.get(normalized)


def effect_op_supported(op: str) -> bool:
    """Return whether one effect op belongs to the canonical contract."""
    return str(op).strip() in EFFECT_OPS


def passive_trigger_supported(trigger: str) -> bool:
    """Return whether one passive trigger belongs to the canonical contract."""
    return str(trigger).strip() in PASSIVE_TRIGGER_SET


def normalize_encounter_exit_mode(raw_mode: str) -> str:
    """Normalize encounter-exit mode; unknown values fall back to `escape`."""
    mode = str(raw_mode).strip().lower()
    if mode in ENCOUNTER_EXIT_MODES:
        return mode
    return DEFAULT_ENCOUNTER_EXIT_MODE
