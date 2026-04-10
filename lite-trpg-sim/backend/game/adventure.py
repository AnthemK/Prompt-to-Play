"""Generic story interpreter for node/action/effect based story packs.

`StoryDirector` is where story-pack data becomes runtime behavior. It should
stay free of story-specific constants and instead expose reusable action/effect
semantics that future settings can consume.
"""

from __future__ import annotations

import random
import re
from typing import Any

from .rules import (
    apply_state_effect,
    advance_turn,
    debug_event,
    has_status,
    log_event,
    perform_check,
    perform_contest,
    perform_damage,
    perform_drain,
    perform_healing,
    perform_save,
    use_utility_item,
)
from .resolution import (
    BreakdownEntry,
    ResolutionPayload,
    add_encounter_effect,
    build_resolution,
    ensure_resolution,
    legacy_roll_payload,
    merge_change_lines,
    refresh_resolution_explain,
)
from .story_contract import (
    IMPACT_ACTION_KINDS,
    IMPACT_EFFECT_OPS,
    ROLL_ACTION_KINDS,
    normalize_encounter_exit_mode,
    required_action_config_key,
)

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

    def _encounter_runtime_and_template(self, state: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Return `(encounter_runtime, encounter_template)` as one explicit pair.

        Naming rule:
        - `encounter_runtime`: mutable state block under `state["encounter"]`
        - `encounter_template`: read-only story-pack definition under
          `content["encounters"][encounter_id]`
        """
        encounter_runtime = self._active_encounter(state)
        if encounter_runtime is None:
            return None, {}
        encounter_template = self._encounter_template(str(encounter_runtime.get("id", "")))
        return encounter_runtime, encounter_template

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

    def _encounter_environment_config(self, template: dict[str, Any]) -> dict[str, Any]:
        """Return one encounter template's environment configuration map."""
        raw = template.get("environment", {})
        if isinstance(raw, dict):
            return raw
        return {}

    def _normalize_encounter_environment(self, encounter: dict[str, Any], template: dict[str, Any]) -> None:
        """Backfill runtime environment values and metadata from template config."""
        configured = self._encounter_environment_config(template)
        configured_rules = template.get("environment_rules", [])
        runtime_env = encounter.get("environment")
        if not isinstance(runtime_env, dict):
            runtime_env = {}
        runtime_meta = encounter.get("environment_meta")
        if not isinstance(runtime_meta, dict):
            runtime_meta = {}

        for raw_key, raw_entry in configured.items():
            field = str(raw_key).strip()
            if not field:
                continue

            if isinstance(raw_entry, dict):
                default_value = raw_entry.get("value", raw_entry.get("default", 0))
                label = str(raw_entry.get("label", field))
                min_value = raw_entry.get("min")
                max_value = raw_entry.get("max")
                value_kind = str(raw_entry.get("kind", "auto")).strip().lower() or "auto"
            else:
                default_value = raw_entry
                label = field
                min_value = None
                max_value = None
                value_kind = "auto"

            runtime_env.setdefault(field, default_value)
            runtime_meta[field] = {
                "label": label,
                "min": min_value if isinstance(min_value, (int, float)) else None,
                "max": max_value if isinstance(max_value, (int, float)) else None,
                "kind": value_kind,
            }

        encounter["environment"] = runtime_env
        encounter["environment_meta"] = runtime_meta
        if isinstance(configured_rules, list):
            encounter.setdefault("environment_rules", [entry for entry in configured_rules if isinstance(entry, dict)])
        else:
            encounter.setdefault("environment_rules", [])
        configured_impact_rules = template.get("environment_impact_rules", [])
        if isinstance(configured_impact_rules, list):
            encounter.setdefault("environment_impact_rules", [entry for entry in configured_impact_rules if isinstance(entry, dict)])
        else:
            encounter.setdefault("environment_impact_rules", [])

    def _encounter_economy_config(self, template: dict[str, Any]) -> dict[str, Any]:
        """Return normalized encounter action-economy config."""
        cfg = template.get("action_economy")
        if isinstance(cfg, dict):
            return cfg
        return {}

    def _normalize_action_cost(self, raw_cost: Any, default_cost: dict[str, int]) -> dict[str, int]:
        """Normalize action cost dictionaries for main/bonus/move budgets."""
        cost: dict[str, int] = {
            "main": int(default_cost.get("main", 0)),
            "bonus": int(default_cost.get("bonus", 0)),
            "move": int(default_cost.get("move", 0)),
        }
        if isinstance(raw_cost, dict):
            for key in ("main", "bonus", "move"):
                if key in raw_cost:
                    cost[key] = max(0, int(raw_cost.get(key, 0)))
        for key in ("main", "bonus", "move"):
            cost[key] = max(0, int(cost.get(key, 0)))
        return cost

    def _encounter_budget(self, template: dict[str, Any]) -> dict[str, int]:
        """Return one turn's encounter-action budget."""
        cfg = self._encounter_economy_config(template)
        raw_budget = cfg.get("budget", {})
        budget = self._normalize_action_cost(raw_budget, {"main": 1, "bonus": 0, "move": 0})
        return budget

    def _encounter_default_cost(self, template: dict[str, Any]) -> dict[str, int]:
        """Return default action cost for encounter actions in this template."""
        cfg = self._encounter_economy_config(template)
        raw_default = cfg.get("default_cost", {"main": 1})
        return self._normalize_action_cost(raw_default, {"main": 1, "bonus": 0, "move": 0})

    def _encounter_max_actions(self, template: dict[str, Any]) -> int:
        """Return max player actions per encounter turn."""
        cfg = self._encounter_economy_config(template)
        return max(1, int(cfg.get("max_actions", 2)))

    def _encounter_action_cost(self, action: dict[str, Any], template: dict[str, Any]) -> dict[str, int]:
        """Resolve one encounter action's cost block."""
        if isinstance(action.get("cost"), dict):
            # Explicit action cost uses sparse override semantics with zero base.
            return self._normalize_action_cost(action.get("cost"), {"main": 0, "bonus": 0, "move": 0})
        return self._normalize_action_cost(action.get("cost"), self._encounter_default_cost(template))

    def _encounter_action_turn_flow(self, action: dict[str, Any], cost: dict[str, int]) -> str:
        """Resolve whether this action should continue the turn or end it."""
        flow = str(action.get("turn_flow", "")).strip().lower()
        if flow in {"continue", "end"}:
            return flow
        # Keep defaults predictable for lite-TRPG flow: main action ends turn.
        if int(cost.get("main", 0)) > 0:
            return "end"
        return "continue"

    def _ensure_encounter_economy(self, encounter: dict[str, Any], template: dict[str, Any]) -> None:
        """Backfill encounter-economy runtime fields and reset them per round."""
        budget = self._encounter_budget(template)
        economy = encounter.get("economy")
        if not isinstance(economy, dict):
            economy = {}
            encounter["economy"] = economy

        economy.setdefault("turn", int(encounter.get("round", 1)))
        economy.setdefault("budget", dict(budget))
        economy.setdefault("spent", {"main": 0, "bonus": 0, "move": 0})
        economy.setdefault("actions_taken", 0)
        economy["budget"] = self._normalize_action_cost(economy.get("budget"), budget)
        economy["spent"] = self._normalize_action_cost(economy.get("spent"), {"main": 0, "bonus": 0, "move": 0})
        economy["actions_taken"] = max(0, int(economy.get("actions_taken", 0)))

        current_round = int(encounter.get("round", 1))
        if int(economy.get("turn", current_round)) != current_round:
            economy["turn"] = current_round
            economy["spent"] = {"main": 0, "bonus": 0, "move": 0}
            economy["actions_taken"] = 0

    def _encounter_remaining_budget(self, encounter: dict[str, Any]) -> dict[str, int]:
        """Return remaining budget in the active encounter turn."""
        economy = encounter.get("economy")
        if not isinstance(economy, dict):
            return {"main": 0, "bonus": 0, "move": 0}
        budget = self._normalize_action_cost(economy.get("budget"), {"main": 0, "bonus": 0, "move": 0})
        spent = self._normalize_action_cost(economy.get("spent"), {"main": 0, "bonus": 0, "move": 0})
        return {
            "main": max(0, int(budget.get("main", 0)) - int(spent.get("main", 0))),
            "bonus": max(0, int(budget.get("bonus", 0)) - int(spent.get("bonus", 0))),
            "move": max(0, int(budget.get("move", 0)) - int(spent.get("move", 0))),
        }

    def _encounter_can_pay_cost(self, encounter: dict[str, Any], cost: dict[str, int]) -> bool:
        """Return whether the encounter economy can afford one action cost."""
        remaining = self._encounter_remaining_budget(encounter)
        return all(int(cost.get(key, 0)) <= int(remaining.get(key, 0)) for key in ("main", "bonus", "move"))

    def _encounter_spend_cost(self, encounter: dict[str, Any], cost: dict[str, int]) -> None:
        """Spend action-economy budget for one performed action."""
        economy = encounter.get("economy")
        if not isinstance(economy, dict):
            return
        spent = self._normalize_action_cost(economy.get("spent"), {"main": 0, "bonus": 0, "move": 0})
        for key in ("main", "bonus", "move"):
            spent[key] = max(0, int(spent.get(key, 0)) + int(cost.get(key, 0)))
        economy["spent"] = spent
        economy["actions_taken"] = max(0, int(economy.get("actions_taken", 0)) + 1)

    def _encounter_behavior_pool(self, state: dict[str, Any], template: dict[str, Any]) -> list[dict[str, Any]]:
        """Return global + phase enemy behavior templates in evaluation order."""
        encounter = self._active_encounter(state)
        if encounter is None:
            return []
        phase_id = str(encounter.get("phase", self._default_phase_id(template)))
        phase_def = self._phase_def(template, phase_id)
        pool: list[dict[str, Any]] = []
        global_behaviors = template.get("enemy_behaviors", [])
        if isinstance(global_behaviors, list):
            pool.extend([entry for entry in global_behaviors if isinstance(entry, dict)])
        phase_behaviors = phase_def.get("enemy_behaviors", [])
        if isinstance(phase_behaviors, list):
            pool.extend([entry for entry in phase_behaviors if isinstance(entry, dict)])
        return pool

    def _encounter_behavior_selection(self, template: dict[str, Any], phase_def: dict[str, Any]) -> str:
        """Resolve enemy behavior selection mode for the current phase."""
        selected = str(phase_def.get("enemy_behavior_selection", "")).strip().lower()
        if not selected:
            selected = str(template.get("enemy_behavior_selection", "first_match")).strip().lower()
        if selected in {"priority", "weighted", "first_match"}:
            return selected
        return "first_match"

    def _run_enemy_behavior(
        self,
        state: dict[str, Any],
        *,
        template: dict[str, Any],
        resolution: ResolutionPayload | None,
    ) -> None:
        """Execute one eligible enemy behavior template each encounter turn.

        Supported selection modes:
        - `first_match` (default): first eligible behavior in list order
        - `priority`: highest-priority eligible behavior, then list order
        - `weighted`: weighted random from eligible behaviors

        Behavior-level fields:
        - `priority`: integer, used by `priority` mode
        - `weight`: integer, used by `weighted` mode
        - `repeat_cooldown`: skip this behavior for N future rounds
        """
        encounter = self._active_encounter(state)
        if encounter is None:
            return
        enemy = encounter.get("enemy")
        if isinstance(enemy, dict) and int(enemy.get("hp", 1)) <= 0:
            # Defeated enemies no longer take encounter turns. The encounter
            # stays active until the player chooses one of the unlocked exits.
            encounter["last_enemy_behavior"] = None
            return
        pool = self._encounter_behavior_pool(state, template)
        if not pool:
            encounter["last_enemy_behavior"] = None
            return

        current_round = max(1, int(encounter.get("round", 1)))
        cooldowns = encounter.get("enemy_behavior_cooldowns")
        if not isinstance(cooldowns, dict):
            cooldowns = {}
            encounter["enemy_behavior_cooldowns"] = cooldowns

        eligible: list[dict[str, Any]] = []
        for index, behavior in enumerate(pool):
            condition = behavior.get("if")
            if isinstance(condition, dict) and not self._check_requirement(state, condition, {"kind": "enemy_behavior"}):
                continue
            behavior_id = str(behavior.get("id", "")).strip() or f"behavior_{index + 1}"
            next_available_round = int(cooldowns.get(behavior_id, 0))
            if current_round < next_available_round:
                continue
            copied = dict(behavior)
            copied["_behavior_id"] = behavior_id
            copied["_priority"] = int(behavior.get("priority", 0))
            copied["_weight"] = max(1, int(behavior.get("weight", 1)))
            eligible.append(copied)

        phase_id = str(encounter.get("phase", self._default_phase_id(template)))
        phase_def = self._phase_def(template, phase_id)
        selection = self._encounter_behavior_selection(template, phase_def)
        chosen: dict[str, Any] | None = None
        if selection == "priority" and eligible:
            chosen = sorted(eligible, key=lambda item: int(item.get("_priority", 0)), reverse=True)[0]
        elif selection == "weighted" and eligible:
            total_weight = sum(max(1, int(item.get("_weight", 1))) for item in eligible)
            roll = random.randint(1, max(1, total_weight))
            cursor = 0
            for behavior in eligible:
                cursor += max(1, int(behavior.get("_weight", 1)))
                if roll <= cursor:
                    chosen = behavior
                    break
        elif eligible:
            chosen = eligible[0]

        if not isinstance(chosen, dict):
            encounter["last_enemy_behavior"] = None
            return

        behavior_id = str(chosen.get("_behavior_id", chosen.get("id", ""))).strip()
        label = str(chosen.get("label", behavior_id or "敌方行动"))
        effects = chosen.get("effects", [])
        if isinstance(effects, list):
            self._apply_effects(
                state,
                effects,
                {
                    "resolution": resolution,
                    "source": str(chosen.get("source", f"敌方行为：{label}")),
                },
            )

        cooldown_turns = max(0, int(chosen.get("repeat_cooldown", 0)))
        if behavior_id and cooldown_turns > 0:
            cooldowns[behavior_id] = current_round + cooldown_turns + 1

        encounter["last_enemy_behavior"] = {
            "id": behavior_id,
            "label": label,
            "selection": selection,
            "priority": int(chosen.get("_priority", 0)),
            "cooldown": cooldown_turns,
        }
        debug_event(
            state,
            event="encounter.enemy_behavior",
            message="Executed one enemy behavior.",
            payload={
                "encounter_id": str(encounter.get("id", "")),
                "behavior_id": behavior_id,
                "label": label,
                "selection": selection,
                "priority": int(chosen.get("_priority", 0)),
                "cooldown": cooldown_turns,
                "round": current_round,
            },
        )
        add_encounter_effect(
            resolution,
            mode="enemy_behavior",
            title=str(encounter.get("title", "遭遇")),
            label=label,
            source=str(chosen.get("source", "敌方行为")),
        )

    def _sync_encounter_phase(
        self,
        state: dict[str, Any],
        *,
        resolution: ResolutionPayload | None = None,
        source: str = "遭遇阶段",
    ) -> None:
        """Evaluate phase rules and synchronize phase-specific runtime fields."""
        encounter_runtime, encounter_template = self._encounter_runtime_and_template(state)
        if encounter_runtime is None:
            return

        default_phase_id = self._default_phase_id(encounter_template)
        previous_phase = str(encounter_runtime.get("phase", "")).strip() or default_phase_id
        selected_phase = previous_phase

        phase_rules = encounter_template.get("phase_rules", [])
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

        phase_def = self._phase_def(encounter_template, selected_phase)
        encounter_runtime["phase"] = selected_phase
        encounter_runtime["phase_label"] = str(phase_def.get("label", selected_phase))
        encounter_runtime["intent"] = str(
            phase_def.get(
                "intent",
                encounter_runtime.get("intent")
                or (encounter_runtime.get("enemy", {}) if isinstance(encounter_runtime.get("enemy"), dict) else {}).get("intent", ""),
            )
        )

        if phase_def.get("summary"):
            encounter_runtime["summary"] = str(phase_def.get("summary", encounter_runtime.get("summary", "")))
        if phase_def.get("goal"):
            encounter_runtime["goal"] = str(phase_def.get("goal", encounter_runtime.get("goal", "")))

        if selected_phase != previous_phase:
            add_encounter_effect(
                resolution,
                mode="phase",
                title=str(encounter_runtime.get("title", "遭遇")),
                label=str(encounter_runtime.get("phase_label", selected_phase)),
                source=source,
            )

    def _normalize_active_encounter(self, state: dict[str, Any]) -> None:
        """Backfill encounter runtime fields for old saves and old templates."""
        encounter_runtime, encounter_template = self._encounter_runtime_and_template(state)
        if encounter_runtime is None:
            return

        encounter_runtime.setdefault("title", str(encounter_template.get("title", encounter_runtime.get("id", "遭遇"))))
        encounter_runtime.setdefault("type", str(encounter_template.get("type", "encounter")))
        encounter_runtime.setdefault("summary", str(encounter_template.get("summary", "")))
        encounter_runtime.setdefault("goal", str(encounter_template.get("goal", "")))
        encounter_runtime.setdefault("round", 0)
        encounter_runtime.setdefault("pressure", int(encounter_template.get("start_pressure", 0)))
        encounter_runtime.setdefault("pressure_label", str(encounter_template.get("pressure_label", "压力")))
        encounter_runtime.setdefault("pressure_max", max(0, int(encounter_template.get("pressure_max", 0))))
        encounter_runtime.setdefault("flags", {})
        self._normalize_encounter_environment(encounter_runtime, encounter_template)

        enemy_template = encounter_template.get("enemy")
        enemy_runtime = encounter_runtime.get("enemy")
        if not isinstance(enemy_runtime, dict):
            enemy_runtime = {}
        if isinstance(enemy_template, dict):
            enemy_runtime.setdefault("name", str(enemy_template.get("name", "敌方")))
            enemy_runtime.setdefault("intent", str(enemy_template.get("intent", "")))
            enemy_max_hp = int(enemy_template.get("max_hp", enemy_template.get("hp", 0)))
            enemy_runtime.setdefault("max_hp", max(0, enemy_max_hp))
            enemy_runtime.setdefault("hp", max(0, int(enemy_template.get("hp", enemy_runtime.get("max_hp", 0)))))
            enemy_runtime.setdefault("shield", max(0, int(enemy_template.get("shield", 0))))
            enemy_runtime.setdefault(
                "resistances",
                [entry for entry in enemy_template.get("resistances", []) if isinstance(entry, dict)]
                if isinstance(enemy_template.get("resistances", []), list)
                else [],
            )
            enemy_runtime.setdefault(
                "vulnerabilities",
                [entry for entry in enemy_template.get("vulnerabilities", []) if isinstance(entry, dict)]
                if isinstance(enemy_template.get("vulnerabilities", []), list)
                else [],
            )
        if enemy_runtime:
            encounter_runtime["enemy"] = enemy_runtime

        objective_template = encounter_template.get("objective")
        objective_runtime = encounter_runtime.get("objective")
        if not isinstance(objective_runtime, dict):
            objective_runtime = {}
        if isinstance(objective_template, dict):
            objective_runtime.setdefault("label", str(objective_template.get("label", "进度")))
            objective_runtime.setdefault("target", max(0, int(objective_template.get("target", 0))))
            objective_runtime.setdefault("progress", max(0, int(objective_template.get("start", 0))))
        if objective_runtime:
            encounter_runtime["objective"] = objective_runtime

        encounter_runtime.setdefault("phase", self._default_phase_id(encounter_template))
        encounter_runtime.setdefault("phase_label", str(encounter_runtime.get("phase", "default")))
        encounter_runtime.setdefault("intent", str((encounter_runtime.get("enemy") or {}).get("intent", "")))
        encounter_runtime.setdefault("last_enemy_behavior", None)
        encounter_runtime.setdefault("enemy_behavior_cooldowns", {})
        encounter_runtime.setdefault("announced_exit_modes", [])
        self._ensure_encounter_economy(encounter_runtime, encounter_template)
        self._sync_encounter_phase(state, source="遭遇同步")

    def _encounter_exit_unlock_text(self, mode: str, encounter_title: str) -> tuple[str, str]:
        """Return one player-facing message for a newly unlocked exit window."""
        if mode == "defeat":
            return ("敌方阵线已经崩溃。", f"{encounter_title}已经出现击溃收尾窗口，你现在可以直接结束这场遭遇。")
        if mode == "delay":
            return ("你已经拿稳局势。", f"{encounter_title}已经满足拖延收尾条件，现在可以选择稳妥收束。")
        if mode == "negotiate":
            return ("你已经逼出了让步空间。", f"{encounter_title}已经出现交涉收尾窗口，现在可以迫使对方让路。")
        return ("遭遇出口已解锁。", f"{encounter_title}已经出现新的收尾窗口。")

    def _sync_encounter_exit_unlocks(
        self,
        state: dict[str, Any],
        *,
        resolution: ResolutionPayload | None = None,
        source: str = "遭遇里程碑",
    ) -> None:
        """Announce newly available encounter-exit windows exactly once."""
        encounter_runtime, encounter_template = self._encounter_runtime_and_template(state)
        if encounter_runtime is None:
            return

        raw_announced = encounter_runtime.get("announced_exit_modes")
        announced = {str(mode) for mode in raw_announced} if isinstance(raw_announced, list) else set()
        configured = encounter_template.get("exit_strategies", [])
        if not isinstance(configured, list):
            return

        title = str(encounter_runtime.get("title", "遭遇"))
        for entry in configured:
            if not isinstance(entry, dict):
                continue
            mode = normalize_encounter_exit_mode(str(entry.get("mode", "")))
            if mode in {"", "escape"} or mode in announced:
                continue

            requirement = entry.get("requires")
            if isinstance(requirement, dict):
                available = self._check_requirement(state, requirement, {"kind": "encounter_exit", "mode": mode})
            else:
                available = self._default_exit_requirement(state, mode)
            if not available:
                continue

            announced.add(mode)
            summary, detail = self._encounter_exit_unlock_text(mode, title)
            self._set_outcome(state, summary, detail, resolution=resolution)
            log_event(state, summary)
            add_encounter_effect(
                resolution,
                mode="exit_unlock",
                title=title,
                label=summary,
                source=source,
            )

        encounter_runtime["announced_exit_modes"] = sorted(announced)

    def _set_outcome(
        self,
        state: dict[str, Any],
        summary: str,
        detail: str,
        *,
        roll: dict[str, Any] | None = None,
        resolution: ResolutionPayload | None = None,
        changes: list[str] | None = None,
    ) -> None:
        """Write the latest player-facing outcome block to state."""
        refreshed = refresh_resolution_explain(resolution)
        merged_changes = merge_change_lines(changes, refreshed)
        state["last_outcome"] = {
            "summary": summary,
            "detail": detail,
            "roll": roll or legacy_roll_payload(refreshed),
            "resolution": refreshed,
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
        refreshed = refresh_resolution_explain(outcome.get("resolution"))
        outcome["resolution"] = refreshed
        outcome["changes"] = merge_change_lines(
            [str(item) for item in outcome.get("changes", []) if isinstance(item, str)],
            refreshed,
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

        if "status" in requirement:
            status_id = str(requirement.get("status", "")).strip()
            present = has_status(state, status_id) if status_id else False
            return self._compare(present, op, right if right is not None else True)

        return False

    def _finish_game(
        self,
        state: dict[str, Any],
        ending_id: str,
        summary: str,
        *,
        roll: dict[str, Any] | None = None,
        resolution: ResolutionPayload | None = None,
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
        resolution: ResolutionPayload | None = None,
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

    def _apply_fatal(self, state: dict[str, Any], *, resolution: ResolutionPayload | None = None) -> None:
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
            debug_event(
                state,
                event="encounter.started",
                message="Started one encounter from template.",
                payload={"encounter_id": encounter_id, "title": encounter_title},
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

        if op == "adjust_environment":
            encounter = self._active_encounter(state)
            if encounter is None:
                return False
            field = str(effect.get("field", "")).strip()
            if not field:
                return False

            env = encounter.setdefault("environment", {})
            env_meta = encounter.setdefault("environment_meta", {})
            meta = env_meta.get(field) if isinstance(env_meta.get(field), dict) else {}
            label = str(meta.get("label", field))
            before = env.get(field, 0)
            after = before
            delta_value: int | None = None

            if "value" in effect:
                after = effect.get("value")
            else:
                try:
                    before_number = int(before)
                except (TypeError, ValueError):
                    before_number = 0
                delta_value = int(effect.get("amount", 0))
                after_number = before_number + delta_value
                min_value = meta.get("min")
                max_value = meta.get("max")
                if isinstance(min_value, (int, float)):
                    after_number = max(int(min_value), after_number)
                if isinstance(max_value, (int, float)):
                    after_number = min(int(max_value), after_number)
                after = after_number
                delta_value = int(after_number - before_number)

            env[field] = after
            resolution = ctx.get("resolution")
            if isinstance(resolution, dict):
                add_encounter_effect(
                    resolution,
                    mode="environment",
                    title=str(encounter.get("title", "遭遇")),
                    delta=delta_value,
                    label=f"{label}: {before} -> {after}",
                    source=str(ctx.get("source", "遭遇环境")),
                )
            self._sync_encounter_phase(
                state,
                resolution=ctx.get("resolution"),
                source=str(ctx.get("source", "遭遇环境")),
            )
            debug_event(
                state,
                event="encounter.environment_adjusted",
                message="Adjusted one encounter environment field.",
                payload={"field": field, "label": label, "before": before, "after": after, "delta": delta_value},
            )
            return False

        if op == "sync_encounter_phase":
            self._sync_encounter_phase(
                state,
                resolution=ctx.get("resolution"),
                source=str(ctx.get("source", "遭遇阶段")),
            )
            return False

        if op in IMPACT_EFFECT_OPS:
            payload_cfg = effect.get(op)
            payload = payload_cfg if isinstance(payload_cfg, dict) else effect
            if not isinstance(payload, dict):
                return False
            if op == "healing":
                damage_result = perform_healing(state, self.content, payload)
            elif op == "drain":
                damage_result = perform_drain(state, self.content, payload)
            else:
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
                encounter_id = str(encounter.get("id", ""))
                encounter_title = str(encounter.get("title", "遭遇"))
                add_encounter_effect(
                    ctx.get("resolution"),
                    mode="leave",
                    title=encounter_title,
                    source=str(ctx.get("source", "遭遇结束")),
                )
                state["encounter"] = None
                debug_event(
                    state,
                    event="encounter.ended",
                    message="Ended active encounter.",
                    payload={"encounter_id": encounter_id, "title": encounter_title},
                )
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
        resolution: ResolutionPayload | None,
    ) -> None:
        """Run per-turn encounter rules after each successful player action."""
        encounter_runtime, encounter_template = self._encounter_runtime_and_template(state)
        if encounter_runtime is None:
            return

        self._ensure_encounter_economy(encounter_runtime, encounter_template)
        rules = encounter_template.get("turn_rules", [])
        if not isinstance(rules, list):
            rules = []

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

        self._sync_encounter_exit_unlocks(state, resolution=resolution, source="遭遇回合")
        self._run_enemy_behavior(state, template=encounter_template, resolution=resolution)
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
        encounter_runtime, encounter_template = self._encounter_runtime_and_template(state)
        if encounter_runtime is None:
            return []
        self._normalize_active_encounter(state)
        encounter_runtime, encounter_template = self._encounter_runtime_and_template(state)
        if encounter_runtime is None:
            return []
        self._ensure_encounter_economy(encounter_runtime, encounter_template)
        phase_id = str(encounter_runtime.get("phase", self._default_phase_id(encounter_template)))
        actions: list[dict[str, Any]] = []

        global_actions = encounter_template.get("actions", [])
        if isinstance(global_actions, list):
            actions.extend([action for action in global_actions if isinstance(action, dict)])

        phase_def = self._phase_def(encounter_template, phase_id)
        phase_actions = phase_def.get("actions", [])
        if isinstance(phase_actions, list):
            actions.extend([action for action in phase_actions if isinstance(action, dict)])
        actions.extend(self._encounter_exit_actions(state, encounter_template))
        visible_actions = [action for action in actions if self._action_visible_in_phase(action, phase_id)]
        affordable_actions: list[dict[str, Any]] = []
        for action in visible_actions:
            cost = self._encounter_action_cost(action, encounter_template)
            if not self._encounter_can_pay_cost(encounter_runtime, cost):
                continue
            copied = dict(action)
            copied["_encounter_action"] = True
            copied["_cost"] = cost
            copied["_turn_flow"] = self._encounter_action_turn_flow(copied, cost)
            affordable_actions.append(copied)

        remaining = self._encounter_remaining_budget(encounter_runtime)
        if any(int(value) > 0 for value in remaining.values()):
            affordable_actions.append(
                {
                    "id": "encounter_end_turn",
                    "label": "结束回合",
                    "hint": "保留行动预算，交由敌方行动。",
                    "kind": "story",
                    "system_action": "end_turn",
                    "_encounter_action": True,
                    "_cost": {"main": 0, "bonus": 0, "move": 0},
                    "_turn_flow": "end",
                }
            )
        return affordable_actions

    def _default_exit_requirement(self, state: dict[str, Any], mode: str) -> bool:
        """Evaluate built-in availability checks for one encounter exit mode."""
        mode = normalize_encounter_exit_mode(mode)
        encounter_runtime = self._active_encounter(state)
        if encounter_runtime is None:
            return False

        enemy = encounter_runtime.get("enemy") if isinstance(encounter_runtime.get("enemy"), dict) else {}
        objective = encounter_runtime.get("objective") if isinstance(encounter_runtime.get("objective"), dict) else {}

        if mode == "defeat":
            return int(enemy.get("hp", 1)) <= 0
        if mode == "delay":
            target = int(objective.get("target", 0))
            progress = int(objective.get("progress", 0))
            return target > 0 and progress >= target
        if mode == "negotiate":
            progress = int(objective.get("progress", 0))
            return progress >= 1
        # Escape is always available as a baseline fallback.
        return True

    def _encounter_exit_actions(self, state: dict[str, Any], encounter_template: dict[str, Any]) -> list[dict[str, Any]]:
        """Build synthetic encounter exit actions from template configuration."""
        configured = encounter_template.get("exit_strategies", [])
        if not isinstance(configured, list):
            return []

        encounter_runtime = self._active_encounter(state)
        if encounter_runtime is None:
            return []

        actions: list[dict[str, Any]] = []
        for index, entry in enumerate(configured, start=1):
            if not isinstance(entry, dict):
                continue
            mode = normalize_encounter_exit_mode(str(entry.get("mode", "")))
            strategy_id = str(entry.get("id", "")).strip() or f"{mode}_{index}"

            requirement = entry.get("requires")
            if isinstance(requirement, dict):
                available = self._check_requirement(state, requirement, {"kind": "encounter_exit", "mode": mode})
            else:
                available = self._default_exit_requirement(state, mode)
            if not available:
                continue

            label = str(entry.get("label", "")).strip() or f"以{mode}结束遭遇"
            hint = str(entry.get("hint", "")).strip() or "执行遭遇出口策略。"
            action = {
                "id": f"encounter_exit_{strategy_id}",
                "label": label,
                "hint": hint,
                "kind": "story",
                "system_action": "encounter_exit",
                "_exit_strategy": entry,
                "_requirement_ctx": {"kind": "encounter_exit", "mode": mode},
                "cost": entry.get("cost"),
                "turn_flow": str(entry.get("turn_flow", "end")),
            }
            if isinstance(requirement, dict):
                # Keep the original requirement on the synthetic action so
                # apply_action can re-check it before execution.
                action["requires"] = requirement
            actions.append(action)
        return actions

    def _default_exit_outcome(self, state: dict[str, Any], mode: str) -> tuple[str, str]:
        """Return default outcome text for one encounter-exit mode."""
        mode = normalize_encounter_exit_mode(mode)
        encounter_runtime = self._active_encounter(state)
        title = str((encounter_runtime or {}).get("title", "遭遇"))
        if mode == "defeat":
            return ("你击溃了敌方。", f"{title}以你的胜利收场。")
        if mode == "delay":
            return ("你成功拖住了局势。", f"在{title}中你守住了关键时间窗口。")
        if mode == "negotiate":
            return ("你迫使对方进入谈判。", f"{title}暂时以脆弱的妥协告一段落。")
        if mode == "escape":
            return ("你脱离了遭遇。", f"你从{title}中撤离，留下未解的风险。")
        return ("你结束了当前遭遇。", f"{title}被你以非常规方式终止。")

    def _all_actions(self, state: dict[str, Any], node: dict[str, Any]) -> list[dict[str, Any]]:
        """Merge encounter, node, and utility actions into one list."""
        actions: list[dict[str, Any]] = []
        actions.extend(self._encounter_actions(state))
        base_actions = node.get("actions", [])
        if isinstance(base_actions, list):
            actions.extend([action for action in base_actions if isinstance(action, dict)])
        actions.extend(self._utility_actions(state))
        return actions

    def _apply_contest_failure_cost(
        self,
        state: dict[str, Any],
        contest_cfg: dict[str, Any],
        resolution: ResolutionPayload,
    ) -> None:
        """Apply optional built-in failure cost for contest actions.

        This is intentionally lightweight for the lite-TRPG baseline: story
        authors can declare one generic penalty directly on the contest config
        without writing a dedicated on_failure effect list.
        """
        failure_cost = contest_cfg.get("failure_cost")
        if not isinstance(failure_cost, dict):
            return

        mode = str(failure_cost.get("mode", "resource_loss")).strip().lower() or "resource_loss"
        source = str(failure_cost.get("source", "对抗失败代价"))
        amount = max(0, int(failure_cost.get("amount", 0)))
        if amount <= 0:
            return

        if mode == "damage":
            damage_payload = {
                "target": str(failure_cost.get("target", "player")),
                "resource": str(failure_cost.get("resource", "hp")),
                "amount": amount,
                "damage_type": str(failure_cost.get("damage_type", "physical")),
                "penetration": int(failure_cost.get("penetration", 0)),
                "source": source,
                "label": str(failure_cost.get("label", "对抗失败代价")),
            }
            damage_result = perform_damage(state, self.content, damage_payload)
            merged = ensure_resolution(resolution)
            if merged is not None:
                merged_effects = merged.setdefault("effects", [])
                for item in damage_result.get("effects", []):
                    merged_effects.append(item)
                merged.setdefault("breakdown", []).append(BreakdownEntry(value=-amount, source=f"{source}(damage)"))
            return

        resource = str(failure_cost.get("resource", "hp")).strip() or "hp"
        before_value = int(state.get("player", {}).get(resource, 0))
        if resource == "doom":
            before_value = int(state.get("progress", {}).get("doom", 0))
        # Resource loss mode is player-side only to keep the config simple.
        apply_state_effect(
            state,
            self.content,
            {
                "op": "adjust",
                "resource": resource,
                "amount": -amount,
                "source": source,
            },
            resolution=resolution,
            default_source=source,
        )
        after_value = int(state.get("player", {}).get(resource, 0))
        if resource == "doom":
            after_value = int(state.get("progress", {}).get("doom", 0))
        merged = ensure_resolution(resolution)
        if merged is not None:
            actual_loss = max(0, before_value - after_value)
            if actual_loss > 0:
                merged.setdefault("breakdown", []).append(
                    BreakdownEntry(value=-actual_loss, source=f"{source}({resource})")
                )

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
                    # Mirror action availability into the view so the frontend
                    # can explain blocked actions before the player clicks.
                    "available": not isinstance(action.get("requires"), dict)
                    or self._check_requirement(state, action.get("requires"), action.get("_requirement_ctx")),
                    "unavailable_detail": (
                        str(action.get("on_unavailable", {}).get("detail", "你还不满足执行该行动的条件。"))
                        if isinstance(action.get("on_unavailable"), dict)
                        else "你还不满足执行该行动的条件。"
                    ),
                    "cost": action.get("_cost") if isinstance(action.get("_cost"), dict) else None,
                    "turn_flow": str(action.get("_turn_flow", "")) if action.get("_encounter_action") else "",
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
            debug_event(
                state,
                event="action.invalid",
                message="Rejected action because it is not present in current scene.",
                payload={"action_id": action_id, "node_id": node_id},
                level="warn",
            )
            return

        debug_event(
            state,
            event="action.start",
            message="Started resolving one player action.",
            payload={
                "action_id": action_id,
                "label": str(chosen.get("label", "")),
                "kind": str(chosen.get("kind", "story")),
                "system_action": str(chosen.get("system_action", "")),
                "node_id": node_id,
            },
        )

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
        requirement_ctx = chosen.get("_requirement_ctx")
        if isinstance(requirement, dict) and not self._check_requirement(state, requirement, requirement_ctx):
            unavailable = chosen.get("on_unavailable")
            if isinstance(unavailable, dict):
                self._set_outcome(
                    state,
                    str(unavailable.get("summary", "当前行动不可执行。")),
                    str(unavailable.get("detail", "你还不满足执行该行动的条件。")),
                )
            else:
                self._set_outcome(state, "当前行动不可执行。", "你还不满足执行该行动的条件。")
            debug_event(
                state,
                event="action.blocked",
                message="Blocked action because requirements are not met.",
                payload={"action_id": action_id, "node_id": node_id},
                level="warn",
            )
            return

        # Keep runtime/template names explicit to avoid state-vs-config confusion.
        encounter_runtime = self._active_encounter(state)
        encounter_template: dict[str, Any] = {}
        encounter_action = bool(chosen.get("_encounter_action")) and encounter_runtime is not None
        encounter_cost = {"main": 0, "bonus": 0, "move": 0}
        encounter_turn_flow = "end"
        if encounter_action and encounter_runtime is not None:
            encounter_template = self._encounter_template(str(encounter_runtime.get("id", "")))
            encounter_cost = (
                chosen.get("_cost")
                if isinstance(chosen.get("_cost"), dict)
                else self._encounter_action_cost(chosen, encounter_template)
            )
            encounter_turn_flow = (
                str(chosen.get("_turn_flow", "")).strip().lower()
                or self._encounter_action_turn_flow(chosen, encounter_cost)
            )
            if not self._encounter_can_pay_cost(encounter_runtime, encounter_cost):
                self._set_outcome(state, "行动预算不足", "当前遭遇回合的行动预算不足以执行该动作。")
                return

        should_advance_turn = True
        kind = str(chosen.get("kind", "story"))
        system_action = str(chosen.get("system_action", "")).strip().lower()
        outcome_written = False
        action_resolution = build_resolution(
            kind=kind,
            label=str(chosen.get("label", "")),
            tags=[kind],
        )

        if system_action == "end_turn":
            action_resolution = build_resolution(
                kind="story",
                label="结束回合",
                success=True,
                tags=["encounter", "turn_end"],
            )
            self._set_outcome(state, "你结束了本回合。", "敌方正在调整阵型。", resolution=action_resolution)
        elif system_action == "encounter_exit":
            # Encounter exit actions are synthetic actions generated from
            # template `exit_strategies`, keeping story data decoupled.
            strategy = chosen.get("_exit_strategy")
            if not isinstance(strategy, dict):
                self._set_outcome(state, "行动配置错误", "遭遇退出策略缺少必要配置。")
                return
            mode = normalize_encounter_exit_mode(str(strategy.get("mode", "")))
            source = str(strategy.get("source", chosen.get("label", "遭遇退出")))

            # Re-check availability defensively in case state changed between
            # scene render and action execution.
            requirement = strategy.get("requires")
            if isinstance(requirement, dict):
                available = self._check_requirement(state, requirement, {"kind": "encounter_exit", "mode": mode})
            else:
                available = self._default_exit_requirement(state, mode)
            if not available:
                self._set_outcome(state, "当前行动不可执行。", "当前遭遇局势尚不满足该退出策略。")
                return
            default_summary, default_detail = self._default_exit_outcome(state, mode)

            action_resolution = build_resolution(
                kind="story",
                label=str(chosen.get("label", "遭遇退出")),
                success=True,
                tags=["encounter", "exit", mode],
            )
            action_resolution["system"] = {"action": "encounter_exit", "mode": mode}
            effects = strategy.get("effects", [])
            outcome_written = self._apply_effects(
                state,
                effects if isinstance(effects, list) else [],
                {
                    "resolution": action_resolution,
                    "source": source,
                },
            )

            # Persist a coarse-grained global flag for post-encounter branching.
            encounter_id = str((encounter_runtime or {}).get("id", "")).strip()
            set_flag = str(strategy.get("set_flag", "")).strip()
            if not set_flag and encounter_id:
                set_flag = f"encounter_exit_{encounter_id}_{mode}"
            if set_flag:
                apply_state_effect(
                    state,
                    self.content,
                    {
                        "op": "set_flag",
                        "flag": set_flag,
                        "value": bool(strategy.get("flag_value", True)),
                        "source": source,
                    },
                    resolution=action_resolution,
                    default_source=source,
                )

            if bool(strategy.get("end_encounter", True)):
                self._apply_effect(
                    state,
                    {"op": "end_encounter"},
                    {
                        "resolution": action_resolution,
                        "source": source,
                    },
                )
            log_event(state, f"遭遇退出：{mode}")

            if not outcome_written:
                self._set_outcome(
                    state,
                    str(strategy.get("summary", default_summary)),
                    str(strategy.get("detail", default_detail)),
                    resolution=action_resolution,
                )
        elif kind in ROLL_ACTION_KINDS:
            # Check/save/contest share branching semantics, but each resolution
            # kind carries its own fields in the unified payload.
            cfg_key = required_action_config_key(kind) or kind
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
                if not result.get("success"):
                    self._apply_contest_failure_cost(state, cfg, result)

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
        elif kind in IMPACT_ACTION_KINDS:
            cfg = chosen.get(kind)
            if not isinstance(cfg, dict):
                self._set_outcome(state, "行动配置错误", f"该{kind}行动缺少必要配置。")
                return
            if kind == "healing":
                result = perform_healing(state, self.content, cfg)
            elif kind == "drain":
                result = perform_drain(state, self.content, cfg)
            else:
                result = perform_damage(state, self.content, cfg)
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
                if kind == "healing":
                    detail = "治疗已生效。" if result.get("success") else "本次治疗没有有效恢复。"
                elif kind == "drain":
                    detail = "吸取已生效。" if result.get("success") else "本次吸取没有造成有效影响。"
                else:
                    detail = "伤害已生效。" if result.get("success") else "本次伤害没有造成有效影响。"
                self._set_outcome(
                    state,
                    "结算完成",
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

        active_encounter_runtime = self._active_encounter(state)
        if encounter_action and active_encounter_runtime is encounter_runtime and not state.get("game_over"):
            self._encounter_spend_cost(active_encounter_runtime, encounter_cost)
            max_actions = self._encounter_max_actions(encounter_template)
            economy = active_encounter_runtime.get("economy", {})
            actions_taken = int(economy.get("actions_taken", 0)) if isinstance(economy, dict) else 0
            remaining = self._encounter_remaining_budget(active_encounter_runtime)
            has_remaining_budget = any(int(value) > 0 for value in remaining.values())
            if system_action == "end_turn":
                should_advance_turn = True
            elif encounter_turn_flow == "continue" and actions_taken < max_actions and has_remaining_budget:
                should_advance_turn = False
            else:
                should_advance_turn = True

        if not state.get("game_over"):
            self._sync_encounter_exit_unlocks(
                state,
                resolution=action_resolution,
                source=str(chosen.get("label", "玩家行动")),
            )
            if should_advance_turn:
                advance_turn(state, self.content, resolution=action_resolution)
                self._encounter_turn_rules(state, resolution=action_resolution)
            self._apply_fatal(state, resolution=action_resolution)
            if not state.get("game_over"):
                self._refresh_outcome_changes(state)
        debug_event(
            state,
            event="action.finish",
            message="Finished resolving one player action.",
            payload={
                "action_id": action_id,
                "game_over": bool(state.get("game_over")),
                "turns": int(state.get("progress", {}).get("turns", 0)),
                "node_id": str(state.get("progress", {}).get("node_id", "")),
            },
        )
