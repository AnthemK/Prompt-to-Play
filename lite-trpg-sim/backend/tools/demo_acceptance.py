#!/usr/bin/env python3
"""Run acceptance routes against the built-in Demo story pack.

This helper is meant to verify two things at once:

- the Demo story still works as a regression-oriented mechanics pack
- the Demo story still behaves like a compact playable mission

Routes deliberately cover different slices of the experience instead of forcing
every mechanic into one brittle linear script.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow running directly from repository root:
# `python3 backend/tools/demo_acceptance.py`
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from game.engine import GameEngine  # noqa: E402

DEMO_STORY_ID = "demo"


def _action_ids(view: dict[str, Any]) -> list[str]:
    """Extract visible action ids from one engine view payload."""
    actions = view.get("scene", {}).get("actions", [])
    if not isinstance(actions, list):
        return []
    return [str(action.get("id", "")) for action in actions if isinstance(action, dict)]


def _assert_action_available(view: dict[str, Any], action_id: str, route_name: str) -> None:
    """Raise a clear error when one expected action is not currently visible."""
    available = _action_ids(view)
    if action_id in available:
        return
    raise RuntimeError(f"[{route_name}] missing action `{action_id}`; available actions: {available}")


def _run_action(
    engine: GameEngine,
    *,
    session_id: str,
    view: dict[str, Any],
    action_id: str,
    route_name: str,
) -> dict[str, Any]:
    """Execute one visible action and return the updated view."""
    _assert_action_available(view, action_id, route_name)
    return engine.act(session_id, action_id)


def _profession_ids(engine: GameEngine) -> dict[str, str]:
    """Return available Demo profession ids keyed by id."""
    meta = engine.meta(story_id=DEMO_STORY_ID)
    professions = meta.get("professions", [])
    if not isinstance(professions, list) or not professions:
        raise RuntimeError("[bootstrap] demo story has no professions")

    mapping: dict[str, str] = {}
    for profession in professions:
        if not isinstance(profession, dict):
            continue
        profession_id = str(profession.get("id", "")).strip()
        if profession_id:
            mapping[profession_id] = profession_id

    if "warden" not in mapping or "scout" not in mapping:
        raise RuntimeError(f"[bootstrap] expected demo professions `warden` and `scout`, got {sorted(mapping)}")
    return mapping


def _new_demo_session(
    engine: GameEngine,
    route_name: str,
    profession_id: str,
) -> tuple[str, dict[str, Any]]:
    """Start one new Demo session and return `(session_id, initial_view)`."""
    view = engine.new_game(
        player_name=f"Acceptance-{route_name}",
        profession_id=profession_id,
        story_id=DEMO_STORY_ID,
    )
    session_id = str(view.get("session_id", "")).strip()
    if not session_id:
        raise RuntimeError(f"[{route_name}] engine returned empty session id")
    return session_id, view


def _assert_ending(view: dict[str, Any], expected_ending_id: str, route_name: str) -> None:
    """Verify that one route finished with the expected ending id."""
    if not bool(view.get("game_over")):
        raise RuntimeError(f"[{route_name}] route did not finish the game")
    ending = view.get("ending")
    ending_id = str(ending.get("id", "")) if isinstance(ending, dict) else ""
    if ending_id != expected_ending_id:
        raise RuntimeError(f"[{route_name}] expected ending `{expected_ending_id}`, got `{ending_id}`")


def _assert_resolution_kind(view: dict[str, Any], expected_kind: str, route_name: str) -> None:
    """Verify the latest outcome was produced by one expected resolution kind."""
    outcome = view.get("last_outcome")
    resolution = outcome.get("resolution") if isinstance(outcome, dict) else None
    kind = str(resolution.get("kind", "")) if isinstance(resolution, dict) else ""
    if kind != expected_kind:
        raise RuntimeError(f"[{route_name}] expected resolution kind `{expected_kind}`, got `{kind}`")


def _assert_status_present(view: dict[str, Any], status_id: str, route_name: str) -> None:
    """Verify the player currently has one expected status."""
    statuses = view.get("statuses", [])
    if not isinstance(statuses, list):
        raise RuntimeError(f"[{route_name}] invalid statuses payload")
    if any(isinstance(entry, dict) and str(entry.get("id", "")) == status_id for entry in statuses):
        return
    raise RuntimeError(f"[{route_name}] expected status `{status_id}` to be present")


def _assert_status_absent(view: dict[str, Any], status_id: str, route_name: str) -> None:
    """Verify the player no longer has one specific status."""
    statuses = view.get("statuses", [])
    if not isinstance(statuses, list):
        raise RuntimeError(f"[{route_name}] invalid statuses payload")
    if any(isinstance(entry, dict) and str(entry.get("id", "")) == status_id for entry in statuses):
        raise RuntimeError(f"[{route_name}] expected status `{status_id}` to be absent")


def _assert_resolution_mentions(view: dict[str, Any], needle: str, route_name: str) -> None:
    """Verify the latest resolution explain/effects mention one expected token."""
    outcome = view.get("last_outcome")
    resolution = outcome.get("resolution") if isinstance(outcome, dict) else None
    if not isinstance(resolution, dict):
        raise RuntimeError(f"[{route_name}] missing resolution payload")

    haystacks: list[str] = []
    explain = resolution.get("explain")
    if isinstance(explain, dict):
        haystacks.append(str(explain.get("summary", "")))
        fragments = explain.get("fragments", [])
        if isinstance(fragments, list):
            for fragment in fragments:
                if isinstance(fragment, dict):
                    haystacks.append(str(fragment.get("text", "")))

    effects = resolution.get("effects", [])
    if isinstance(effects, list):
        for effect in effects:
            if isinstance(effect, dict):
                haystacks.append(json.dumps(effect, ensure_ascii=False, sort_keys=True))

    if any(needle in text for text in haystacks):
        return
    raise RuntimeError(f"[{route_name}] expected resolution to mention `{needle}`")


def _route_escape(engine: GameEngine, profession_id: str) -> dict[str, Any]:
    """Verify the always-available retreat route."""
    route_name = "escape"
    session_id, view = _new_demo_session(engine, route_name, profession_id)
    view = _run_action(engine, session_id=session_id, view=view, action_id="force_breach", route_name=route_name)
    view = _run_action(
        engine,
        session_id=session_id,
        view=view,
        action_id="encounter_exit_escape_finish",
        route_name=route_name,
    )
    _assert_ending(view, "ending_escape", route_name)
    return {"route": route_name, "session_id": session_id, "ending_id": "ending_escape"}


def _route_negotiate(engine: GameEngine, profession_id: str) -> dict[str, Any]:
    """Verify one non-lethal encounter exit after making real mission progress."""
    route_name = "negotiate"
    session_id, view = _new_demo_session(engine, route_name, profession_id)
    view = _run_action(engine, session_id=session_id, view=view, action_id="force_breach", route_name=route_name)
    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_cut_down", route_name=route_name)
    _assert_resolution_kind(view, "damage", route_name)
    view = _run_action(
        engine,
        session_id=session_id,
        view=view,
        action_id="encounter_exit_negotiate_finish",
        route_name=route_name,
    )
    _assert_ending(view, "ending_compromise", route_name)
    return {"route": route_name, "session_id": session_id, "ending_id": "ending_compromise"}


def _route_delay_with_load(engine: GameEngine, profession_id: str) -> dict[str, Any]:
    """Verify save/load inside the encounter plus the delay exit."""
    route_name = "delay_load"
    session_id, view = _new_demo_session(engine, route_name, profession_id)
    view = _run_action(engine, session_id=session_id, view=view, action_id="force_breach", route_name=route_name)
    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_cut_down", route_name=route_name)

    save_data = engine.save(session_id)
    loaded_view = engine.load(save_data)
    loaded_session_id = str(loaded_view.get("session_id", "")).strip()
    if not loaded_session_id:
        raise RuntimeError(f"[{route_name}] load returned empty session id")

    view = _run_action(
        engine,
        session_id=loaded_session_id,
        view=loaded_view,
        action_id="demo_cut_down",
        route_name=route_name,
    )
    for follow_up in ["demo_cut_down", "demo_shadow_step", "demo_hold_nerve", "encounter_end_turn"]:
        if "encounter_exit_delay_finish" in _action_ids(view):
            break
        if follow_up not in _action_ids(view):
            continue
        view = _run_action(
            engine,
            session_id=loaded_session_id,
            view=view,
            action_id=follow_up,
            route_name=route_name,
        )

    _assert_action_available(view, "encounter_exit_delay_finish", route_name)
    view = _run_action(
        engine,
        session_id=loaded_session_id,
        view=view,
        action_id="encounter_exit_delay_finish",
        route_name=route_name,
    )
    _assert_ending(view, "ending_delay", route_name)
    return {"route": route_name, "session_id": loaded_session_id, "ending_id": "ending_delay"}


def _route_defeat(engine: GameEngine, profession_id: str) -> dict[str, Any]:
    """Verify the true defeat-victory route now reaches the victory ending."""
    route_name = "defeat"
    session_id, view = _new_demo_session(engine, route_name, profession_id)
    view = _run_action(engine, session_id=session_id, view=view, action_id="force_breach", route_name=route_name)
    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_cut_down", route_name=route_name)
    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_cut_down", route_name=route_name)
    view = _run_action(
        engine,
        session_id=session_id,
        view=view,
        action_id="encounter_exit_defeat_finish",
        route_name=route_name,
    )
    _assert_ending(view, "ending_victory", route_name)
    return {"route": route_name, "session_id": session_id, "ending_id": "ending_victory"}


def _route_prepared_entry(engine: GameEngine, profession_id: str) -> dict[str, Any]:
    """Verify the Demo's before_check plus after_check passive lifecycle."""
    route_name = "prepared_entry"
    session_id, view = _new_demo_session(engine, route_name, profession_id)

    view = _run_action(
        engine,
        session_id=session_id,
        view=view,
        action_id="utility_use_route_map",
        route_name=route_name,
    )
    _assert_status_present(view, "mapped_route", route_name)

    view = _run_action(engine, session_id=session_id, view=view, action_id="force_breach", route_name=route_name)
    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_shadow_step", route_name=route_name)
    _assert_resolution_kind(view, "check", route_name)
    _assert_status_absent(view, "mapped_route", route_name)
    _assert_status_absent(view, "opening_edge", route_name)
    _assert_resolution_mentions(view, "先手优势", route_name)
    _assert_resolution_mentions(view, "路线在心", route_name)

    view = _run_action(
        engine,
        session_id=session_id,
        view=view,
        action_id="encounter_exit_escape_finish",
        route_name=route_name,
    )
    _assert_ending(view, "ending_escape", route_name)
    return {"route": route_name, "session_id": session_id, "ending_id": "ending_escape"}


def _route_mechanics_mix(engine: GameEngine, profession_id: str) -> dict[str, Any]:
    """Touch the main encounter action kinds in one compact but stable route."""
    route_name = "mechanics_mix"
    session_id, view = _new_demo_session(engine, route_name, profession_id)

    view = _run_action(
        engine,
        session_id=session_id,
        view=view,
        action_id="utility_use_smoke_bomb",
        route_name=route_name,
    )
    view = _run_action(engine, session_id=session_id, view=view, action_id="force_breach", route_name=route_name)

    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_hold_nerve", route_name=route_name)
    _assert_resolution_kind(view, "save", route_name)
    _assert_resolution_mentions(view, "生命 -1", route_name)

    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_field_dress", route_name=route_name)
    _assert_resolution_kind(view, "healing", route_name)
    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_wrest_seal", route_name=route_name)
    _assert_resolution_kind(view, "contest", route_name)

    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_take_cover", route_name=route_name)
    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_siphon_miasma", route_name=route_name)
    _assert_resolution_kind(view, "drain", route_name)

    if bool(view.get("game_over")):
        ending = view.get("ending") if isinstance(view.get("ending"), dict) else {}
        ending_id = str(ending.get("id", ""))
        return {"route": route_name, "session_id": session_id, "ending_id": ending_id}

    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_douse_lamps", route_name=route_name)
    view = _run_action(engine, session_id=session_id, view=view, action_id="demo_cut_down", route_name=route_name)
    _assert_resolution_kind(view, "damage", route_name)

    if bool(view.get("game_over")):
        ending = view.get("ending") if isinstance(view.get("ending"), dict) else {}
        ending_id = str(ending.get("id", ""))
        return {"route": route_name, "session_id": session_id, "ending_id": ending_id}

    exit_action = "encounter_exit_defeat_finish" if "encounter_exit_defeat_finish" in _action_ids(view) else "encounter_exit_escape_finish"
    expected = "ending_victory" if exit_action.endswith("defeat_finish") else "ending_escape"
    view = _run_action(engine, session_id=session_id, view=view, action_id=exit_action, route_name=route_name)
    _assert_ending(view, expected, route_name)
    return {"route": route_name, "session_id": session_id, "ending_id": expected}


def _route_fatal_death(engine: GameEngine, profession_id: str) -> dict[str, Any]:
    """Trigger explicit HP-zero fatal handling from the setup node."""
    route_name = "fatal_death"
    session_id, view = _new_demo_session(engine, route_name, profession_id)
    view = _run_action(engine, session_id=session_id, view=view, action_id="fatal_test_death", route_name=route_name)
    _assert_ending(view, "ending_death", route_name)
    return {"route": route_name, "session_id": session_id, "ending_id": "ending_death"}


def _route_fatal_corrupt(engine: GameEngine, profession_id: str) -> dict[str, Any]:
    """Trigger explicit corruption-limit fatal handling from the setup node."""
    route_name = "fatal_corrupt"
    session_id, view = _new_demo_session(engine, route_name, profession_id)
    view = _run_action(engine, session_id=session_id, view=view, action_id="fatal_test_corruption", route_name=route_name)
    _assert_ending(view, "ending_corrupt", route_name)
    return {"route": route_name, "session_id": session_id, "ending_id": "ending_corrupt"}


def run_acceptance() -> list[dict[str, Any]]:
    """Execute all configured acceptance routes and return compact summaries."""
    engine = GameEngine()
    professions = _profession_ids(engine)
    results = [
        _route_escape(engine, professions["warden"]),
        _route_negotiate(engine, professions["warden"]),
        _route_delay_with_load(engine, professions["warden"]),
        _route_defeat(engine, professions["warden"]),
        _route_prepared_entry(engine, professions["scout"]),
        _route_mechanics_mix(engine, professions["warden"]),
        _route_fatal_death(engine, professions["warden"]),
        _route_fatal_corrupt(engine, professions["warden"]),
    ]

    # Pull one debug snapshot per route to ensure diagnostic payloads remain useful.
    for result in results:
        session_id = str(result.get("session_id", ""))
        debug_data = engine.debug_trace(session_id, limit=20)
        entries = debug_data.get("entries", [])
        if not isinstance(entries, list) or not entries:
            raise RuntimeError(f"[{result.get('route', '?')}] empty debug trace entries")

    return results


def _build_parser() -> argparse.ArgumentParser:
    """Build command-line parser for the acceptance helper."""
    parser = argparse.ArgumentParser(description="Run built-in demo acceptance routes")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON payload",
    )
    return parser


def main() -> int:
    """CLI entrypoint."""
    parser = _build_parser()
    args = parser.parse_args()
    try:
        results = run_acceptance()
    except Exception as exc:  # pragma: no cover - CLI error branch
        payload = {"ok": False, "error": str(exc)}
        if bool(args.json):
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("[demo-acceptance] FAIL")
            print(f"- {exc}")
        return 1

    payload = {"ok": True, "routes": results}
    if bool(args.json):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("[demo-acceptance] PASS")
        for route in results:
            print(f"- {route['route']}: {route['ending_id']} (session={route['session_id']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
