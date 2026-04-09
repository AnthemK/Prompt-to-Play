"""Core rules helpers shared by all story packs.

This module contains the generic, topic-agnostic mechanics layer: resource
changes, passive effects, check math, and lightweight inventory/status helpers.
Story packs feed data into these helpers instead of re-implementing rules.
"""

from __future__ import annotations

import random
from typing import Any

from .resolution import (
    add_damage_effect,
    add_flag_effect,
    add_item_effect,
    add_resource_effect,
    add_status_effect,
    build_resolution,
)


def stat_modifier(value: int) -> int:
    """Convert a raw attribute score into the current lightweight modifier."""
    return int(value) - 2


def get_profession(content: dict[str, Any], profession_id: str) -> dict[str, Any] | None:
    """Look up one profession entry by id."""
    for profession in content.get("professions", []):
        if profession.get("id") == profession_id:
            return profession
    return None


def has_item(state: dict[str, Any], item_id: str) -> bool:
    """Return whether the player currently owns at least one item."""
    return int(state["player"]["inventory"].get(item_id, 0)) > 0


def add_item(state: dict[str, Any], item_id: str, qty: int = 1) -> None:
    """Add an item stack to the player's inventory."""
    if qty <= 0:
        return
    inventory = state["player"]["inventory"]
    inventory[item_id] = int(inventory.get(item_id, 0)) + qty


def remove_item(state: dict[str, Any], item_id: str, qty: int = 1) -> bool:
    """Remove items from inventory and report whether anything was spent."""
    inventory = state["player"]["inventory"]
    current = int(inventory.get(item_id, 0))
    if current <= 0:
        return False
    left = current - max(1, qty)
    if left <= 0:
        inventory.pop(item_id, None)
    else:
        inventory[item_id] = left
    return True


def has_status(state: dict[str, Any], status_id: str) -> bool:
    """Return whether a status is currently active."""
    return status_id in state["player"]["statuses"]


def add_status(state: dict[str, Any], status_id: str) -> None:
    """Append a status if it is not already present."""
    statuses = state["player"]["statuses"]
    if status_id not in statuses:
        statuses.append(status_id)


def remove_status(state: dict[str, Any], status_id: str) -> None:
    """Remove all copies of one status id from the player state."""
    statuses = state["player"]["statuses"]
    state["player"]["statuses"] = [entry for entry in statuses if entry != status_id]


def adjust_resource(state: dict[str, Any], content: dict[str, Any], resource: str, amount: int) -> int:
    """Apply a clamped resource delta and return the actual change applied."""
    if resource == "hp":
        player = state["player"]
        before = int(player["hp"])
        player["hp"] = max(0, min(int(player["max_hp"]), before + int(amount)))
        return int(player["hp"]) - before

    if resource == "corruption":
        player = state["player"]
        limit = int(content.get("world", {}).get("corruption_limit", 10))
        before = int(player["corruption"])
        player["corruption"] = max(0, min(limit, before + int(amount)))
        return int(player["corruption"]) - before

    if resource == "doom":
        progress = state["progress"]
        before = int(progress["doom"])
        progress["doom"] = max(0, min(99, before + int(amount)))
        return int(progress["doom"]) - before

    if resource == "shillings":
        player = state["player"]
        before = int(player["shillings"])
        player["shillings"] = max(0, before + int(amount))
        return int(player["shillings"]) - before

    return 0


def log_event(state: dict[str, Any], entry: str) -> None:
    """Append one log line and keep only the most recent history."""
    logs = state["log"]
    logs.append(entry)
    if len(logs) > 120:
        state["log"] = logs[-120:]


def _entry_name(entry: dict[str, Any], fallback: str) -> str:
    """Resolve a display name for a content entry."""
    return str(entry.get("name", fallback))


def _effect_source_name(kind: str, entry: dict[str, Any], fallback: str) -> str:
    """Build a human-readable source label for passive effects."""
    label = {
        "profession": "职业",
        "item": "装备",
        "status": "状态",
    }.get(kind, "效果")
    return f"{label}：{_entry_name(entry, fallback)}"


def _trigger_effect_matches(effect: dict[str, Any], ctx: dict[str, Any]) -> bool:
    """Return whether a passive effect's `match` clause applies right now."""
    match = effect.get("match")
    if not isinstance(match, dict):
        return True

    if "success" in match and bool(ctx.get("success")) != bool(match.get("success")):
        return False

    if "stat" in match and str(ctx.get("stat", "")) != str(match.get("stat", "")):
        return False

    stat_in = match.get("stat_in")
    if isinstance(stat_in, list) and stat_in:
        if str(ctx.get("stat", "")) not in {str(value) for value in stat_in}:
            return False

    if "kind" in match and str(ctx.get("kind", "")) != str(match.get("kind", "")):
        return False

    tags = {str(tag) for tag in ctx.get("tags", []) if isinstance(tag, str)}

    tags_any = match.get("tags_any")
    if isinstance(tags_any, list) and tags_any:
        if not ({str(tag) for tag in tags_any} & tags):
            return False

    tags_all = match.get("tags_all")
    if isinstance(tags_all, list) and tags_all:
        if not ({str(tag) for tag in tags_all} <= tags):
            return False

    return True


def apply_state_effect(
    state: dict[str, Any],
    content: dict[str, Any],
    effect: dict[str, Any],
    *,
    resolution: dict[str, Any] | None = None,
    default_source: str = "系统效果",
) -> bool:
    """Apply one generic effect op to state.

    Returns `True` when the operation was recognized by the rules layer, even if
    it ended up being a no-op because the effect was redundant.
    """
    op = str(effect.get("op", ""))
    source = str(effect.get("source", default_source))

    if op == "set_flag":
        flag = str(effect.get("flag", "")).strip()
        if not flag:
            return True
        value = bool(effect.get("value", True))
        state["progress"].setdefault("flags", {})[flag] = value
        add_flag_effect(resolution, flag=flag, value=value, source=source)
        return True

    if op == "adjust":
        resource = str(effect.get("resource", ""))
        delta = adjust_resource(state, content, resource, int(effect.get("amount", 0)))
        add_resource_effect(resolution, resource, delta, source)
        return True

    if op == "add_status":
        status_id = str(effect.get("status", "")).strip()
        if not status_id or has_status(state, status_id):
            return True
        add_status(state, status_id)
        status_name = _entry_name(content.get("statuses", {}).get(status_id, {}), status_id)
        add_status_effect(resolution, mode="add", status_id=status_id, name=status_name, source=source)
        return True

    if op == "remove_status":
        status_id = str(effect.get("status", "")).strip()
        if not status_id or not has_status(state, status_id):
            return True
        remove_status(state, status_id)
        status_name = _entry_name(content.get("statuses", {}).get(status_id, {}), status_id)
        add_status_effect(resolution, mode="remove", status_id=status_id, name=status_name, source=source)
        return True

    if op == "add_item":
        item_id = str(effect.get("item", "")).strip()
        qty = int(effect.get("qty", 1))
        if not item_id or qty <= 0:
            return True
        if bool(effect.get("only_if_missing")) and has_item(state, item_id):
            return True
        add_item(state, item_id, qty)
        item_name = _entry_name(content.get("items", {}).get(item_id, {}), item_id)
        add_item_effect(resolution, mode="add", item_id=item_id, name=item_name, qty=qty, source=source)
        return True

    if op == "remove_first_item":
        items = effect.get("items", [])
        if not isinstance(items, list):
            return True
        for item_id in items:
            if not isinstance(item_id, str):
                continue
            if remove_item(state, item_id, 1):
                item_name = _entry_name(content.get("items", {}).get(item_id, {}), item_id)
                add_item_effect(resolution, mode="remove", item_id=item_id, name=item_name, qty=1, source=source)
                break
        return True

    if op == "log":
        text = str(effect.get("text", "")).strip()
        if text:
            log_event(state, text)
        return True

    return False


def _iter_passive_sources(state: dict[str, Any], content: dict[str, Any]) -> list[tuple[str, str, dict[str, Any], str]]:
    """Collect professions, items, and statuses that can emit passive effects."""
    sources: list[tuple[str, str, dict[str, Any], str]] = []

    profession_id = str(state["player"].get("profession_id", ""))
    profession = get_profession(content, profession_id)
    if profession:
        sources.append(("profession", profession_id, profession, _effect_source_name("profession", profession, profession_id)))

    items = content.get("items", {})
    for item_id, qty in state["player"].get("inventory", {}).items():
        if int(qty) <= 0:
            continue
        item = items.get(item_id)
        if isinstance(item, dict):
            sources.append(("item", str(item_id), item, _effect_source_name("item", item, str(item_id))))

    statuses = content.get("statuses", {})
    for status_id in state["player"].get("statuses", []):
        status = statuses.get(status_id)
        if isinstance(status, dict):
            sources.append(("status", str(status_id), status, _effect_source_name("status", status, str(status_id))))

    return sources


def _legacy_trigger_effects(kind: str, source_id: str, entry: dict[str, Any], trigger: str, default_source: str) -> list[dict[str, Any]]:
    """Map older status fields onto the new trigger-effects lifecycle."""
    effects: list[dict[str, Any]] = []

    if kind == "status" and trigger == "turn_end":
        per_turn_effects = entry.get("per_turn_effects", [])
        if isinstance(per_turn_effects, list):
            for effect in per_turn_effects:
                if isinstance(effect, dict):
                    effects.append({"trigger": "turn_end", "source": default_source, **effect})

    if kind == "status" and trigger == "after_check":
        consume_on_check = entry.get("consume_on_check")
        if isinstance(consume_on_check, dict):
            match: dict[str, Any] = {}
            expected_stat = consume_on_check.get("stat")
            if expected_stat is not None:
                match["stat"] = str(expected_stat)
            effects.append(
                {
                    "trigger": "after_check",
                    "op": "remove_self",
                    "match": match,
                    "source": default_source,
                    "status_id": source_id,
                }
            )

    return effects


def _trigger_effects(kind: str, source_id: str, entry: dict[str, Any], trigger: str, default_source: str) -> list[dict[str, Any]]:
    """Return normalized trigger effects for one passive source."""
    effects: list[dict[str, Any]] = []
    configured = entry.get("trigger_effects", [])
    if isinstance(configured, list):
        for effect in configured:
            if not isinstance(effect, dict):
                continue
            if str(effect.get("trigger", "")) != trigger:
                continue
            effects.append(effect)
    effects.extend(_legacy_trigger_effects(kind, source_id, entry, trigger, default_source))
    return effects


def apply_passive_effects(
    state: dict[str, Any],
    content: dict[str, Any],
    trigger: str,
    *,
    ctx: dict[str, Any] | None = None,
    resolution: dict[str, Any] | None = None,
) -> None:
    """Run passive effects for one lifecycle trigger."""
    trigger_ctx = dict(ctx or {})
    trigger_ctx.setdefault("kind", trigger)

    for source_kind, source_id, entry, default_source in _iter_passive_sources(state, content):
        for effect in _trigger_effects(source_kind, source_id, entry, trigger, default_source):
            if not _trigger_effect_matches(effect, trigger_ctx):
                continue

            source = str(effect.get("source", default_source))
            op = str(effect.get("op", ""))

            if op == "remove_self" and source_kind == "status":
                if has_status(state, source_id):
                    remove_status(state, source_id)
                    status_name = _entry_name(entry, source_id)
                    add_status_effect(resolution, mode="remove", status_id=source_id, name=status_name, source=source)
                continue

            # Strip trigger metadata before forwarding to the generic effect
            # executor so story authors can use the same op vocabulary.
            passive_effect = {key: value for key, value in effect.items() if key not in {"trigger", "match", "source", "status_id"}}
            apply_state_effect(state, content, passive_effect, resolution=resolution, default_source=source)


def _match_bonus_rule(
    rule: dict[str, Any],
    *,
    stat: str,
    tags: list[str],
) -> bool:
    """Return whether a check-bonus rule applies to the current roll."""
    tag_set = set(tags)

    tags_any = rule.get("tags_any")
    if isinstance(tags_any, list) and tags_any:
        if not (tag_set & {str(tag) for tag in tags_any}):
            return False

    tags_all = rule.get("tags_all")
    if isinstance(tags_all, list) and tags_all:
        if not ({str(tag) for tag in tags_all} <= tag_set):
            return False

    stat_in = rule.get("stat_in")
    if isinstance(stat_in, list) and stat_in:
        if stat not in {str(v) for v in stat_in}:
            return False

    stat_equals = rule.get("stat_equals")
    if stat_equals is not None and stat != str(stat_equals):
        return False

    return True


def _profession_bonus(state: dict[str, Any], content: dict[str, Any], stat: str, tags: list[str]) -> list[tuple[int, str]]:
    """Collect profession-based check modifiers."""
    profession = get_profession(content, state["player"].get("profession_id", ""))
    if not profession:
        return []

    bonuses: list[tuple[int, str]] = []
    for rule in profession.get("check_bonus", []):
        if not isinstance(rule, dict):
            continue
        if not _match_bonus_rule(rule, stat=stat, tags=tags):
            continue
        bonuses.append((int(rule.get("value", 0)), str(rule.get("source", "职业加成"))))
    return bonuses


def _item_bonus(state: dict[str, Any], content: dict[str, Any], stat: str, tags: list[str]) -> list[tuple[int, str]]:
    """Collect inventory-based check modifiers."""
    bonuses: list[tuple[int, str]] = []
    items = content.get("items", {})
    for item_id, qty in state["player"]["inventory"].items():
        if int(qty) <= 0:
            continue
        item = items.get(item_id, {})
        for rule in item.get("check_bonus", []):
            if not isinstance(rule, dict):
                continue
            if not _match_bonus_rule(rule, stat=stat, tags=tags):
                continue
            bonuses.append((int(rule.get("value", 0)), str(rule.get("source", f"装备：{item.get('name', item_id)}"))))
    return bonuses


def _status_bonus(state: dict[str, Any], content: dict[str, Any], stat: str, tags: list[str]) -> list[tuple[int, str]]:
    """Collect status-based check modifiers."""
    bonuses: list[tuple[int, str]] = []
    statuses = content.get("statuses", {})
    for status_id in state["player"].get("statuses", []):
        status = statuses.get(status_id, {})
        for rule in status.get("check_bonus", []):
            if not isinstance(rule, dict):
                continue
            if not _match_bonus_rule(rule, stat=stat, tags=tags):
                continue
            bonuses.append((int(rule.get("value", 0)), str(rule.get("source", f"状态：{status.get('name', status_id)}"))))
    return bonuses


def _corruption_penalty(state: dict[str, Any], content: dict[str, Any]) -> tuple[int, str] | None:
    """Resolve the strongest active corruption penalty, if any."""
    entries = content.get("world", {}).get("corruption_penalties", [])
    if not isinstance(entries, list):
        return None

    corruption = int(state["player"].get("corruption", 0))
    for entry in sorted((entry for entry in entries if isinstance(entry, dict)), key=lambda x: int(x.get("min", 0)), reverse=True):
        if corruption >= int(entry.get("min", 0)):
            return int(entry.get("value", 0)), str(entry.get("source", "腐化惩罚"))
    return None


def _doom_dc_delta(state: dict[str, Any], check_cfg: dict[str, Any]) -> int:
    """Compute a DC modifier driven by global doom/progress pressure."""
    doom = int(state["progress"].get("doom", 0))
    entries = check_cfg.get("dc_adjust_by_doom", [])
    if not isinstance(entries, list):
        return 0

    for entry in sorted((entry for entry in entries if isinstance(entry, dict)), key=lambda x: int(x.get("min", 0)), reverse=True):
        if doom >= int(entry.get("min", 0)):
            return int(entry.get("delta", 0))
    return 0


def _flag_dc_delta(state: dict[str, Any], check_cfg: dict[str, Any]) -> int:
    """Compute a DC modifier contributed by progress flags."""
    result = 0
    entries = check_cfg.get("dc_adjust_if_flags", [])
    if not isinstance(entries, list):
        return 0

    flags = state["progress"].get("flags", {})
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        flag = str(entry.get("flag", ""))
        if flag and bool(flags.get(flag)):
            result += int(entry.get("delta", 0))
    return result


def _extra_bonus_from_flags(state: dict[str, Any], check_cfg: dict[str, Any]) -> list[tuple[int, str]]:
    """Collect bonus modifiers unlocked by story flags."""
    bonuses: list[tuple[int, str]] = []
    entries = check_cfg.get("extra_bonus_if_flags", [])
    if not isinstance(entries, list):
        return bonuses

    flags = state["progress"].get("flags", {})
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        flag = str(entry.get("flag", ""))
        if flag and bool(flags.get(flag)):
            bonuses.append((int(entry.get("bonus", 0)), str(entry.get("source", "情境修正"))))
    return bonuses


def _roll_die(sides: int) -> int:
    """Roll one die with the given number of sides."""
    safe_sides = max(2, int(sides))
    return random.randint(1, safe_sides)


def _spend_bonus_item(
    state: dict[str, Any],
    content: dict[str, Any],
    cfg: dict[str, Any],
    breakdown: list[dict[str, Any]],
    resolution: dict[str, Any],
) -> None:
    """Spend one configured item to add a temporary bonus to this resolution."""
    spend_if_has = cfg.get("spend_if_has")
    if not isinstance(spend_if_has, dict):
        return

    spend_item_id = str(spend_if_has.get("item", ""))
    if not spend_item_id or not has_item(state, spend_item_id):
        return

    remove_item(state, spend_item_id, 1)
    bonus = int(spend_if_has.get("bonus", 0))
    spend_label = str(spend_if_has.get("label", spend_item_id))
    breakdown.append({"value": bonus, "source": f"消耗物品：{spend_label}"})
    item_name = _entry_name(content.get("items", {}).get(spend_item_id, {}), spend_item_id)
    add_item_effect(
        resolution,
        mode="spend",
        item_id=spend_item_id,
        name=item_name,
        qty=1,
        source=f"消耗物品：{spend_label}",
    )


def _build_modifier_breakdown(
    state: dict[str, Any],
    content: dict[str, Any],
    cfg: dict[str, Any],
    *,
    stat: str,
    tags: list[str],
    include_doom_flag_bonus: bool,
) -> list[dict[str, Any]]:
    """Build and return the full modifier breakdown for one stat test."""
    stat_value = int(state["player"]["stats"].get(stat, 0))
    breakdown: list[dict[str, Any]] = [{"value": stat_modifier(stat_value), "source": f"属性修正({stat_value})"}]

    for value, source in _profession_bonus(state, content, stat, tags):
        breakdown.append({"value": value, "source": source})

    for value, source in _item_bonus(state, content, stat, tags):
        breakdown.append({"value": value, "source": source})

    for value, source in _status_bonus(state, content, stat, tags):
        breakdown.append({"value": value, "source": source})

    corruption_penalty = _corruption_penalty(state, content)
    if corruption_penalty:
        breakdown.append({"value": corruption_penalty[0], "source": corruption_penalty[1]})

    if include_doom_flag_bonus:
        for value, source in _extra_bonus_from_flags(state, cfg):
            breakdown.append({"value": value, "source": source})

    return breakdown


def _perform_stat_test(
    state: dict[str, Any],
    content: dict[str, Any],
    cfg: dict[str, Any],
    *,
    kind: str,
    default_label: str,
    trigger_kind: str,
    include_doom_flag_bonus: bool = True,
) -> dict[str, Any]:
    """Execute a generic d20 stat test used by check/save flows."""
    stat = str(cfg.get("stat", "might"))
    tags = [str(tag) for tag in cfg.get("tags", []) if isinstance(tag, str)]
    if kind not in tags:
        tags.append(kind)

    label = str(cfg.get("label", default_label))
    resolution = build_resolution(kind=kind, label=label, stat=stat, tags=tags)

    # Passive hooks can mutate resources/flags before and after the roll.
    apply_passive_effects(
        state,
        content,
        "before_check",
        ctx={"kind": trigger_kind, "stat": stat, "tags": tags},
        resolution=resolution,
    )

    base_dc = int(cfg.get("dc", 10))
    dc = base_dc + _doom_dc_delta(state, cfg) + _flag_dc_delta(state, cfg)
    breakdown = _build_modifier_breakdown(
        state,
        content,
        cfg,
        stat=stat,
        tags=tags,
        include_doom_flag_bonus=include_doom_flag_bonus,
    )
    _spend_bonus_item(state, content, cfg, breakdown, resolution)

    roll = _roll_die(int(cfg.get("die", 20)))
    modifier = sum(int(entry.get("value", 0)) for entry in breakdown)
    total = roll + modifier
    success = total >= dc

    resolution["dc"] = dc
    resolution["roll"] = roll
    resolution["modifier"] = modifier
    resolution["total"] = total
    resolution["success"] = success
    resolution["breakdown"] = breakdown

    apply_passive_effects(
        state,
        content,
        "after_check",
        ctx={"kind": trigger_kind, "stat": stat, "tags": tags, "success": success},
        resolution=resolution,
    )
    return resolution


def perform_check(state: dict[str, Any], content: dict[str, Any], check_cfg: dict[str, Any]) -> dict[str, Any]:
    """Execute the engine's standard attribute check."""
    return _perform_stat_test(
        state,
        content,
        check_cfg,
        kind="check",
        default_label="检定",
        trigger_kind="check",
    )


def perform_save(state: dict[str, Any], content: dict[str, Any], save_cfg: dict[str, Any]) -> dict[str, Any]:
    """Execute a saving throw style resolution against a fixed DC."""
    return _perform_stat_test(
        state,
        content,
        save_cfg,
        kind="save",
        default_label="豁免",
        trigger_kind="save",
    )


def perform_contest(state: dict[str, Any], content: dict[str, Any], contest_cfg: dict[str, Any]) -> dict[str, Any]:
    """Execute a player-vs-opponent contested roll."""
    stat = str(contest_cfg.get("stat", "might"))
    tags = [str(tag) for tag in contest_cfg.get("tags", []) if isinstance(tag, str)]
    if "contest" not in tags:
        tags.append("contest")
    label = str(contest_cfg.get("label", "对抗"))
    resolution = build_resolution(kind="contest", label=label, stat=stat, tags=tags)

    apply_passive_effects(
        state,
        content,
        "before_check",
        ctx={"kind": "contest", "stat": stat, "tags": tags},
        resolution=resolution,
    )

    breakdown = _build_modifier_breakdown(
        state,
        content,
        contest_cfg,
        stat=stat,
        tags=tags,
        include_doom_flag_bonus=True,
    )
    _spend_bonus_item(state, content, contest_cfg, breakdown, resolution)

    roll = _roll_die(int(contest_cfg.get("die", 20)))
    modifier = sum(int(entry.get("value", 0)) for entry in breakdown)
    total = roll + modifier

    opponent_roll = _roll_die(int(contest_cfg.get("opponent_die", 20)))
    opponent_modifier = int(contest_cfg.get("opponent_modifier", 0))
    opponent_total = opponent_roll + opponent_modifier

    success = total >= opponent_total
    resolution["roll"] = roll
    resolution["modifier"] = modifier
    resolution["total"] = total
    resolution["success"] = success
    resolution["breakdown"] = breakdown
    resolution["opponent_label"] = str(contest_cfg.get("opponent_label", "对手"))
    resolution["opponent_roll"] = opponent_roll
    resolution["opponent_modifier"] = opponent_modifier
    resolution["opponent_total"] = opponent_total

    apply_passive_effects(
        state,
        content,
        "after_check",
        ctx={"kind": "contest", "stat": stat, "tags": tags, "success": success},
        resolution=resolution,
    )
    return resolution


def _match_damage_rule(rule: dict[str, Any], damage_type: str) -> bool:
    """Return whether one resistance rule applies to a damage type."""
    rule_type = str(rule.get("type", "")).strip().lower()
    if rule_type and rule_type not in {"any", damage_type}:
        return False

    type_in = rule.get("type_in")
    if isinstance(type_in, list) and type_in:
        expected = {str(item).strip().lower() for item in type_in}
        if damage_type not in expected:
            return False

    return True


def _normalize_resistance_rules(raw_rules: Any, *, default_source: str) -> list[dict[str, Any]]:
    """Normalize list/dict resistance declarations into a rule list."""
    normalized: list[dict[str, Any]] = []

    if isinstance(raw_rules, dict):
        for key, value in raw_rules.items():
            normalized.append(
                {
                    "type": str(key).strip().lower(),
                    "reduce": int(value),
                    "percent": 0,
                    "source": default_source,
                }
            )
        return normalized

    if not isinstance(raw_rules, list):
        return normalized

    for entry in raw_rules:
        if not isinstance(entry, dict):
            continue
        normalized.append(
            {
                "type": str(entry.get("type", "")).strip().lower(),
                "type_in": [str(item).strip().lower() for item in entry.get("type_in", []) if str(item).strip()]
                if isinstance(entry.get("type_in"), list)
                else [],
                "reduce": int(entry.get("reduce", 0)),
                "percent": int(entry.get("percent", 0)),
                "source": str(entry.get("source", default_source)),
            }
        )
    return normalized


def _collect_player_resistance_rules(state: dict[str, Any], content: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect player-side resistance rules from profession, items, and statuses."""
    rules: list[dict[str, Any]] = []

    profession = get_profession(content, str(state["player"].get("profession_id", "")))
    if isinstance(profession, dict):
        rules.extend(
            _normalize_resistance_rules(
                profession.get("damage_resistances", []),
                default_source=_effect_source_name("profession", profession, str(profession.get("id", "职业"))),
            )
        )

    items = content.get("items", {})
    for item_id, qty in state["player"].get("inventory", {}).items():
        if int(qty) <= 0:
            continue
        item = items.get(item_id)
        if not isinstance(item, dict):
            continue
        rules.extend(
            _normalize_resistance_rules(
                item.get("damage_resistances", []),
                default_source=_effect_source_name("item", item, str(item_id)),
            )
        )

    statuses = content.get("statuses", {})
    for status_id in state["player"].get("statuses", []):
        status = statuses.get(status_id)
        if not isinstance(status, dict):
            continue
        rules.extend(
            _normalize_resistance_rules(
                status.get("damage_resistances", []),
                default_source=_effect_source_name("status", status, str(status_id)),
            )
        )

    return rules


def _collect_enemy_resistance_rules(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect resistance rules from the active encounter enemy runtime block."""
    encounter = state.get("encounter")
    if not isinstance(encounter, dict):
        return []

    enemy = encounter.get("enemy")
    if not isinstance(enemy, dict):
        return []

    return _normalize_resistance_rules(
        enemy.get("resistances", []),
        default_source=f"敌方：{enemy.get('name', '敌方')}",
    )


def _apply_damage_to_target(
    state: dict[str, Any],
    content: dict[str, Any],
    *,
    target: str,
    resource: str,
    amount: int,
    resolution: dict[str, Any],
    source: str,
) -> tuple[int, str]:
    """Apply final damage value to the selected target and return applied amount."""
    if target == "enemy":
        encounter = state.get("encounter")
        if not isinstance(encounter, dict):
            return 0, "敌方目标"

        enemy = encounter.get("enemy")
        if not isinstance(enemy, dict):
            return 0, "敌方目标"

        if resource != "hp":
            return 0, str(enemy.get("name", "敌方目标"))

        before = max(0, int(enemy.get("hp", 0)))
        max_hp = max(0, int(enemy.get("max_hp", before)))
        after = before - max(0, int(amount))
        if max_hp > 0:
            after = max(0, min(max_hp, after))
        else:
            after = max(0, after)
        enemy["hp"] = after
        return before - after, str(enemy.get("name", "敌方目标"))

    delta = adjust_resource(state, content, resource, -amount)
    add_resource_effect(resolution, resource, delta, source)
    return abs(int(delta)), "你"


def perform_damage(state: dict[str, Any], content: dict[str, Any], damage_cfg: dict[str, Any]) -> dict[str, Any]:
    """Execute typed damage with resistance and mitigation handling."""
    target = str(damage_cfg.get("target", "player")).strip().lower() or "player"
    resource = str(damage_cfg.get("resource", "hp")).strip() or "hp"
    damage_type = str(damage_cfg.get("damage_type", "physical")).strip().lower() or "physical"
    penetration = max(0, int(damage_cfg.get("penetration", 0)))
    tags = [str(tag) for tag in damage_cfg.get("tags", []) if isinstance(tag, str)]
    if "damage" not in tags:
        tags.append("damage")
    if damage_type not in tags:
        tags.append(damage_type)

    label = str(damage_cfg.get("label", "伤害结算"))
    resolution = build_resolution(kind="damage", label=label, tags=tags)

    static_amount = max(0, int(damage_cfg.get("amount", 0)))
    roll_cfg = damage_cfg.get("roll")
    rolled_amount = 0
    if isinstance(roll_cfg, dict):
        dice = max(1, int(roll_cfg.get("dice", 1)))
        sides = max(2, int(roll_cfg.get("sides", 6)))
        bonus = int(roll_cfg.get("bonus", 0))
        rolled_amount = sum(_roll_die(sides) for _ in range(dice)) + bonus
        if rolled_amount < 0:
            rolled_amount = 0
        resolution["roll"] = rolled_amount
        resolution["breakdown"] = [{"value": rolled_amount, "source": f"{dice}d{sides}+{bonus}"}]

    declared = max(0, static_amount + rolled_amount)
    base_breakdown: list[dict[str, Any]] = [{"value": declared, "source": "宣告伤害"}]
    if isinstance(resolution.get("breakdown"), list):
        base_breakdown.extend([entry for entry in resolution.get("breakdown", []) if isinstance(entry, dict)])

    if bool(damage_cfg.get("ignore_resistance")):
        resistance_rules: list[dict[str, Any]] = []
    elif target == "enemy":
        resistance_rules = _collect_enemy_resistance_rules(state)
    else:
        resistance_rules = _collect_player_resistance_rules(state, content)

    flat_total = 0
    percent_total = 0
    for rule in resistance_rules:
        if not _match_damage_rule(rule, damage_type):
            continue
        flat_total += max(0, int(rule.get("reduce", 0)))
        percent_total += max(0, int(rule.get("percent", 0)))

    percent_total = max(0, min(95, percent_total))
    effective_flat = max(0, flat_total - penetration)
    mitigated_flat = min(declared, effective_flat)
    after_flat = max(0, declared - mitigated_flat)
    mitigated_percent = int(round(after_flat * percent_total / 100))
    final_amount = max(0, after_flat - mitigated_percent)
    mitigated = max(0, declared - final_amount)

    if penetration > 0:
        base_breakdown.append({"value": penetration, "source": "穿透"})
    if mitigated_flat > 0:
        base_breakdown.append({"value": -mitigated_flat, "source": "平减伤"})
    if mitigated_percent > 0:
        base_breakdown.append({"value": -mitigated_percent, "source": f"百分比减伤({percent_total}%)"})
    resolution["breakdown"] = base_breakdown

    applied, target_label = _apply_damage_to_target(
        state,
        content,
        target=target,
        resource=resource,
        amount=final_amount,
        resolution=resolution,
        source=str(damage_cfg.get("source", "伤害效果")),
    )

    resolution["amount"] = declared
    resolution["mitigated"] = mitigated
    resolution["applied"] = applied
    resolution["damage_type"] = damage_type
    resolution["target"] = target
    resolution["target_label"] = target_label
    resolution["penetration"] = penetration
    resolution["resistance_flat"] = flat_total
    resolution["resistance_percent"] = percent_total
    resolution["success"] = applied > 0
    add_damage_effect(
        resolution,
        resource=resource,
        amount=declared,
        applied=applied,
        mitigated=mitigated,
        damage_type=damage_type,
        target=target,
        target_label=target_label,
        penetration=penetration,
        resistance_flat=flat_total,
        resistance_percent=percent_total,
        source=str(damage_cfg.get("source", "伤害效果")),
    )
    return resolution


def advance_turn(state: dict[str, Any], content: dict[str, Any], resolution: dict[str, Any] | None = None) -> None:
    """Advance shared turn counters and run turn-end passive effects."""
    state["progress"]["turns"] = int(state["progress"].get("turns", 0)) + 1
    encounter = state.get("encounter")
    if isinstance(encounter, dict) and encounter.get("id"):
        encounter["round"] = int(encounter.get("round", 0)) + 1
    apply_passive_effects(
        state,
        content,
        "turn_end",
        ctx={"kind": "turn_end"},
        resolution=resolution,
    )


def use_utility_item(state: dict[str, Any], content: dict[str, Any], item_id: str) -> tuple[bool, str, dict[str, Any]]:
    """Consume one directly-usable item from inventory."""
    item = content.get("items", {}).get(item_id, {"name": item_id})
    item_name = str(item.get("name", item_id))
    resolution = build_resolution(kind="utility", label=f"使用{item_name}", success=False, tags=["utility"])

    if not has_item(state, item_id):
        return False, "你没有这件物品。", resolution

    effects = item.get("use_effects", [])
    if not isinstance(effects, list) or not effects:
        return False, f"{item.get('name', item_id)} 不能在这里直接使用。", resolution

    remove_item(state, item_id, 1)
    add_item_effect(resolution, mode="spend", item_id=item_id, name=item_name, qty=1, source=f"物品：{item_name}")

    for effect in effects:
        if not isinstance(effect, dict):
            continue
        apply_state_effect(state, content, effect, resolution=resolution, default_source=f"物品：{item_name}")

    resolution["success"] = True
    return True, f"你使用了{item_name}。", resolution


def inventory_view(state: dict[str, Any], content: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize the inventory for frontend rendering."""
    inventory = state["player"].get("inventory", {})
    items = content.get("items", {})
    result: list[dict[str, Any]] = []

    for item_id, qty in inventory.items():
        if int(qty) <= 0:
            continue
        item = items.get(item_id, {})
        result.append(
            {
                "id": item_id,
                "qty": int(qty),
                "name": str(item.get("name", item_id)),
                "description": str(item.get("description", "")),
                "usable": bool(item.get("use_effects")),
            }
        )

    result.sort(key=lambda entry: entry["name"])
    return result


def statuses_view(state: dict[str, Any], content: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize active statuses for frontend rendering."""
    statuses = content.get("statuses", {})
    result: list[dict[str, Any]] = []

    for status_id in state["player"].get("statuses", []):
        status = statuses.get(status_id, {})
        result.append(
            {
                "id": status_id,
                "name": str(status.get("name", status_id)),
                "description": str(status.get("description", "")),
            }
        )

    return result
