"""Regression tests for unified resolution and passive-effect flow."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.game.resolution import build_resolution, resolution_change_lines
from backend.game.rules import (
    advance_turn,
    perform_check,
    perform_contest,
    perform_damage,
    perform_drain,
    perform_healing,
    perform_save,
    use_utility_item,
)


def make_state() -> dict:
    """Build a compact runtime state fixture for rules tests."""
    return {
        "player": {
            "name": "Tester",
            "profession_id": "ritualist",
            "profession_name": "仪式学徒",
            "stats": {
                "might": 2,
                "agility": 2,
                "insight": 3,
                "will": 4,
                "fellowship": 2,
            },
            "max_hp": 10,
            "hp": 8,
            "shield": 0,
            "corruption": 0,
            "shillings": 3,
            "inventory": {"medkit": 1},
            "statuses": [],
        },
        "progress": {
            "node_id": "arrival",
            "doom": 0,
            "turns": 0,
            "flags": {},
        },
        "encounter": None,
        "log": [],
    }


def make_content() -> dict:
    """Build a minimal content fixture that exercises rules behavior."""
    return {
        "world": {"corruption_limit": 10},
        "professions": [
            {
                "id": "ritualist",
                "name": "仪式学徒",
                "stats": {"will": 4},
                "check_bonus": [],
                "trigger_effects": [],
            }
        ],
        "items": {
            "medkit": {
                "id": "medkit",
                "name": "急救包",
                "use_effects": [{"op": "adjust", "resource": "hp", "amount": 2}],
            }
        },
        "statuses": {
            "blessed": {
                "id": "blessed",
                "name": "受祝",
                "consume_on_check": {"stat": "will"},
            },
            "poisoned": {
                "id": "poisoned",
                "name": "中毒",
                "trigger_effects": [
                    {"trigger": "turn_end", "op": "adjust", "resource": "hp", "amount": -2},
                ],
            },
            "armored": {
                "id": "armored",
                "name": "临时护甲",
                "damage_resistances": [
                    {"type": "physical", "reduce": 2, "source": "状态：临时护甲"},
                    {"type": "physical", "percent": 25, "source": "状态：护甲偏转"},
                ],
            },
            "cursed_skin": {
                "id": "cursed_skin",
                "name": "诅咒肤壳",
                "damage_vulnerabilities": [
                    {"type": "physical", "increase": 1, "source": "状态：裂伤"},
                    {"type": "physical", "percent": 50, "source": "状态：诅咒引爆"},
                ],
            },
        },
    }


class RulesResolutionTests(unittest.TestCase):
    def test_perform_check_returns_unified_resolution_and_consumes_status(self) -> None:
        """A will check should resolve and consume the configured status."""
        state = make_state()
        content = make_content()
        state["player"]["statuses"] = ["blessed"]

        with patch("backend.game.rules.random.randint", return_value=9):
            result = perform_check(
                state,
                content,
                {"stat": "will", "dc": 10, "label": "意志检定", "tags": ["ritual"]},
            )

        self.assertEqual(result["kind"], "check")
        self.assertEqual(result["label"], "意志检定")
        self.assertEqual(result["dc"], 10)
        self.assertTrue(result["success"])
        self.assertNotIn("blessed", state["player"]["statuses"])
        self.assertIn("移除状态：受祝", resolution_change_lines(result))
        explain = result.get("explain", {})
        self.assertEqual(explain.get("summary"), "意志检定：成功")
        self.assertTrue(
            any(
                str(entry.get("text", "")).startswith("d20=")
                for entry in explain.get("fragments", [])
                if isinstance(entry, dict)
            )
        )

    def test_advance_turn_applies_trigger_effects_and_records_changes(self) -> None:
        """Turn-end effects should mutate state and appear in resolution text."""
        state = make_state()
        content = make_content()
        state["player"]["statuses"] = ["poisoned"]
        resolution = build_resolution(kind="story", label="等待")

        advance_turn(state, content, resolution=resolution)

        self.assertEqual(state["player"]["hp"], 6)
        self.assertEqual(state["progress"]["turns"], 1)
        self.assertIn("生命 -2", resolution_change_lines(resolution))

    def test_use_utility_item_returns_resolution_and_item_spend(self) -> None:
        """Using an item should spend it and emit unified effect lines."""
        state = make_state()
        content = make_content()

        ok, message, resolution = use_utility_item(state, content, "medkit")

        self.assertTrue(ok)
        self.assertEqual(message, "你使用了急救包。")
        self.assertEqual(state["player"]["hp"], 10)
        self.assertNotIn("medkit", state["player"]["inventory"])
        self.assertEqual(resolution["kind"], "utility")
        self.assertIn("消耗物品：急救包", resolution_change_lines(resolution))
        self.assertIn("生命 +2", resolution_change_lines(resolution))

    def test_perform_save_uses_save_kind_and_roll_fields(self) -> None:
        """Saving throws should return `kind=save` with d20 roll details."""
        state = make_state()
        content = make_content()
        with patch("backend.game.rules.random.randint", return_value=11):
            result = perform_save(
                state,
                content,
                {"stat": "will", "dc": 12, "label": "抗恐惧豁免", "tags": ["fear"]},
            )
        self.assertEqual(result["kind"], "save")
        self.assertEqual(result["label"], "抗恐惧豁免")
        self.assertEqual(result["dc"], 12)
        self.assertEqual(result["roll"], 11)
        self.assertTrue(result["success"])

    def test_perform_check_applies_environment_bonus_rules(self) -> None:
        """Checks should include configured encounter environment modifiers."""
        state = make_state()
        content = make_content()
        state["encounter"] = {
            "id": "env_case",
            "environment": {"light": 0},
            "environment_rules": [
                {
                    "field": "light",
                    "op": "<=",
                    "value": 1,
                    "bonus": 2,
                    "source": "环境：黑暗掩护",
                    "applies_to": ["check"],
                    "stat_in": ["agility"],
                }
            ],
        }
        with patch("backend.game.rules.random.randint", return_value=8):
            result = perform_check(
                state,
                content,
                {"stat": "agility", "dc": 10, "label": "黑暗潜行检定"},
            )
        self.assertTrue(result["success"])
        self.assertIn(
            "环境：黑暗掩护",
            [str(entry.get("source", "")) for entry in result.get("breakdown", []) if isinstance(entry, dict)],
        )

    def test_perform_contest_records_opponent_roll(self) -> None:
        """Contested rolls should include both player and opponent totals."""
        state = make_state()
        content = make_content()
        with patch("backend.game.rules.random.randint", side_effect=[15, 8]):
            result = perform_contest(
                state,
                content,
                {
                    "stat": "agility",
                    "label": "闪避对抗",
                    "opponent_label": "伏击者",
                    "opponent_modifier": 2,
                },
            )
        self.assertEqual(result["kind"], "contest")
        self.assertEqual(result["opponent_label"], "伏击者")
        self.assertEqual(result["roll"], 15)
        self.assertEqual(result["opponent_roll"], 8)
        self.assertEqual(result["opponent_total"], 10)
        self.assertTrue(result["success"])

    def test_perform_contest_tie_policy_and_active_side(self) -> None:
        """Contest ties should resolve via configured tie policy and active side."""
        state = make_state()
        content = make_content()
        with patch("backend.game.rules.random.randint", side_effect=[10, 8]):
            result = perform_contest(
                state,
                content,
                {
                    "stat": "agility",
                    "label": "缠斗对抗",
                    "opponent_label": "黑帮打手",
                    "opponent_modifier": 2,
                    "active_side": "opponent",
                    "tie_policy": "active_loses",
                },
            )
        self.assertEqual(result["margin"], 0)
        self.assertTrue(result["tie"])
        self.assertEqual(result["active_side"], "opponent")
        self.assertEqual(result["tie_policy"], "active_loses")
        # Tie + active=opponent + active_loses => player wins.
        self.assertTrue(result["success"])

    def test_perform_contest_tie_policy_matrix(self) -> None:
        """Contest tie results should match all supported tie-policy variants."""
        state = make_state()
        content = make_content()
        state["player"]["stats"]["agility"] = 2  # stat_modifier=0, easier tie setup

        # Use player_roll=10 and opponent_roll=8 with opponent_modifier=2 => tie.
        cases = [
            {"tie_policy": "player_wins", "active_side": "player", "expected": True},
            {"tie_policy": "player_loses", "active_side": "player", "expected": False},
            {"tie_policy": "active_wins", "active_side": "player", "expected": True},
            {"tie_policy": "active_wins", "active_side": "opponent", "expected": False},
            {"tie_policy": "active_loses", "active_side": "player", "expected": False},
            {"tie_policy": "active_loses", "active_side": "opponent", "expected": True},
            # Invalid policy should fall back to player_wins.
            {"tie_policy": "unknown_policy", "active_side": "opponent", "expected": True, "resolved_policy": "player_wins"},
        ]

        for case in cases:
            with self.subTest(case=case):
                with patch("backend.game.rules.random.randint", side_effect=[10, 8]):
                    result = perform_contest(
                        state,
                        content,
                        {
                            "stat": "agility",
                            "label": "平局策略矩阵",
                            "opponent_label": "矩阵对手",
                            "opponent_modifier": 2,
                            "active_side": case["active_side"],
                            "tie_policy": case["tie_policy"],
                        },
                    )
                self.assertTrue(result["tie"])
                self.assertEqual(result["margin"], 0)
                self.assertEqual(result["success"], case["expected"])
                if "resolved_policy" in case:
                    self.assertEqual(result["tie_policy"], case["resolved_policy"])

    def test_perform_damage_applies_hp_loss_and_records_effect(self) -> None:
        """Damage resolution should reduce HP and emit unified effect lines."""
        state = make_state()
        content = make_content()
        result = perform_damage(
            state,
            content,
            {"resource": "hp", "amount": 3, "label": "爪击伤害", "source": "敌方：爪击"},
        )
        self.assertEqual(result["kind"], "damage")
        self.assertEqual(result["amount"], 3)
        self.assertEqual(result["applied"], 3)
        self.assertEqual(state["player"]["hp"], 5)
        self.assertIn("生命 -3", resolution_change_lines(result))
        explain = result.get("explain", {})
        self.assertEqual(explain.get("summary"), "爪击伤害：成功")
        self.assertTrue(
            any("生效：3" in str(entry.get("text", "")) for entry in explain.get("fragments", []) if isinstance(entry, dict))
        )

    def test_perform_damage_applies_resistance_and_penetration(self) -> None:
        """Damage should honor type resistance, percent mitigation, and penetration."""
        state = make_state()
        content = make_content()
        state["player"]["statuses"] = ["armored"]
        result = perform_damage(
            state,
            content,
            {
                "resource": "hp",
                "amount": 8,
                "damage_type": "physical",
                "penetration": 1,
                "label": "重击伤害",
                "source": "敌方：重锤",
            },
        )
        # 8 base -> flat(2)-pen(1)=1 -> 7 remain -> 25% => 2 mitigated -> 5 applied
        self.assertEqual(result["amount"], 8)
        self.assertEqual(result["mitigated"], 3)
        self.assertEqual(result["applied"], 5)
        self.assertEqual(state["player"]["hp"], 3)
        self.assertEqual(result["damage_type"], "physical")
        self.assertIn("生命（physical） -5", resolution_change_lines(result))

    def test_perform_damage_stacks_resistance_sources_and_caps_percent(self) -> None:
        """Damage resistance should stack across profession/item/status and cap percent at 95%."""
        state = make_state()
        content = make_content()
        content["professions"][0]["damage_resistances"] = [
            {"type": "physical", "reduce": 2, "percent": 60, "source": "职业：钢铁意志"}
        ]
        content["items"]["iron_charm"] = {
            "id": "iron_charm",
            "name": "铁护符",
            "damage_resistances": [{"type": "physical", "reduce": 3, "percent": 50, "source": "物品：铁护符"}],
        }
        state["player"]["inventory"]["iron_charm"] = 1
        state["player"]["statuses"] = ["armored"]  # +reduce2 +percent25

        result = perform_damage(
            state,
            content,
            {
                "resource": "hp",
                "amount": 20,
                "damage_type": "physical",
                "penetration": 4,
                "label": "叠抗伤害",
                "source": "测试：叠抗",
            },
        )
        # flat: (2+3+2)-4=3 => 20->17; percent: (60+50+25)=135 -> cap95 => 16减伤; applied=1
        self.assertEqual(result["resistance_flat"], 7)
        self.assertEqual(result["resistance_percent"], 95)
        self.assertEqual(result["mitigated"], 19)
        self.assertEqual(result["applied"], 1)
        self.assertEqual(state["player"]["hp"], 7)

    def test_perform_damage_penetration_cannot_make_flat_resistance_negative(self) -> None:
        """Penetration above flat resistance should clamp flat mitigation to zero."""
        state = make_state()
        content = make_content()
        state["player"]["statuses"] = ["armored"]  # flat2 + percent25
        result = perform_damage(
            state,
            content,
            {
                "resource": "hp",
                "amount": 8,
                "damage_type": "physical",
                "penetration": 5,
                "label": "过穿透伤害",
                "source": "测试：过穿透",
            },
        )
        # flat2 is fully penetrated => only 25% mitigation on 8 => 2 mitigated, 6 applied.
        self.assertEqual(result["mitigated"], 2)
        self.assertEqual(result["applied"], 6)
        self.assertEqual(state["player"]["hp"], 2)

    def test_perform_damage_can_target_encounter_enemy(self) -> None:
        """Enemy-target damage should reduce encounter enemy HP instead of player HP."""
        state = make_state()
        content = make_content()
        state["encounter"] = {
            "id": "ambush",
            "enemy": {
                "name": "伏击者",
                "hp": 10,
                "max_hp": 10,
                "resistances": [{"type": "fire", "reduce": 1}],
            },
        }
        result = perform_damage(
            state,
            content,
            {
                "target": "enemy",
                "resource": "hp",
                "amount": 4,
                "damage_type": "fire",
                "label": "火焰伤害",
                "source": "火瓶爆裂",
            },
        )
        self.assertEqual(result["target"], "enemy")
        self.assertEqual(result["target_label"], "伏击者")
        self.assertEqual(result["applied"], 3)
        self.assertEqual(state["encounter"]["enemy"]["hp"], 7)
        self.assertIn("伏击者（fire） 生命 -3", resolution_change_lines(result))

    def test_perform_damage_applies_vulnerability_and_shield_absorb(self) -> None:
        """Damage should amplify on vulnerability and then be reduced by shield."""
        state = make_state()
        content = make_content()
        state["player"]["statuses"] = ["armored", "cursed_skin"]
        state["player"]["shield"] = 2
        result = perform_damage(
            state,
            content,
            {
                "resource": "hp",
                "amount": 8,
                "damage_type": "physical",
                "penetration": 1,
                "label": "污染重击",
                "source": "敌方：污染重击",
            },
        )
        # 8 -> resist: flat1 + percent2 => 5; vulnerability: flat1 + percent3 => 9; shield absorbs2 => 7 applied
        self.assertEqual(result["mitigated"], 3)
        self.assertEqual(result["amplified"], 4)
        self.assertEqual(result["shield_absorbed"], 2)
        self.assertEqual(result["applied"], 7)
        self.assertEqual(state["player"]["shield"], 0)
        self.assertEqual(state["player"]["hp"], 1)

    def test_perform_damage_applies_environment_impact_rules(self) -> None:
        """Damage should apply encounter environment flat/percent modifiers."""
        state = make_state()
        content = make_content()
        state["encounter"] = {
            "id": "env_damage",
            "environment": {"hazard": 3, "cover": 1},
            "environment_impact_rules": [
                {
                    "field": "hazard",
                    "op": ">=",
                    "value": 3,
                    "delta": 2,
                    "source": "环境：危险区增伤",
                    "applies_to": ["damage"],
                    "target": "player",
                    "type": "physical",
                },
                {
                    "field": "cover",
                    "op": ">=",
                    "value": 1,
                    "delta": -1,
                    "source": "环境：掩体减伤",
                    "applies_to": ["damage"],
                    "target": "player",
                    "type": "physical",
                },
            ],
        }
        result = perform_damage(
            state,
            content,
            {
                "resource": "hp",
                "amount": 5,
                "damage_type": "physical",
                "label": "环境伤害校验",
                "source": "测试：环境影响",
            },
        )
        # 5 +2 -1 => declared 6
        self.assertEqual(result["amount"], 6)
        self.assertEqual(result["applied"], 6)
        self.assertEqual(state["player"]["hp"], 2)
        breakdown_sources = [str(entry.get("source", "")) for entry in result.get("breakdown", []) if isinstance(entry, dict)]
        self.assertTrue(any("危险区增伤" in source for source in breakdown_sources))
        self.assertTrue(any("掩体减伤" in source for source in breakdown_sources))

    def test_perform_healing_uses_unified_impact_resolution(self) -> None:
        """Healing should restore resources and emit positive change lines."""
        state = make_state()
        content = make_content()
        state["player"]["hp"] = 5
        result = perform_healing(
            state,
            content,
            {"resource": "hp", "amount": 4, "label": "应急治疗", "source": "药剂回复"},
        )
        self.assertEqual(result["kind"], "healing")
        self.assertEqual(result["applied"], 4)
        self.assertEqual(state["player"]["hp"], 9)
        self.assertIn("生命（restorative） +4", resolution_change_lines(result))

    def test_perform_drain_damages_enemy_and_recovers_player(self) -> None:
        """Drain should deal damage first, then recover based on applied damage."""
        state = make_state()
        content = make_content()
        state["player"]["hp"] = 5
        state["encounter"] = {
            "id": "ambush",
            "enemy": {"name": "伏击者", "hp": 10, "max_hp": 10, "shield": 0},
        }
        result = perform_drain(
            state,
            content,
            {
                "target": "enemy",
                "resource": "hp",
                "amount": 4,
                "damage_type": "necrotic",
                "recover_target": "player",
                "recover_resource": "hp",
                "recover_percent": 50,
                "recover_flat": 1,
                "label": "吸血斩击",
                "source": "武器：吸血斩击",
            },
        )
        self.assertEqual(result["kind"], "drain")
        self.assertEqual(result["applied"], 4)
        self.assertEqual(result["drain_recovered"], 3)
        self.assertEqual(state["encounter"]["enemy"]["hp"], 6)
        self.assertEqual(state["player"]["hp"], 8)
        lines = resolution_change_lines(result)
        self.assertIn("伏击者（necrotic） 生命 -4", lines)
        self.assertIn("生命（drain-heal） +3", lines)

    def test_rules_write_debug_trace_entries(self) -> None:
        """Core rule execution should leave structured debug trace entries."""
        state = make_state()
        content = make_content()
        with patch("backend.game.rules.random.randint", return_value=10):
            perform_check(
                state,
                content,
                {"stat": "will", "dc": 11, "label": "调试检定"},
            )

        trace = state.get("debug_trace", {})
        entries = trace.get("entries", []) if isinstance(trace, dict) else []
        self.assertTrue(entries)
        self.assertTrue(any(entry.get("event") == "check.resolved" for entry in entries if isinstance(entry, dict)))


if __name__ == "__main__":
    unittest.main()
