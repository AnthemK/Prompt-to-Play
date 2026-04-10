"""Story-pack validation helpers for schema and reference integrity checks.

This module stays independent from HTTP/server concerns so both CLI tools and
unit tests can reuse the same validation pipeline.
"""

from __future__ import annotations

from typing import Any

from .content import StoryRepository
from .story_contract import (
    ACTION_KIND_SET,
    ACTION_KIND_CONFIG_KEYS,
    effect_op_supported,
    passive_trigger_supported,
)


def _issue(story_id: str, path: str, code: str, message: str, *, level: str = "error") -> dict[str, str]:
    """Build one normalized validation issue object."""
    return {
        "level": level,
        "story_id": story_id,
        "path": path,
        "code": code,
        "message": message,
    }


def _iter_requirements(requirement: Any, path: str) -> list[tuple[dict[str, Any], str]]:
    """Flatten nested `requires/if` structures into atomic requirement entries."""
    if not isinstance(requirement, dict):
        return []
    result: list[tuple[dict[str, Any], str]] = []
    if isinstance(requirement.get("all"), list):
        for index, child in enumerate(requirement.get("all", [])):
            result.extend(_iter_requirements(child, f"{path}.all[{index}]"))
        return result
    if isinstance(requirement.get("any"), list):
        for index, child in enumerate(requirement.get("any", [])):
            result.extend(_iter_requirements(child, f"{path}.any[{index}]"))
        return result
    result.append((requirement, path))
    return result


def _iter_action_entries(story: dict[str, Any]) -> list[tuple[dict[str, Any], str]]:
    """Return every action object with a stable path label."""
    entries: list[tuple[dict[str, Any], str]] = []
    nodes = story.get("nodes", {})
    if isinstance(nodes, dict):
        for node_id, node in nodes.items():
            if not isinstance(node, dict):
                continue
            actions = node.get("actions", [])
            if not isinstance(actions, list):
                continue
            for index, action in enumerate(actions):
                if isinstance(action, dict):
                    entries.append((action, f"nodes.{node_id}.actions[{index}]"))

    encounters = story.get("encounters", {})
    if isinstance(encounters, dict):
        for encounter_id, encounter in encounters.items():
            if not isinstance(encounter, dict):
                continue
            actions = encounter.get("actions", [])
            if isinstance(actions, list):
                for index, action in enumerate(actions):
                    if isinstance(action, dict):
                        entries.append((action, f"encounters.{encounter_id}.actions[{index}]"))
            phases = encounter.get("phases", {})
            if isinstance(phases, dict):
                for phase_id, phase in phases.items():
                    if not isinstance(phase, dict):
                        continue
                    phase_actions = phase.get("actions", [])
                    if not isinstance(phase_actions, list):
                        continue
                    for index, action in enumerate(phase_actions):
                        if isinstance(action, dict):
                            entries.append(
                                (
                                    action,
                                    f"encounters.{encounter_id}.phases.{phase_id}.actions[{index}]",
                                )
                            )
    return entries


def _iter_effect_lists(story: dict[str, Any]) -> list[tuple[list[Any], str]]:
    """Collect all effect-list containers that may hold reference-carrying ops."""
    blocks: list[tuple[list[Any], str]] = []

    for action, action_path in _iter_action_entries(story):
        effects = action.get("effects")
        if isinstance(effects, list):
            blocks.append((effects, f"{action_path}.effects"))
        on_success = action.get("on_success", {})
        if isinstance(on_success, dict) and isinstance(on_success.get("effects"), list):
            blocks.append((on_success.get("effects", []), f"{action_path}.on_success.effects"))
        on_failure = action.get("on_failure", {})
        if isinstance(on_failure, dict) and isinstance(on_failure.get("effects"), list):
            blocks.append((on_failure.get("effects", []), f"{action_path}.on_failure.effects"))

    items = story.get("items", {})
    if isinstance(items, dict):
        for item_id, item in items.items():
            if not isinstance(item, dict):
                continue
            use_effects = item.get("use_effects")
            if isinstance(use_effects, list):
                blocks.append((use_effects, f"items.{item_id}.use_effects"))
            trigger_effects = item.get("trigger_effects")
            if isinstance(trigger_effects, list):
                blocks.append((trigger_effects, f"items.{item_id}.trigger_effects"))

    statuses = story.get("statuses", {})
    if isinstance(statuses, dict):
        for status_id, status in statuses.items():
            if not isinstance(status, dict):
                continue
            trigger_effects = status.get("trigger_effects")
            if isinstance(trigger_effects, list):
                blocks.append((trigger_effects, f"statuses.{status_id}.trigger_effects"))
            per_turn = status.get("per_turn_effects")
            if isinstance(per_turn, list):
                blocks.append((per_turn, f"statuses.{status_id}.per_turn_effects"))

    professions = story.get("professions", [])
    if isinstance(professions, list):
        for index, profession in enumerate(professions):
            if not isinstance(profession, dict):
                continue
            trigger_effects = profession.get("trigger_effects")
            if isinstance(trigger_effects, list):
                blocks.append((trigger_effects, f"professions[{index}].trigger_effects"))

    encounters = story.get("encounters", {})
    if isinstance(encounters, dict):
        for encounter_id, encounter in encounters.items():
            if not isinstance(encounter, dict):
                continue
            enemy_behaviors = encounter.get("enemy_behaviors")
            if isinstance(enemy_behaviors, list):
                for index, behavior in enumerate(enemy_behaviors):
                    if isinstance(behavior, dict) and isinstance(behavior.get("effects"), list):
                        blocks.append(
                            (
                                behavior.get("effects", []),
                                f"encounters.{encounter_id}.enemy_behaviors[{index}].effects",
                            )
                        )
            turn_rules = encounter.get("turn_rules")
            if isinstance(turn_rules, list):
                for index, rule in enumerate(turn_rules):
                    if isinstance(rule, dict) and isinstance(rule.get("effects"), list):
                        blocks.append((rule.get("effects", []), f"encounters.{encounter_id}.turn_rules[{index}].effects"))
            phase_rules = encounter.get("phase_rules")
            if isinstance(phase_rules, list):
                for index, rule in enumerate(phase_rules):
                    if isinstance(rule, dict) and isinstance(rule.get("effects"), list):
                        blocks.append((rule.get("effects", []), f"encounters.{encounter_id}.phase_rules[{index}].effects"))
            exit_strategies = encounter.get("exit_strategies")
            if isinstance(exit_strategies, list):
                for index, strategy in enumerate(exit_strategies):
                    if isinstance(strategy, dict) and isinstance(strategy.get("effects"), list):
                        blocks.append(
                            (
                                strategy.get("effects", []),
                                f"encounters.{encounter_id}.exit_strategies[{index}].effects",
                            )
                        )
            phases = encounter.get("phases")
            if isinstance(phases, dict):
                for phase_id, phase in phases.items():
                    if not isinstance(phase, dict):
                        continue
                    phase_behaviors = phase.get("enemy_behaviors")
                    if isinstance(phase_behaviors, list):
                        for index, behavior in enumerate(phase_behaviors):
                            if isinstance(behavior, dict) and isinstance(behavior.get("effects"), list):
                                blocks.append(
                                    (
                                        behavior.get("effects", []),
                                        f"encounters.{encounter_id}.phases.{phase_id}.enemy_behaviors[{index}].effects",
                                    )
                                )

    return blocks


def _iter_trigger_effect_entries(story: dict[str, Any]) -> list[tuple[dict[str, Any], str]]:
    """Return configured passive trigger effects with stable paths."""
    entries: list[tuple[dict[str, Any], str]] = []

    for effect_list, list_path in _iter_effect_lists(story):
        if not list_path.endswith("trigger_effects"):
            continue
        for index, effect in enumerate(effect_list):
            if isinstance(effect, dict):
                entries.append((effect, f"{list_path}[{index}]"))

    return entries


def _validate_action_shapes(story: dict[str, Any], story_id: str) -> list[dict[str, str]]:
    """Validate action-kind correctness and required config object presence."""
    issues: list[dict[str, str]] = []
    seen_action_ids: dict[str, str] = {}
    for action, action_path in _iter_action_entries(story):
        action_id = str(action.get("id", "")).strip()
        if not action_id:
            issues.append(_issue(story_id, action_path, "ACTION_ID_MISSING", "action.id 不能为空"))
        else:
            previous = seen_action_ids.get(action_id)
            if previous:
                issues.append(
                    _issue(
                        story_id,
                        action_path,
                        "ACTION_ID_DUPLICATE",
                        f"action.id={action_id!r} 重复，首次出现在 {previous}",
                    )
                )
            else:
                seen_action_ids[action_id] = action_path

        kind = str(action.get("kind", "story")).strip()
        if kind not in ACTION_KIND_SET:
            issues.append(_issue(story_id, f"{action_path}.kind", "ACTION_KIND_INVALID", f"未知 action.kind={kind!r}"))
            continue

        cfg_key = ACTION_KIND_CONFIG_KEYS.get(kind)
        if cfg_key and not isinstance(action.get(cfg_key), dict):
            issues.append(
                _issue(
                    story_id,
                    f"{action_path}.{cfg_key}",
                    "ACTION_CONFIG_MISSING",
                    f"kind={kind!r} 时必须提供对象字段 {cfg_key!r}",
                )
            )

        for req, req_path in _iter_requirements(action.get("requires"), f"{action_path}.requires"):
            item_id = req.get("item")
            if isinstance(item_id, str) and item_id and item_id not in story.get("items", {}):
                issues.append(
                    _issue(
                        story_id,
                        req_path,
                        "REQUIRE_ITEM_MISSING",
                        f"requires 引用了不存在的 item: {item_id!r}",
                    )
                )
            status_id = req.get("status")
            if isinstance(status_id, str) and status_id and status_id not in story.get("statuses", {}):
                issues.append(
                    _issue(
                        story_id,
                        req_path,
                        "REQUIRE_STATUS_MISSING",
                        f"requires 引用了不存在的 status: {status_id!r}",
                    )
                )

    return issues


def _iter_skill_configs(action: dict[str, Any], action_path: str) -> list[tuple[str, dict[str, Any]]]:
    """Return every action config block that may legally declare a skill."""
    entries: list[tuple[str, dict[str, Any]]] = []
    for key in ("check", "save", "contest"):
        cfg = action.get(key)
        if isinstance(cfg, dict):
            entries.append((f"{action_path}.{key}", cfg))
    return entries


def _validate_skill_references(story: dict[str, Any], story_id: str) -> list[dict[str, str]]:
    """Validate optional skill-layer declarations without forcing story adoption."""
    issues: list[dict[str, str]] = []
    skill_meta = story.get("skill_meta", {})
    if not isinstance(skill_meta, dict):
        issues.append(_issue(story_id, "skill_meta", "SKILL_META_INVALID", "skill_meta 必须是对象"))
        return issues

    known_skills = {str(skill_id) for skill_id in skill_meta.keys()}

    for profession_index, profession in enumerate(story.get("professions", [])):
        if not isinstance(profession, dict):
            continue
        skills = profession.get("skills", {})
        if skills is None:
            continue
        if not isinstance(skills, dict):
            issues.append(
                _issue(
                    story_id,
                    f"professions[{profession_index}].skills",
                    "PROFESSION_SKILLS_INVALID",
                    "profession.skills 必须是对象",
                )
            )
            continue
        for skill_id in skills.keys():
            if str(skill_id) not in known_skills:
                issues.append(
                    _issue(
                        story_id,
                        f"professions[{profession_index}].skills.{skill_id}",
                        "SKILL_MISSING",
                        f"profession.skills 引用了不存在的 skill: {skill_id!r}",
                    )
                )

    for action, action_path in _iter_action_entries(story):
        for cfg_path, cfg in _iter_skill_configs(action, action_path):
            skill_id = str(cfg.get("skill", "")).strip()
            if skill_id and skill_id not in known_skills:
                issues.append(
                    _issue(
                        story_id,
                        f"{cfg_path}.skill",
                        "SKILL_MISSING",
                        f"action skill 引用了不存在的 skill: {skill_id!r}",
                    )
                )

    return issues


def _validate_status_condition_references(story: dict[str, Any], story_id: str) -> list[dict[str, str]]:
    """Validate status-aware check/save/contest config references."""
    issues: list[dict[str, str]] = []
    statuses = story.get("statuses", {})

    for action, action_path in _iter_action_entries(story):
        for cfg_path, cfg in _iter_skill_configs(action, action_path):
            for field_name in ("extra_bonus_if_statuses", "dc_adjust_if_statuses"):
                entries = cfg.get(field_name)
                if not isinstance(entries, list):
                    continue
                for index, entry in enumerate(entries):
                    if not isinstance(entry, dict):
                        continue
                    status_id = str(entry.get("status", "")).strip()
                    if status_id and status_id not in statuses:
                        issues.append(
                            _issue(
                                story_id,
                                f"{cfg_path}.{field_name}[{index}].status",
                                "STATUS_MISSING",
                                f"{field_name} 引用了不存在的 status: {status_id!r}",
                            )
                        )

    return issues


def _validate_effect_lifecycle_fields(story: dict[str, Any], story_id: str) -> list[dict[str, str]]:
    """Validate lightweight duration fields for story-defined status flows."""
    issues: list[dict[str, str]] = []

    statuses = story.get("statuses", {})
    if isinstance(statuses, dict):
        for status_id, status in statuses.items():
            if not isinstance(status, dict):
                continue
            default_duration = status.get("default_duration_turns")
            if default_duration is None:
                continue
            if not isinstance(default_duration, int) or int(default_duration) <= 0:
                issues.append(
                    _issue(
                        story_id,
                        f"statuses.{status_id}.default_duration_turns",
                        "STATUS_DURATION_INVALID",
                        "default_duration_turns 必须是正整数",
                    )
                )

    for effect_list, list_path in _iter_effect_lists(story):
        for index, effect in enumerate(effect_list):
            if not isinstance(effect, dict):
                continue
            if str(effect.get("op", "")).strip() != "add_status":
                continue
            duration_turns = effect.get("duration_turns")
            if duration_turns is None:
                continue
            if not isinstance(duration_turns, int) or int(duration_turns) <= 0:
                issues.append(
                    _issue(
                        story_id,
                        f"{list_path}[{index}].duration_turns",
                        "STATUS_DURATION_INVALID",
                        "add_status.duration_turns 必须是正整数",
                    )
                )

    for effect, effect_path in _iter_trigger_effect_entries(story):
        trigger = str(effect.get("trigger", "")).strip()
        if not trigger:
            issues.append(
                _issue(
                    story_id,
                    f"{effect_path}.trigger",
                    "TRIGGER_MISSING",
                    "trigger_effects[*].trigger 不能为空",
                )
            )
            continue
        if not passive_trigger_supported(trigger):
            issues.append(
                _issue(
                    story_id,
                    f"{effect_path}.trigger",
                    "TRIGGER_INVALID",
                    f"未知 passive trigger: {trigger!r}",
                )
            )

    return issues


def _validate_core_references(story: dict[str, Any], story_id: str) -> list[dict[str, str]]:
    """Validate known identifier references across world/actions/effects."""
    issues: list[dict[str, str]] = []
    nodes = story.get("nodes", {})
    endings = story.get("endings", {})
    items = story.get("items", {})
    statuses = story.get("statuses", {})
    encounters = story.get("encounters", {})
    world = story.get("world", {})

    for profession_index, profession in enumerate(story.get("professions", [])):
        if not isinstance(profession, dict):
            continue
        for item_index, item_id in enumerate(profession.get("starting_items", [])):
            if isinstance(item_id, str) and item_id and item_id not in items:
                issues.append(
                    _issue(
                        story_id,
                        f"professions[{profession_index}].starting_items[{item_index}]",
                        "STARTING_ITEM_MISSING",
                        f"profession 起始物品不存在: {item_id!r}",
                    )
                )

    fatal_rules = world.get("fatal_rules", {})
    if isinstance(fatal_rules, dict):
        for key, rule in fatal_rules.items():
            if not isinstance(rule, dict):
                continue
            ending_id = str(rule.get("ending", "")).strip()
            if ending_id and ending_id not in endings:
                issues.append(
                    _issue(
                        story_id,
                        f"world.fatal_rules.{key}.ending",
                        "ENDING_MISSING",
                        f"fatal_rules 引用了不存在的 ending: {ending_id!r}",
                    )
                )

    resolve_victory = world.get("resolve_victory", {})
    if isinstance(resolve_victory, dict):
        default = resolve_victory.get("default")
        if isinstance(default, dict):
            ending_id = str(default.get("ending", "")).strip()
            if ending_id and ending_id not in endings:
                issues.append(
                    _issue(
                        story_id,
                        "world.resolve_victory.default.ending",
                        "ENDING_MISSING",
                        f"resolve_victory.default 引用了不存在的 ending: {ending_id!r}",
                    )
                )
        rules = resolve_victory.get("rules", [])
        if isinstance(rules, list):
            for index, rule in enumerate(rules):
                if not isinstance(rule, dict):
                    continue
                result = rule.get("result")
                if not isinstance(result, dict):
                    continue
                ending_id = str(result.get("ending", "")).strip()
                if ending_id and ending_id not in endings:
                    issues.append(
                        _issue(
                            story_id,
                            f"world.resolve_victory.rules[{index}].result.ending",
                            "ENDING_MISSING",
                            f"resolve_victory.rules[{index}] 引用了不存在的 ending: {ending_id!r}",
                        )
                    )

    for encounter_id, encounter in encounters.items():
        if not isinstance(encounter, dict):
            continue
        phases = encounter.get("phases", {})
        if isinstance(phases, dict):
            start_phase = str(encounter.get("start_phase", "")).strip()
            if start_phase and start_phase not in phases:
                issues.append(
                    _issue(
                        story_id,
                        f"encounters.{encounter_id}.start_phase",
                        "PHASE_MISSING",
                        f"start_phase 引用了不存在的 phase: {start_phase!r}",
                    )
                )
            phase_rules = encounter.get("phase_rules", [])
            if isinstance(phase_rules, list):
                for index, rule in enumerate(phase_rules):
                    if not isinstance(rule, dict):
                        continue
                    target_phase = str(rule.get("phase", "")).strip()
                    if target_phase and target_phase not in phases:
                        issues.append(
                            _issue(
                                story_id,
                                f"encounters.{encounter_id}.phase_rules[{index}].phase",
                                "PHASE_MISSING",
                                f"phase_rules 引用了不存在的 phase: {target_phase!r}",
                            )
                        )

    for effect_list, list_path in _iter_effect_lists(story):
        for index, effect in enumerate(effect_list):
            if not isinstance(effect, dict):
                continue
            op = str(effect.get("op", "")).strip()
            effect_path = f"{list_path}[{index}]"
            if not op:
                issues.append(_issue(story_id, f"{effect_path}.op", "EFFECT_OP_MISSING", "effect.op 不能为空"))
                continue
            if not effect_op_supported(op):
                issues.append(_issue(story_id, f"{effect_path}.op", "EFFECT_OP_INVALID", f"未知 effect.op={op!r}"))
                continue

            if op == "goto":
                node_id = str(effect.get("node", "")).strip()
                if node_id and node_id not in nodes:
                    issues.append(_issue(story_id, f"{effect_path}.node", "NODE_MISSING", f"goto 引用了不存在的 node: {node_id!r}"))
                continue

            if op in {"finish", "finish_if"}:
                ending_id = str(effect.get("ending", "")).strip()
                if ending_id and ending_id not in endings:
                    issues.append(
                        _issue(story_id, f"{effect_path}.ending", "ENDING_MISSING", f"{op} 引用了不存在的 ending: {ending_id!r}")
                    )
                continue

            if op == "add_item":
                item_id = str(effect.get("item", "")).strip()
                if item_id and item_id not in items:
                    issues.append(_issue(story_id, f"{effect_path}.item", "ITEM_MISSING", f"add_item 引用了不存在的 item: {item_id!r}"))
                continue

            if op == "remove_first_item":
                for item_index, item_id in enumerate(effect.get("items", [])):
                    if isinstance(item_id, str) and item_id and item_id not in items:
                        issues.append(
                            _issue(
                                story_id,
                                f"{effect_path}.items[{item_index}]",
                                "ITEM_MISSING",
                                f"remove_first_item 引用了不存在的 item: {item_id!r}",
                            )
                        )
                continue

            if op in {"add_status", "remove_status"}:
                status_id = str(effect.get("status", "")).strip()
                if status_id and status_id not in statuses:
                    issues.append(
                        _issue(
                            story_id,
                            f"{effect_path}.status",
                            "STATUS_MISSING",
                            f"{op} 引用了不存在的 status: {status_id!r}",
                        )
                    )
                continue

            if op == "start_encounter":
                encounter_id = str(effect.get("encounter", "")).strip()
                if encounter_id and encounter_id not in encounters:
                    issues.append(
                        _issue(
                            story_id,
                            f"{effect_path}.encounter",
                            "ENCOUNTER_MISSING",
                            f"start_encounter 引用了不存在的 encounter: {encounter_id!r}",
                        )
                    )
                continue

    return issues


def validate_story(story: dict[str, Any]) -> list[dict[str, str]]:
    """Validate one normalized story object and return issue list."""
    story_id = str(story.get("id", "unknown_story"))
    issues: list[dict[str, str]] = []
    issues.extend(_validate_action_shapes(story, story_id))
    issues.extend(_validate_skill_references(story, story_id))
    issues.extend(_validate_status_condition_references(story, story_id))
    issues.extend(_validate_effect_lifecycle_fields(story, story_id))
    issues.extend(_validate_core_references(story, story_id))
    return issues


def validate_repository(repository: StoryRepository, *, story_id: str | None = None) -> list[dict[str, str]]:
    """Validate one or all story packs loaded in a repository."""
    if story_id:
        story_ids = [story_id]
    else:
        story_ids = sorted([entry["id"] for entry in repository.list_story_briefs()])

    issues: list[dict[str, str]] = []
    for active_story_id in story_ids:
        story = repository.get(active_story_id)
        issues.extend(validate_story(story))
    return issues
