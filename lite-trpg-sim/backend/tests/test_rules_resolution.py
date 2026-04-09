"""Regression tests for unified resolution and passive-effect flow."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.game.resolution import build_resolution, resolution_change_lines
from backend.game.rules import advance_turn, perform_check, perform_contest, perform_damage, perform_save, use_utility_item


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


if __name__ == "__main__":
    unittest.main()
