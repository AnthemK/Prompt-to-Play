"""Regression tests for the staged encounter runtime framework."""

from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from backend.game.adventure import StoryDirector


def make_content() -> dict:
    """Return a story fixture with one encounter template."""
    return {
        "world": {
            "start_node": "arrival",
            "default_ending_id": "default_end",
            "corruption_limit": 10,
        },
        "endings": {
            "default_end": {
                "id": "default_end",
                "title": "结束",
                "text": "结束。",
            }
        },
        "nodes": {
            "arrival": {
                "title": "起点",
                "text": "准备行动。",
                "actions": [
                    {
                        "id": "start_encounter",
                        "label": "触发伏击",
                        "kind": "story",
                        "effects": [
                            {"op": "start_encounter", "encounter": "dock_ambush"},
                            {
                                "op": "outcome",
                                "summary": "伏击开始。",
                                "detail": "几名袭击者从货箱后包了上来。",
                            },
                        ],
                    }
                ],
            }
        },
        "encounters": {
            "dock_ambush": {
                "id": "dock_ambush",
                "title": "码头伏击",
                "type": "hostile",
                "summary": "敌人试图切断退路。",
                "goal": "稳住局势并脱离包围",
                "pressure_label": "警戒",
                "pressure_max": 3,
                "enemy": {"name": "伏击者", "intent": "压迫并逼退", "hp": 6, "max_hp": 6},
                "objective": {"label": "稳控进度", "start": 0, "target": 2},
                "phases": {
                    "opening": {
                        "label": "压制阶段",
                        "intent": "试图包围",
                    },
                    "critical": {
                        "label": "破防阶段",
                        "intent": "准备总攻",
                        "actions": [
                            {
                                "id": "encounter_save",
                                "label": "稳住心志",
                                "kind": "save",
                                "save": {"stat": "will", "dc": 11, "label": "惊惧豁免"},
                                "on_success": {"effects": [{"op": "adjust_objective", "amount": 1}]},
                                "on_failure": {"effects": [{"op": "damage", "amount": 1, "source": "惊惧反噬"}]},
                            }
                        ],
                    },
                },
                "phase_rules": [
                    {"if": {"path": "encounter.pressure", "op": ">=", "value": 2}, "phase": "critical"}
                ],
                "turn_rules": [
                    {"if": {"path": "encounter.phase", "op": "==", "value": "opening"}, "effects": [{"op": "adjust_encounter", "amount": 1}]}
                ],
                "actions": [
                    {
                        "id": "encounter_break_line",
                        "label": "击溃阵线",
                        "kind": "damage",
                        "damage": {
                            "target": "enemy",
                            "resource": "hp",
                            "amount": 6,
                            "damage_type": "physical",
                            "label": "击溃阵线",
                            "source": "测试：击溃阵线",
                        },
                    },
                    {
                        "id": "encounter_hold",
                        "label": "稳住阵线",
                        "kind": "contest",
                        "contest": {
                            "stat": "agility",
                            "label": "阵线对抗",
                            "opponent_label": "伏击者",
                            "opponent_modifier": 1,
                            "active_side": "opponent",
                            "tie_policy": "active_loses",
                            "failure_cost": {
                                "mode": "resource_loss",
                                "resource": "hp",
                                "amount": 1,
                                "source": "阵线失守代价",
                            },
                        },
                        "on_success": {
                          "effects": [
                            {"op": "adjust_encounter", "amount": 1},
                            {"op": "adjust_objective", "amount": 1},
                            {
                                "op": "outcome",
                                "summary": "你顶住了第一波冲击。",
                                "detail": "局势仍紧绷，但你争取到了一点空间。",
                            }
                          ]
                        },
                        "on_failure": {
                          "effects": [
                            {"op": "damage", "amount": 2, "source": "伏击者刀伤"},
                            {"op": "outcome", "summary": "你被逼退了。", "detail": "伤口在渗血，局势迅速恶化。"}
                          ]
                        }
                    },
                    {
                        "id": "encounter_escape",
                        "label": "借空隙撤离",
                        "kind": "story",
                        "requires": {"path": "encounter.pressure", "op": ">=", "value": 1},
                        "effects": [
                            {"op": "end_encounter"},
                            {
                                "op": "outcome",
                                "summary": "你成功脱离遭遇。",
                                "detail": "袭击者没能继续缠住你。",
                            },
                        ],
                    },
                ],
                "exit_strategies": [
                    {
                        "id": "finish_defeat",
                        "mode": "defeat",
                        "label": "彻底击溃伏击者",
                        "effects": [
                            {
                                "op": "finish",
                                "ending": "default_end",
                                "summary": "你击溃了伏击者。",
                            }
                        ],
                    }
                ],
            }
        },
    }


def make_state() -> dict:
    """Return a minimal runtime state that can enter an encounter."""
    return {
        "player": {
            "name": "Tester",
            "profession_id": "none",
            "profession_name": "none",
            "stats": {},
            "max_hp": 10,
            "hp": 10,
            "corruption": 0,
            "shillings": 0,
            "inventory": {},
            "statuses": [],
        },
        "progress": {
            "node_id": "arrival",
            "doom": 0,
            "turns": 0,
            "flags": {},
        },
        "log": [],
        "encounter": None,
        "last_outcome": None,
        "game_over": False,
        "ending": None,
    }


class EncounterFlowTests(unittest.TestCase):
    def test_encounter_start_progress_and_end(self) -> None:
        """Encounter actions should appear, advance rounds, and cleanly end."""
        content = make_content()
        state = make_state()
        state["player"]["stats"]["agility"] = 4
        state["player"]["stats"]["will"] = 3
        director = StoryDirector(content)

        director.apply_action(state, "start_encounter")
        self.assertIsNotNone(state["encounter"])
        self.assertEqual(state["encounter"]["id"], "dock_ambush")
        self.assertEqual(state["encounter"]["round"], 1)
        self.assertEqual(state["encounter"]["phase"], "opening")

        scene = director.scene_view(state)
        action_ids = [action["id"] for action in scene["actions"]]
        self.assertIn("encounter_hold", action_ids)
        self.assertIn("encounter_escape", action_ids)

        with patch("backend.game.rules.random.randint", side_effect=[13, 7]):
            director.apply_action(state, "encounter_hold")
        self.assertEqual(state["encounter"]["pressure"], 2)
        self.assertEqual(state["encounter"]["round"], 2)
        self.assertEqual(state["encounter"]["objective"]["progress"], 1)

        # Turn rules push pressure to 2 on round end, then phase rules switch to critical.
        self.assertEqual(state["encounter"]["phase"], "critical")

        scene_after = director.scene_view(state)
        critical_action_ids = [action["id"] for action in scene_after["actions"]]
        self.assertIn("encounter_save", critical_action_ids)

        director.apply_action(state, "encounter_escape")
        self.assertIsNone(state["encounter"])
        self.assertEqual(state["progress"]["turns"], 3)

    def test_contest_failure_cost_applies_before_failure_branch_effects(self) -> None:
        """Contest failure_cost should apply generic penalty on top of failure branch."""
        content = make_content()
        state = make_state()
        state["player"]["stats"]["agility"] = 2
        director = StoryDirector(content)

        director.apply_action(state, "start_encounter")
        with patch("backend.game.rules.random.randint", side_effect=[4, 15]):
            director.apply_action(state, "encounter_hold")

        # on_failure damage 2 + contest failure_cost hp 1
        self.assertEqual(state["player"]["hp"], 7)

    def test_enemy_zero_hp_unlocks_defeat_exit_and_stops_enemy_turn(self) -> None:
        """Encounter should announce defeat unlock and stop enemy behavior once enemy HP hits zero."""
        content = make_content()
        state = make_state()
        director = StoryDirector(content)

        director.apply_action(state, "start_encounter")
        director.apply_action(state, "encounter_break_line")

        self.assertEqual(state["encounter"]["enemy"]["hp"], 0)
        self.assertEqual(state["encounter"]["last_enemy_behavior"], None)
        self.assertEqual(state["last_outcome"]["summary"], "敌方阵线已经崩溃。")
        self.assertIn("击溃收尾窗口", state["last_outcome"]["detail"])

        scene = director.scene_view(state)
        action_ids = [action["id"] for action in scene["actions"]]
        self.assertIn("encounter_exit_finish_defeat", action_ids)
        self.assertIn("敌方阵线已经崩溃。", state["log"])
        resolution = state.get("last_outcome", {}).get("resolution", {})
        self.assertEqual(resolution.get("kind"), "damage")
        effects = resolution.get("effects", [])
        self.assertTrue(any(effect.get("kind") == "encounter" and effect.get("mode") == "exit_unlock" for effect in effects))

    def test_requires_status_gates_encounter_action_visibility(self) -> None:
        """Status-gated encounter actions should appear only after the status is gained."""
        content = make_content()
        content["statuses"] = {
            "battle_focus": {
                "id": "battle_focus",
                "name": "战斗专注",
                "description": "你稳住了呼吸，准备抓住下一次机会。"
            }
        }
        ambush = content["encounters"]["dock_ambush"]
        ambush["actions"] = copy.deepcopy(ambush["actions"]) + [
            {
                "id": "encounter_focus",
                "label": "稳住呼吸",
                "kind": "story",
                "effects": [
                    {"op": "add_status", "status": "battle_focus", "source": "动作：稳住呼吸"},
                    {"op": "outcome", "summary": "你稳住了节奏。"},
                ],
            },
            {
                "id": "encounter_focus_strike",
                "label": "借专注逼近",
                "kind": "story",
                "requires": {"status": "battle_focus", "op": "==", "value": True},
                "effects": [
                    {"op": "adjust_objective", "amount": 1, "source": "状态：战斗专注"},
                    {"op": "outcome", "summary": "你借着专注逼近了一步。"},
                ],
            },
        ]

        state = make_state()
        director = StoryDirector(content)
        director.apply_action(state, "start_encounter")

        scene_before = director.scene_view(state)
        before_map = {action["id"]: action for action in scene_before["actions"]}
        self.assertIn("encounter_focus", before_map)
        self.assertIn("encounter_focus_strike", before_map)
        self.assertFalse(before_map["encounter_focus_strike"]["available"])

        director.apply_action(state, "encounter_focus")

        scene_after = director.scene_view(state)
        after_map = {action["id"]: action for action in scene_after["actions"]}
        self.assertIn("encounter_focus_strike", after_map)
        self.assertTrue(after_map["encounter_focus_strike"]["available"])

    def test_encounter_exit_requirement_ctx_is_reused_on_execution(self) -> None:
        """Synthetic exit actions should use the same requirement context in view and execution."""
        content = make_content()
        content["encounters"]["dock_ambush"]["exit_strategies"] = [
            {
                "id": "ctx_escape",
                "mode": "escape",
                "label": "顺势撤离",
                "requires": {"ctx": "mode", "op": "==", "value": "escape"},
            }
        ]
        state = make_state()
        director = StoryDirector(content)
        director.apply_action(state, "start_encounter")

        scene = director.scene_view(state)
        action_map = {action["id"]: action for action in scene["actions"]}
        self.assertIn("encounter_exit_ctx_escape", action_map)
        self.assertTrue(action_map["encounter_exit_ctx_escape"]["available"])

        director.apply_action(state, "encounter_exit_ctx_escape")
        self.assertIsNone(state["encounter"])

    def test_encounter_action_economy_and_enemy_behavior(self) -> None:
        """Encounter should support continue-actions and per-turn enemy behavior templates."""
        content = make_content()
        ambush = content["encounters"]["dock_ambush"]
        ambush["action_economy"] = {
            "budget": {"main": 1, "bonus": 1, "move": 0},
            "default_cost": {"main": 1, "bonus": 0, "move": 0},
            "max_actions": 2,
        }
        ambush["actions"] = copy.deepcopy(ambush["actions"]) + [
            {
                "id": "encounter_feint",
                "label": "佯攻试探",
                "kind": "story",
                "cost": {"bonus": 1},
                "turn_flow": "continue",
                "effects": [
                    {
                        "op": "outcome",
                        "summary": "你佯攻逼迫对方移动。",
                        "detail": "你暂时争取到侧翼空间。",
                    }
                ],
            }
        ]
        ambush["enemy_behaviors"] = [
            {
                "id": "enemy_suppress",
                "label": "敌方压制射击",
                "effects": [{"op": "damage", "amount": 1, "source": "敌方压制射击"}],
            }
        ]

        state = make_state()
        state["player"]["stats"]["agility"] = 4
        state["player"]["stats"]["will"] = 3
        director = StoryDirector(content)

        director.apply_action(state, "start_encounter")
        self.assertEqual(state["progress"]["turns"], 1)
        self.assertEqual(state["encounter"]["round"], 1)
        # Enemy behavior runs at turn end after start action.
        self.assertEqual(state["player"]["hp"], 9)

        director.apply_action(state, "encounter_feint")
        # Continue-action should not advance turn.
        self.assertEqual(state["progress"]["turns"], 1)
        self.assertEqual(state["encounter"]["round"], 1)
        self.assertEqual(state["encounter"]["economy"]["spent"]["bonus"], 1)

        with patch("backend.game.rules.random.randint", side_effect=[13, 7]):
            director.apply_action(state, "encounter_hold")
        # Main action ends turn, then enemy behavior runs.
        self.assertEqual(state["progress"]["turns"], 2)
        self.assertEqual(state["encounter"]["round"], 2)
        self.assertEqual(state["player"]["hp"], 8)
        self.assertEqual(state["encounter"]["last_enemy_behavior"]["label"], "敌方压制射击")

    def test_encounter_manual_end_turn_action_available(self) -> None:
        """Encounter should expose a manual end-turn action when budget remains."""
        content = make_content()
        content["encounters"]["dock_ambush"]["action_economy"] = {
            "budget": {"main": 1, "bonus": 1, "move": 0},
            "default_cost": {"main": 1, "bonus": 0, "move": 0},
            "max_actions": 2,
        }
        state = make_state()
        director = StoryDirector(content)
        director.apply_action(state, "start_encounter")

        scene = director.scene_view(state)
        action_ids = [action["id"] for action in scene["actions"]]
        self.assertIn("encounter_end_turn", action_ids)

        director.apply_action(state, "encounter_end_turn")
        self.assertEqual(state["progress"]["turns"], 2)

    def test_enemy_behavior_priority_and_cooldown(self) -> None:
        """Enemy behavior should support priority selection with repeat cooldown."""
        content = make_content()
        ambush = content["encounters"]["dock_ambush"]
        ambush["enemy_behavior_selection"] = "priority"
        ambush["enemy_behaviors"] = [
            {
                "id": "fallback_poke",
                "label": "敌方骚扰打击",
                "priority": 1,
                "effects": [{"op": "damage", "amount": 1, "source": "敌方骚扰打击"}],
            },
            {
                "id": "heavy_press",
                "label": "敌方重压突袭",
                "priority": 3,
                "repeat_cooldown": 1,
                "effects": [{"op": "damage", "amount": 2, "source": "敌方重压突袭"}],
            },
        ]
        # Use only explicit end-turn to keep this test deterministic.
        ambush["actions"] = []

        state = make_state()
        director = StoryDirector(content)
        director.apply_action(state, "start_encounter")
        # Round 1 end: highest priority behavior.
        self.assertEqual(state["player"]["hp"], 8)
        self.assertEqual(state["encounter"]["last_enemy_behavior"]["id"], "heavy_press")

        director.apply_action(state, "encounter_end_turn")
        # Round 2 end: heavy behavior is in cooldown, fallback fires.
        self.assertEqual(state["player"]["hp"], 7)
        self.assertEqual(state["encounter"]["last_enemy_behavior"]["id"], "fallback_poke")

        director.apply_action(state, "encounter_end_turn")
        # Round 3 end: heavy behavior available again.
        self.assertEqual(state["player"]["hp"], 5)
        self.assertEqual(state["encounter"]["last_enemy_behavior"]["id"], "heavy_press")

    def test_encounter_environment_adjustment_and_phase_sync(self) -> None:
        """Encounter environment fields should support runtime updates and phase rules."""
        content = make_content()
        ambush = content["encounters"]["dock_ambush"]
        ambush["environment"] = {
            "light": {"label": "光照", "value": 2, "min": 0, "max": 3},
            "hazard": {"label": "危险区", "value": 0, "min": 0, "max": 5},
        }
        ambush["phase_rules"] = [
            {"if": {"path": "encounter.environment.light", "op": "<=", "value": 1}, "phase": "critical"}
        ]
        ambush["actions"] = list(ambush["actions"]) + [
            {
                "id": "encounter_darkening",
                "label": "压暗火盆",
                "kind": "story",
                "effects": [
                    {"op": "adjust_environment", "field": "light", "amount": -2},
                ],
            }
        ]

        state = make_state()
        director = StoryDirector(content)
        director.apply_action(state, "start_encounter")
        self.assertEqual(state["encounter"]["environment"]["light"], 2)

        director.apply_action(state, "encounter_darkening")
        # Clamp to min and trigger phase sync by environment rule.
        self.assertEqual(state["encounter"]["environment"]["light"], 0)
        self.assertEqual(state["encounter"]["phase"], "critical")
        resolution = state.get("last_outcome", {}).get("resolution", {})
        effects = resolution.get("effects", [])
        self.assertTrue(any(effect.get("kind") == "encounter" and effect.get("mode") == "environment" for effect in effects))

    def test_encounter_exit_strategy_visibility(self) -> None:
        """Exit strategy actions should appear only when their mode is available."""
        content = make_content()
        content["encounters"]["dock_ambush"]["exit_strategies"] = [
            {"id": "defeat_route", "mode": "defeat", "label": "彻底击溃敌人"},
            {"id": "escape_route", "mode": "escape", "label": "强行撤离"},
            {"id": "negotiate_route", "mode": "negotiate", "label": "逼迫谈判"},
            {"id": "delay_route", "mode": "delay", "label": "拖到援军抵达"},
        ]
        state = make_state()
        director = StoryDirector(content)
        director.apply_action(state, "start_encounter")

        scene = director.scene_view(state)
        action_ids = [action["id"] for action in scene["actions"]]
        self.assertIn("encounter_exit_escape_route", action_ids)
        self.assertNotIn("encounter_exit_defeat_route", action_ids)
        self.assertNotIn("encounter_exit_negotiate_route", action_ids)
        self.assertNotIn("encounter_exit_delay_route", action_ids)

        state["encounter"]["objective"]["progress"] = 1
        scene = director.scene_view(state)
        action_ids = [action["id"] for action in scene["actions"]]
        self.assertIn("encounter_exit_negotiate_route", action_ids)

        state["encounter"]["objective"]["progress"] = 2
        scene = director.scene_view(state)
        action_ids = [action["id"] for action in scene["actions"]]
        self.assertIn("encounter_exit_delay_route", action_ids)

        state["encounter"]["enemy"]["hp"] = 0
        scene = director.scene_view(state)
        action_ids = [action["id"] for action in scene["actions"]]
        self.assertIn("encounter_exit_defeat_route", action_ids)

    def test_encounter_exit_strategy_execution(self) -> None:
        """Choosing an exit strategy should apply effects, set flag, and leave encounter."""
        content = make_content()
        content["encounters"]["dock_ambush"]["exit_strategies"] = [
            {
                "id": "fallback_escape",
                "mode": "escape",
                "label": "冒险撤离",
                "summary": "你仓促撤离了战场。",
                "detail": "你逃过一劫，但敌人掌握了先手。",
                "set_flag": "dock_escape_used",
                "effects": [
                    {"op": "adjust", "resource": "doom", "amount": 1},
                ],
            }
        ]
        state = make_state()
        director = StoryDirector(content)
        director.apply_action(state, "start_encounter")
        director.apply_action(state, "encounter_exit_fallback_escape")

        self.assertIsNone(state["encounter"])
        self.assertTrue(state["progress"]["flags"]["dock_escape_used"])
        self.assertEqual(state["progress"]["doom"], 1)
        self.assertEqual(state["progress"]["turns"], 2)
        self.assertEqual(state["last_outcome"]["summary"], "你仓促撤离了战场。")
        resolution = state["last_outcome"]["resolution"]
        self.assertEqual(resolution.get("system", {}).get("action"), "encounter_exit")
        self.assertEqual(resolution.get("system", {}).get("mode"), "escape")
        self.assertIn("exit", resolution.get("tags", []))
        self.assertIn("escape", resolution.get("tags", []))


if __name__ == "__main__":
    unittest.main()
