"""Generic story interpreter for node/action/effect based story packs.

`StoryDirector` is where story-pack data becomes runtime behavior. It should
stay free of story-specific constants and instead expose reusable action/effect
semantics that future settings can consume.
"""

from __future__ import annotations

import re
from typing import Any

from .rules import (
    apply_state_effect,
    advance_turn,
    log_event,
    perform_check,
    perform_contest,
    perform_damage,
    perform_save,
    use_utility_item,
)
from .resolution import add_encounter_effect, build_resolution, ensure_resolution, legacy_roll_payload, merge_change_lines

_TEMPLATE_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


class StoryDirector:
    """Interpret node actions, checks, effects, and endings for one story pack."""

    def __init__(self, content: dict[str, Any]) -> None:
        """Bind the normalized content dictionary for one active story."""
        self.content = content

    def _nodes(self) -> dict[str, Any]:
        """Return the story's node table."""
        return self.content.get("nodes", {})

    def _encounters(self) -> dict[str, Any]:
        """Return the story's encounter template table."""
        return self.content.get("encounters", {})

    def _node(self, node_id: str) -> dict[str, Any]:
        """Return one node, falling back to start/first node for resilience."""
        nodes = self._nodes()
        if node_id in nodes:
            return nodes[node_id]
        start_node = str(self.content.get("world", {}).get("start_node", ""))
        if start_node in nodes:
            return nodes[start_node]
        first_key = next(iter(nodes.keys()), "")
        return nodes.get(first_key, {"title": "", "text": "", "actions": []})

    def _encounter_template(self, encounter_id: str) -> dict[str, Any]:
        """Return one encounter template or an empty object."""
        encounters = self._encounters()
        template = encounters.get(encounter_id)
        if isinstance(template, dict):
            return template
        return {}

    def _active_encounter(self, state: dict[str, Any]) -> dict[str, Any] | None:
        """Return the active encounter runtime block if one exists."""
        encounter = state.get("encounter")
        if isinstance(encounter, dict) and encounter.get("id"):
            return encounter
        return None

    def _encounter_phases(self, template: dict[str, Any]) -> dict[str, Any]:
        """Return phase definitions for one encounter template."""
        phases = template.get("phases", {})
        if isinstance(phases, dict):
            return phases
        return {}

    def _default_phase_id(self, template: dict[str, Any]) -> str:
        """Resolve the default phase id for an encounter template."""
        phases = self._encounter_phases(template)
        start_phase = str(template.get("start_phase", "")).strip()
        if start_phase and start_phase in phases:
            return start_phase
        if phases:
            return str(next(iter(phases.keys())))
        return "default"

    def _phase_def(self, template: dict[str, Any], phase_id: str) -> dict[str, Any]:
        """Return one phase definition object or an empty mapping."""
        phase = self._encounter_phases(template).get(phase_id)
        if isinstance(phase, dict):
            return phase
        return {}

    def _sync_encounter_phase(
        self,
        state: dict[str, Any],
        *,
        resolution: dict[str, Any] | None = None,
        source: str = "遭遇阶段",
    ) -> None:
        """Evaluate phase rules and synchronize phase-specific runtime fields."""
        encounter = self._active_encounter(state)
        if encounter is None:
            return

        template = self._encounter_template(str(encounter.get("id", "")))
        default_phase_id = self._default_phase_id(template)
        previous_phase = str(encounter.get("phase", "")).strip() or default_phase_id
        selected_phase = previous_phase

        phase_rules = template.get("phase_rules", [])
        if isinstance(phase_rules, list):
            for rule in phase_rules:
                if not isinstance(rule, dict):
                    continue
                target_phase = str(rule.get("phase", "")).strip()
                if not target_phase:
                    continue
                condition = rule.get("if")
                if isinstance(condition, dict) and not self._check_requirement(state, condition, {"kind": "encounter_phase"}):
                    continue
                selected_phase = target_phase
                break

        phase_def = self._phase_def(template, selected_phase)
        encounter["phase"] = selected_phase
        encounter["phase_label"] = str(phase_def.get("label", selected_phase))
        encounter["intent"] = str(
            phase_def.get(
                "intent",
                encounter.get("intent")
                or (encounter.get("enemy", {}) if isinstance(encounter.get("enemy"), dict) else {}).get("intent", ""),
            )
        )

        if phase_def.get("summary"):
            encounter["summary"] = str(phase_def.get("summary", encounter.get("summary", "")))
        if phase_def.get("goal"):
            encounter["goal"] = str(phase_def.get("goal", encounter.get("goal", "")))

        if selected_phase != previous_phase:
            add_encounter_effect(
                resolution,
                mode="phase",
                title=str(encounter.get("title", "遭遇")),
                label=str(encounter.get("phase_label", selected_phase)),
                source=source,
            )

    def _normalize_active_encounter(self, state: dict[str, Any]) -> None:
        """Backfill encounter runtime fields for old saves and old templates."""
        encounter = self._active_encounter(state)
        if encounter is None:
            return

        template = self._encounter_template(str(encounter.get("id", "")))
        encounter.setdefault("title", str(template.get("title", encounter.get("id", "遭遇"))))
        encounter.setdefault("type", str(template.get("type", "encounter")))
        encounter.setdefault("summary", str(template.get("summary", "")))
        encounter.setdefault("goal", str(template.get("goal", "")))
        encounter.setdefault("round", 0)
        encounter.setdefault("pressure", int(template.get("start_pressure", 0)))
        encounter.setdefault("pressure_label", str(template.get("pressure_label", "压力")))
        encounter.setdefault("pressure_max", max(0, int(template.get("pressure_max", 0))))
        encounter.setdefault("flags", {})

        enemy_template = template.get("enemy")
        enemy_runtime = encounter.get("enemy")
        if not isinstance(enemy_runtime, dict):
            enemy_runtime = {}
        if isinstance(enemy_template, dict):
            enemy_runtime.setdefault("name", str(enemy_template.get("name", "敌方")))
            enemy_runtime.setdefault("intent", str(enemy_template.get("intent", "")))
            enemy_max_hp = int(enemy_template.get("max_hp", enemy_template.get("hp", 0)))
            enemy_runtime.setdefault("max_hp", max(0, enemy_max_hp))
            enemy_runtime.setdefault("hp", max(0, int(enemy_template.get("hp", enemy_runtime.get("max_hp", 0)))))
            enemy_runtime.setdefault(
                "resistances",
                [entry for entry in enemy_template.get("resistances", []) if isinstance(entry, dict)]
                if isinstance(enemy_template.get("resistances", []), list)
                else [],
            )
        if enemy_runtime:
            encounter["enemy"] = enemy_runtime

        objective_template = template.get("objective")
        objective_runtime = encounter.get("objective")
        if not isinstance(objective_runtime, dict):
            objective_runtime = {}
        if isinstance(objective_template, dict):
            objective_runtime.setdefault("label", str(objective_template.get("label", "进度")))
            objective_runtime.setdefault("target", max(0, int(objective_template.get("target", 0))))
            objective_runtime.setdefault("progress", max(0, int(objective_template.get("start", 0))))
        if objective_runtime:
            encounter["objective"] = objective_runtime

        encounter.setdefault("phase", self._default_phase_id(template))
        encounter.setdefault("phase_label", str(encounter.get("phase", "default")))
        encounter.setdefault("intent", str((encounter.get("enemy") or {}).get("intent", "")))
        self._sync_encounter_phase(state, source="遭遇同步")

    def _set_outcome(
        self,
        state: dict[str, Any],
        summary: str,
        detail: str,
        *,
        roll: dict[str, Any] | None = None,
        resolution: dict[str, Any] | None = None,
        changes: list[str] | None = None,
    ) -> None:
        """Write the latest player-facing outcome block to state."""
        merged_changes = merge_change_lines(changes, resolution)
        state["last_outcome"] = {
            "summary": summary,
            "detail": detail,
            "roll": roll or legacy_roll_payload(resolution),
            "resolution": resolution,
            "changes": merged_changes,
        }

    def _doom_text(self, state: dict[str, Any]) -> str:
        """Resolve the flavor text for the current doom threshold."""
        doom = int(state.get("progress", {}).get("doom", 0))
        entries = self.content.get("world", {}).get("doom_texts", [])
        if not isinstance(entries, list):
            return ""

        for entry in sorted((entry for entry in entries if isinstance(entry, dict)), key=lambda x: int(x.get("min", 0)), reverse=True):
            if doom >= int(entry.get("min", 0)):
                return str(entry.get("text", ""))
        return ""

    def _refresh_outcome_changes(self, state: dict[str, Any]) -> None:
        """Rebuild rendered change lines after turn-end or fatal effects."""
        outcome = state.get("last_outcome")
        if not isinstance(outcome, dict):
            return
        outcome["changes"] = merge_change_lines(
            [str(item) for item in outcome.get("changes", []) if isinstance(item, str)],
            outcome.get("resolution"),
        )

    def _resolve_path(self, data: dict[str, Any], path: str) -> Any:
        """Follow a dotted path inside nested dictionaries."""
        current: Any = data
        for key in path.split("."):
            if not isinstance(current, dict):
                return None
            if key not in current:
                return None
            current = current[key]
        return current

    def _render_text(self, state: dict[str, Any], text: str) -> str:
        """Render template placeholders inside story text."""
        context = {
            "player": state.get("player", {}),
            "progress": state.get("progress", {}),
            "encounter": state.get("encounter", {}),
            "world": self.content.get("world", {}),
            "doom_text": self._doom_text(state),
        }

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            if key == "doom_text":
                return str(context.get("doom_text", ""))
            value = self._resolve_path(context, key)
            if value is None:
                return ""
            return str(value)

        return _TEMPLATE_RE.sub(replace, text)

    def _compare(self, left: Any, op: str, right: Any) -> bool:
        """Evaluate a simple comparison operator used by requirements."""
        if op == "==":
            return left == right
        if op == "!=":
            return left != right

        numeric_ops = {">=", "<=", ">", "<"}
        if op in numeric_ops:
            try:
                left_num = float(left)
                right_num = float(right)
            except (TypeError, ValueError):
                return False
            if op == ">=":
                return left_num >= right_num
            if op == "<=":
                return left_num <= right_num
            if op == ">":
                return left_num > right_num
            if op == "<":
                return left_num < right_num

        return False

    def _check_requirement(self, state: dict[str, Any], requirement: dict[str, Any], ctx: dict[str, Any] | None = None) -> bool:
        """Evaluate the story DSL's requirement/condition object."""
        if not isinstance(requirement, dict) or not requirement:
            return True

        if "all" in requirement:
            all_items = requirement.get("all", [])
            if not isinstance(all_items, list):
                return False
            return all(self._check_requirement(state, item, ctx) for item in all_items)

        if "any" in requirement:
            any_items = requirement.get("any", [])
            if not isinstance(any_items, list):
                return False
            return any(self._check_requirement(state, item, ctx) for item in any_items)

        op = str(requirement.get("op", "=="))
        right = requirement.get("value")

        if "path" in requirement:
            left = self._resolve_path(state, str(requirement.get("path", "")))
            return self._compare(left, op, right)

        if "ctx" in requirement:
            left = self._resolve_path(ctx or {}, str(requirement.get("ctx", "")))
            return self._compare(left, op, right)

        if "item" in requirement:
            item_id = str(requirement.get("item", ""))
            qty = int(state.get("player", {}).get("inventory", {}).get(item_id, 0))
            return self._compare(qty, op, int(right or 0))

        return False

    def _finish_game(
        self,
        state: dict[str, Any],
        ending_id: str,
        summary: str,
        *,
        roll: dict[str, Any] | None = None,
        resolution: dict[str, Any] | None = None,
    ) -> None:
        """Write a final ending into state and stop further play."""
        endings = self.content.get("endings", {})
        fallback = {
            "id": "unknown",
            "title": "未知结局",
            "text": "故事以一种无法解释的方式终止。",
        }
        ending = endings.get(ending_id, fallback)
        state["game_over"] = True
        state["ending"] = ending
        self._set_outcome(state, summary, str(ending.get("text", "")), roll=roll, resolution=resolution)
        log_event(state, f"结局：{ending.get('title', ending_id)}")

    def _default_ending_id(self) -> str:
        """Return the configured default ending id for fallback cases."""
        endings = self.content.get("endings", {})
        configured = str(self.content.get("world", {}).get("default_ending_id", "")).strip()
        if configured and configured in endings:
            return configured
        for ending_id in endings.keys():
            return str(ending_id)
        return "unknown"

    def _fatal_rule(self, key: str, default_summary: str) -> tuple[str, str]:
        """Resolve configured fatal-rule endings such as death or corruption."""
        fatal_rules = self.content.get("world", {}).get("fatal_rules", {})
        if isinstance(fatal_rules, dict):
            rule = fatal_rules.get(key)
            if isinstance(rule, dict):
                ending_id = str(rule.get("ending", self._default_ending_id())) or self._default_ending_id()
                summary = str(rule.get("summary", default_summary))
                return ending_id, summary
        return self._default_ending_id(), default_summary

    def _resolve_victory(
        self,
        state: dict[str, Any],
        method: str,
        *,
        roll: dict[str, Any] | None = None,
        resolution: dict[str, Any] | None = None,
    ) -> None:
        """Select a victory ending using story-configured result rules."""
        resolver = self.content.get("world", {}).get("resolve_victory")
        chosen: dict[str, Any] | None = None
        if isinstance(resolver, dict):
            if isinstance(resolver.get("default"), dict):
                chosen = resolver.get("default")
            rules = resolver.get("rules", [])
            if isinstance(rules, list):
                for rule in rules:
                    if not isinstance(rule, dict):
                        continue
                    condition = rule.get("if")
                    if not isinstance(condition, dict):
                        continue
                    if self._check_requirement(state, condition, {"method": method}):
                        result = rule.get("result")
                        if isinstance(result, dict):
                            chosen = result

        if not isinstance(chosen, dict):
            chosen = {"ending": self._default_ending_id(), "summary": "你完成了最终对抗。"}

        ending_id = str(chosen.get("ending", self._default_ending_id())) or self._default_ending_id()
        summary = str(chosen.get("summary", "你完成了最终对抗。"))
        self._finish_game(state, ending_id, summary, roll=roll, resolution=resolution)

    def _apply_fatal(self, state: dict[str, Any], *, resolution: dict[str, Any] | None = None) -> None:
        """Stop the game when HP or corruption reaches a fatal threshold."""
        if state.get("game_over"):
            return
        if int(state["player"].get("hp", 0)) <= 0:
            ending_id, summary = self._fatal_rule("on_hp_zero", "你的生命归零。")
            self._finish_game(state, ending_id, summary, resolution=resolution)
            return
        corruption_limit = int(self.content.get("world", {}).get("corruption_limit", 10))
        if int(state["player"].get("corruption", 0)) >= corruption_limit:
            ending_id, summary = self._fatal_rule("on_corruption_limit", "腐化吞没了你的意志。")
            self._finish_game(state, ending_id, summary, resolution=resolution)

    def _apply_effect(self, state: dict[str, Any], effect: dict[str, Any], ctx: dict[str, Any]) -> bool:
        """Apply one effect DSL entry.

        Returns `True` when the effect wrote a visible outcome block. This lets
        callers avoid overwriting explicit narrative outcomes with generic text.
        """
        op = str(effect.get("op", ""))

        if apply_state_effect(
            state,
            self.content,
            effect,
            resolution=ctx.get("resolution"),
            default_source=str(ctx.get("source", "剧情效果")),
        ):
            return False

        if op == "goto":
            node_id = str(effect.get("node", "")).strip()
            if node_id in self._nodes():
                state["progress"]["node_id"] = node_id
            return False

        if op == "start_encounter":
            # Encounters are runtime state objects created from templates so the
            # same story pack can reuse them across nodes and branches.
            encounter_id = str(effect.get("encounter", "")).strip()
            template = self._encounter_template(encounter_id)
            if not encounter_id or not template:
                return False
            encounter_title = str(template.get("title", encounter_id))
            enemy_template = template.get("enemy") if isinstance(template.get("enemy"), dict) else {}
            objective_template = template.get("objective") if isinstance(template.get("objective"), dict) else {}
            state["encounter"] = {
                "id": encounter_id,
                "title": encounter_title,
                "type": str(template.get("type", "encounter")),
                "summary": str(template.get("summary", "")),
                "goal": str(template.get("goal", "")),
                "round": max(0, int(effect.get("round", template.get("start_round", 0)))),
                "pressure": int(effect.get("pressure", template.get("start_pressure", 0))),
                "pressure_label": str(template.get("pressure_label", "压力")),
                "pressure_max": max(0, int(template.get("pressure_max", 0))),
                "phase": self._default_phase_id(template),
                "phase_label": "",
                "intent": "",
                "enemy": {
                    "name": str(enemy_template.get("name", "敌方")),
                    "intent": str(enemy_template.get("intent", "")),
                    "max_hp": max(0, int(enemy_template.get("max_hp", enemy_template.get("hp", 0)))),
                    "hp": max(0, int(enemy_template.get("hp", enemy_template.get("max_hp", 0)))),
                    "resistances": [entry for entry in enemy_template.get("resistances", []) if isinstance(entry, dict)]
                    if isinstance(enemy_template.get("resistances", []), list)
                    else [],
                }
                if enemy_template
                else None,
                "objective": {
                    "label": str(objective_template.get("label", "进度")),
                    "target": max(0, int(objective_template.get("target", 0))),
                    "progress": max(0, int(objective_template.get("start", 0))),
                }
                if objective_template
                else None,
                "flags": {},
            }
            self._normalize_active_encounter(state)
            self._sync_encounter_phase(
                state,
                resolution=ctx.get("resolution"),
                source=str(ctx.get("source", "遭遇开始")),
            )
            add_encounter_effect(
                ctx.get("resolution"),
                mode="enter",
                title=encounter_title,
                source=str(ctx.get("source", "遭遇开始")),
            )
            return False

        if op == "adjust_encounter":
            # The first supported encounter stat is `pressure`; more fields can
            # be added later without changing the frontend contract.
            encounter = self._active_encounter(state)
            if encounter is None:
                return False
            field = str(effect.get("field", "pressure"))
            if field != "pressure":
                return False
            before = int(encounter.get("pressure", 0))
            delta = int(effect.get("amount", 0))
            pressure_max = max(0, int(encounter.get("pressure_max", 0)))
            after = before + delta
            if pressure_max > 0:
                after = max(0, min(pressure_max, after))
            else:
                after = max(0, after)
            encounter["pressure"] = after
            actual_delta = after - before
            resolution = ctx.get("resolution")
            if isinstance(resolution, dict):
                add_encounter_effect(
                    resolution,
                    mode="pressure",
                    title=str(encounter.get("title", "遭遇")),
                    delta=actual_delta,
                    label=str(encounter.get("pressure_label", "压力")),
                    source=str(ctx.get("source", "遭遇效果")),
                )
            self._sync_encounter_phase(
                state,
                resolution=ctx.get("resolution"),
                source=str(ctx.get("source", "遭遇效果")),
            )
            return False

        if op == "set_encounter_flag":
            encounter = self._active_encounter(state)
            if encounter is None:
                return False
            flag = str(effect.get("flag", "")).strip()
            if not flag:
                return False
            encounter.setdefault("flags", {})[flag] = bool(effect.get("value", True))
            return False

        if op == "clear_encounter_flag":
            encounter = self._active_encounter(state)
            if encounter is None:
                return False
            flag = str(effect.get("flag", "")).strip()
            if not flag:
                return False
            encounter.setdefault("flags", {}).pop(flag, None)
            return False

        if op == "adjust_enemy_hp":
            encounter = self._active_encounter(state)
            if encounter is None:
                return False
            enemy = encounter.get("enemy")
            if not isinstance(enemy, dict):
                return False
            before = max(0, int(enemy.get("hp", 0)))
            delta = int(effect.get("amount", 0))
            max_hp = max(0, int(enemy.get("max_hp", before)))
            after = before + delta
            if max_hp > 0:
                after = max(0, min(max_hp, after))
            else:
                after = max(0, after)
            enemy["hp"] = after
            self._sync_encounter_phase(
                state,
                resolution=ctx.get("resolution"),
                source=str(ctx.get("source", "遭遇效果")),
            )
            return False

        if op == "adjust_objective":
            encounter = self._active_encounter(state)
            if encounter is None:
                return False
            objective = encounter.get("objective")
            if not isinstance(objective, dict):
                return False
            before = max(0, int(objective.get("progress", 0)))
            delta = int(effect.get("amount", 0))
            target = max(0, int(objective.get("target", 0)))
            after = before + delta
            if target > 0:
                after = max(0, min(target, after))
            else:
                after = max(0, after)
            objective["progress"] = after
            self._sync_encounter_phase(
                state,
                resolution=ctx.get("resolution"),
                source=str(ctx.get("source", "遭遇效果")),
            )
            return False

        if op == "sync_encounter_phase":
            self._sync_encounter_phase(
                state,
                resolution=ctx.get("resolution"),
                source=str(ctx.get("source", "遭遇阶段")),
            )
            return False

        if op == "damage":
            damage_cfg = effect.get("damage")
            payload = damage_cfg if isinstance(damage_cfg, dict) else effect
            if not isinstance(payload, dict):
                return False
            damage_result = perform_damage(state, self.content, payload)
            merged = ensure_resolution(ctx.get("resolution"))
            if merged is not None:
                merged_effects = merged.setdefault("effects", [])
                for item in damage_result.get("effects", []):
                    merged_effects.append(item)
            return False

        if op == "end_encounter":
            encounter = self._active_encounter(state)
            if encounter is not None:
                add_encounter_effect(
                    ctx.get("resolution"),
                    mode="leave",
                    title=str(encounter.get("title", "遭遇")),
                    source=str(ctx.get("source", "遭遇结束")),
                )
                state["encounter"] = None
            return False

        if op == "outcome":
            self._set_outcome(
                state,
                str(effect.get("summary", "")),
                str(effect.get("detail", "")),
                roll=ctx.get("check"),
                resolution=ctx.get("resolution"),
                changes=[str(item) for item in effect.get("changes", []) if isinstance(item, str)],
            )
            return True

        if op == "finish_if":
            condition = effect.get("if")
            if isinstance(condition, dict) and self._check_requirement(state, condition, ctx):
                self._finish_game(
                    state,
                    str(effect.get("ending", self._default_ending_id())),
                    str(effect.get("summary", "你的故事结束了。")),
                    roll=ctx.get("check"),
                    resolution=ctx.get("resolution"),
                )
                return True
            return False

        if op == "finish":
            self._finish_game(
                state,
                str(effect.get("ending", self._default_ending_id())),
                str(effect.get("summary", "你的故事结束了。")),
                roll=ctx.get("check"),
                resolution=ctx.get("resolution"),
            )
            return True

        if op == "resolve_victory":
            self._resolve_victory(
                state,
                str(effect.get("method", "sigil")),
                roll=ctx.get("check"),
                resolution=ctx.get("resolution"),
            )
            return True

        return False

    def _apply_effects(self, state: dict[str, Any], effects: list[dict[str, Any]], ctx: dict[str, Any]) -> bool:
        """Apply an ordered list of effects until completion or game over."""
        outcome_written = False
        for effect in effects:
            if not isinstance(effect, dict):
                continue
            outcome_written = self._apply_effect(state, effect, ctx) or outcome_written
            if state.get("game_over"):
                break
        return outcome_written

    def _utility_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate item-use actions from the current inventory."""
        utility_actions: list[dict[str, Any]] = []
        items = self.content.get("items", {})
        inventory = state.get("player", {}).get("inventory", {})

        for item_id, qty in inventory.items():
            if int(qty) <= 0:
                continue
            item = items.get(item_id, {})
            if not item.get("use_effects"):
                continue
            item_name = str(item.get("name", item_id))
            utility_actions.append(
                {
                    "id": f"utility_use_{item_id}",
                    "label": f"使用{item_name}",
                    "hint": str(item.get("description", "消耗品")),
                    "kind": "utility",
                    "utility_item_id": item_id,
                }
            )

        utility_actions.sort(key=lambda action: action["label"])
        return utility_actions

    def _encounter_turn_rules(
        self,
        state: dict[str, Any],
        *,
        resolution: dict[str, Any] | None,
    ) -> None:
        """Run per-turn encounter rules after each successful player action."""
        encounter = self._active_encounter(state)
        if encounter is None:
            return

        template = self._encounter_template(str(encounter.get("id", "")))
        rules = template.get("turn_rules", [])
        if not isinstance(rules, list):
            return

        for rule in rules:
            if not isinstance(rule, dict):
                continue
            condition = rule.get("if")
            if isinstance(condition, dict) and not self._check_requirement(state, condition, {"kind": "encounter_turn"}):
                continue
            effects = rule.get("effects", [])
            if not isinstance(effects, list):
                continue
            self._apply_effects(
                state,
                effects,
                {
                    "resolution": resolution,
                    "source": str(rule.get("source", "遭遇回合")),
                },
            )

        self._sync_encounter_phase(state, resolution=resolution, source="遭遇回合")

    def _action_visible_in_phase(self, action: dict[str, Any], phase_id: str) -> bool:
        """Return whether an encounter action should be shown in the active phase."""
        phase = str(action.get("phase", "")).strip()
        if phase and phase != phase_id:
            return False

        phase_in = action.get("phase_in")
        if isinstance(phase_in, list) and phase_in:
            if phase_id not in {str(value) for value in phase_in}:
                return False

        excluded = action.get("phase_not_in")
        if isinstance(excluded, list) and excluded:
            if phase_id in {str(value) for value in excluded}:
                return False

        return True

    def _encounter_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        """Return actions contributed by the currently active encounter."""
        encounter = self._active_encounter(state)
        if encounter is None:
            return []
        self._normalize_active_encounter(state)
        template = self._encounter_template(str(encounter.get("id", "")))
        phase_id = str(encounter.get("phase", self._default_phase_id(template)))
        actions: list[dict[str, Any]] = []

        global_actions = template.get("actions", [])
        if isinstance(global_actions, list):
            actions.extend([action for action in global_actions if isinstance(action, dict)])

        phase_def = self._phase_def(template, phase_id)
        phase_actions = phase_def.get("actions", [])
        if isinstance(phase_actions, list):
            actions.extend([action for action in phase_actions if isinstance(action, dict)])

        return [action for action in actions if self._action_visible_in_phase(action, phase_id)]

    def _all_actions(self, state: dict[str, Any], node: dict[str, Any]) -> list[dict[str, Any]]:
        """Merge encounter, node, and utility actions into one list."""
        actions: list[dict[str, Any]] = []
        actions.extend(self._encounter_actions(state))
        base_actions = node.get("actions", [])
        if isinstance(base_actions, list):
            actions.extend([action for action in base_actions if isinstance(action, dict)])
        actions.extend(self._utility_actions(state))
        return actions

    def scene_view(self, state: dict[str, Any]) -> dict[str, Any]:
        """Render the current node into the frontend's scene payload."""
        self._normalize_active_encounter(state)
        node_id = str(state.get("progress", {}).get("node_id", ""))
        node = self._node(node_id)
        actions = self._all_actions(state, node)

        return {
            "id": node_id,
            "title": str(node.get("title", "")),
            "text": self._render_text(state, str(node.get("text", ""))),
            "actions": [
                {
                    "id": str(action.get("id", "")),
                    "label": str(action.get("label", "")),
                    "hint": str(action.get("hint", "")),
                    "kind": str(action.get("kind", "story")),
                }
                for action in actions
            ],
        }

    def apply_action(self, state: dict[str, Any], action_id: str) -> None:
        """Execute one player action from the current node or encounter."""
        if state.get("game_over"):
            self._set_outcome(state, "游戏已结束。", "请重新开始或读档。")
            return

        node_id = str(state.get("progress", {}).get("node_id", ""))
        node = self._node(node_id)
        actions = self._all_actions(state, node)

        chosen = next((action for action in actions if str(action.get("id", "")) == action_id), None)
        if not chosen:
            self._set_outcome(state, "无效行动", "当前场景中不存在该行动。")
            return

        utility_item_id = chosen.get("utility_item_id")
        if isinstance(utility_item_id, str) and utility_item_id:
            # Utility actions are synthesized by the interpreter, so they do not
            # have their own effect lists inside the story pack.
            ok, message, resolution = use_utility_item(state, self.content, utility_item_id)
            self._set_outcome(
                state,
                "你使用了一件物品。" if ok else "无法使用该物品。",
                message,
                resolution=resolution,
            )
            if not state.get("game_over"):
                advance_turn(state, self.content, resolution=resolution)
                self._apply_fatal(state, resolution=resolution)
                if not state.get("game_over"):
                    self._refresh_outcome_changes(state)
            return

        requirement = chosen.get("requires")
        if isinstance(requirement, dict) and not self._check_requirement(state, requirement):
            unavailable = chosen.get("on_unavailable")
            if isinstance(unavailable, dict):
                self._set_outcome(
                    state,
                    str(unavailable.get("summary", "当前行动不可执行。")),
                    str(unavailable.get("detail", "你还不满足执行该行动的条件。")),
                )
            else:
                self._set_outcome(state, "当前行动不可执行。", "你还不满足执行该行动的条件。")
            return

        kind = str(chosen.get("kind", "story"))
        outcome_written = False
        action_resolution = build_resolution(
            kind=kind,
            label=str(chosen.get("label", "")),
            tags=[kind],
        )

        if kind in {"check", "save", "contest"}:
            # Check/save/contest share branching semantics, but each resolution
            # kind carries its own fields in the unified payload.
            cfg_key = "check" if kind == "check" else kind
            cfg = chosen.get(cfg_key)
            if not isinstance(cfg, dict):
                self._set_outcome(state, "行动配置错误", f"该{kind}行动缺少必要配置。")
                return

            if kind == "check":
                result = perform_check(state, self.content, cfg)
                success_title = "检定成功"
                fail_title = "检定失败"
            elif kind == "save":
                result = perform_save(state, self.content, cfg)
                success_title = "豁免成功"
                fail_title = "豁免失败"
            else:
                result = perform_contest(state, self.content, cfg)
                success_title = "对抗成功"
                fail_title = "对抗失败"

            branch_key = "on_success" if result.get("success") else "on_failure"
            branch = chosen.get(branch_key)
            effects = branch.get("effects", []) if isinstance(branch, dict) else []
            outcome_written = self._apply_effects(
                state,
                effects if isinstance(effects, list) else [],
                {
                    "check": legacy_roll_payload(result),
                    "resolution": result,
                    "source": str(chosen.get("label", "")),
                },
            )
            if not outcome_written:
                self._set_outcome(
                    state,
                    success_title if result.get("success") else fail_title,
                    "你完成了这次行动。" if result.get("success") else "局势没有按你期待的方式发展。",
                    roll=legacy_roll_payload(result),
                    resolution=result,
                )
            action_resolution = result
        elif kind == "damage":
            damage_cfg = chosen.get("damage")
            if not isinstance(damage_cfg, dict):
                self._set_outcome(state, "行动配置错误", "该伤害行动缺少必要配置。")
                return
            result = perform_damage(state, self.content, damage_cfg)
            branch_key = "on_success" if result.get("success") else "on_failure"
            branch = chosen.get(branch_key)
            effects = branch.get("effects", []) if isinstance(branch, dict) else []
            outcome_written = self._apply_effects(
                state,
                effects if isinstance(effects, list) else [],
                {
                    "resolution": result,
                    "source": str(chosen.get("label", "")),
                },
            )
            if not outcome_written:
                detail = "伤害已生效。" if result.get("success") else "本次伤害没有造成有效影响。"
                self._set_outcome(
                    state,
                    "伤害结算完成",
                    detail,
                    resolution=result,
                )
            action_resolution = result
        else:
            effects = chosen.get("effects", [])
            outcome_written = self._apply_effects(
                state,
                effects if isinstance(effects, list) else [],
                {
                    "resolution": action_resolution,
                    "source": str(chosen.get("label", "")),
                },
            )
            if not outcome_written:
                self._set_outcome(state, "行动完成", "你完成了这个选择。", resolution=action_resolution)

        if not state.get("game_over"):
            advance_turn(state, self.content, resolution=action_resolution)
            self._encounter_turn_rules(state, resolution=action_resolution)
            self._apply_fatal(state, resolution=action_resolution)
            if not state.get("game_over"):
                self._refresh_outcome_changes(state)
