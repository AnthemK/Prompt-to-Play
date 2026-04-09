"""Regression tests for the staged encounter runtime framework."""

from __future__ import annotations

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
                        "id": "encounter_hold",
                        "label": "稳住阵线",
                        "kind": "contest",
                        "contest": {
                            "stat": "agility",
                            "label": "阵线对抗",
                            "opponent_label": "伏击者",
                            "opponent_modifier": 1
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


if __name__ == "__main__":
    unittest.main()
