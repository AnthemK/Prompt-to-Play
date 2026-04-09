#!/usr/bin/env python3
"""CLI tools for story-pack maintenance.

Current commands:
- validate: schema/load + reference integrity checks
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow running this script directly from anywhere:
# `python3 backend/tools/story_cli.py ...`
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from game.content import ContentError, StoryRepository  # noqa: E402
from game.story_validation import validate_repository  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    """Build top-level argument parser for story maintenance commands."""
    parser = argparse.ArgumentParser(description="Story pack maintenance CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate story schema and references")
    validate_parser.add_argument(
        "--root",
        type=str,
        default=str(BACKEND_ROOT / "stories"),
        help="Story repository root directory (default: backend/stories)",
    )
    validate_parser.add_argument(
        "--story-id",
        type=str,
        default="",
        help="Validate one story id only (default: validate all packs)",
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output",
    )

    scaffold_parser = subparsers.add_parser("scaffold", help="Create a new minimal story pack scaffold")
    scaffold_parser.add_argument("--id", type=str, required=True, help="Story id (folder name and story.id)")
    scaffold_parser.add_argument(
        "--root",
        type=str,
        default=str(BACKEND_ROOT / "stories"),
        help="Story repository root directory (default: backend/stories)",
    )
    scaffold_parser.add_argument("--title", type=str, default="", help="World title")
    scaffold_parser.add_argument("--chapter", type=str, default="", help="Chapter title")
    scaffold_parser.add_argument("--tone", type=str, default="", help="Story tone summary")
    scaffold_parser.add_argument("--intro", type=str, default="", help="World intro text")
    scaffold_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing scaffold files if target folder already exists",
    )
    return parser


def _print_human_report(issues: list[dict[str, str]], *, story_id: str | None) -> None:
    """Print concise human-readable validation report."""
    scope_text = f"story_id={story_id}" if story_id else "all stories"
    if not issues:
        print(f"[story-cli] validate: PASS ({scope_text})")
        return

    print(f"[story-cli] validate: FAIL ({scope_text})")
    print(f"[story-cli] issues: {len(issues)}")
    for issue in issues:
        print(
            f"- [{issue.get('level', 'error')}] {issue.get('story_id', '?')} "
            f"{issue.get('path', '')} {issue.get('code', 'UNKNOWN')}: {issue.get('message', '')}"
        )


def _run_validate(args: argparse.Namespace) -> int:
    """Run repository validation and return process exit code."""
    root = Path(str(args.root)).resolve()
    selected_story_id = str(args.story_id).strip() or None
    try:
        repository = StoryRepository(root=root)
        issues = validate_repository(repository, story_id=selected_story_id)
    except ContentError as exc:
        payload = {
            "ok": False,
            "error": "content_error",
            "message": str(exc),
            "issues": [],
        }
        if bool(args.json):
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"[story-cli] validate: FAIL ({root})")
            print(f"[story-cli] content load failed: {exc}")
        return 1
    except KeyError:
        payload = {
            "ok": False,
            "error": "story_not_found",
            "message": f"story_id not found: {selected_story_id}",
            "issues": [],
        }
        if bool(args.json):
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"[story-cli] validate: FAIL ({root})")
            print(f"[story-cli] story_id not found: {selected_story_id}")
        return 1

    ok = len(issues) == 0
    if bool(args.json):
        payload: dict[str, Any] = {
            "ok": ok,
            "root": str(root),
            "story_id": selected_story_id,
            "issues": issues,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_human_report(issues, story_id=selected_story_id)
    return 0 if ok else 1


def _safe_story_id(raw_story_id: str) -> str:
    """Normalize one story id for folder and metadata usage."""
    candidate = str(raw_story_id).strip().lower().replace(" ", "_")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    clean = "".join(ch for ch in candidate if ch in allowed)
    return clean


def _scaffold_story_payload(
    *,
    story_id: str,
    title: str,
    chapter_title: str,
    tone: str,
    intro: str,
) -> dict[str, Any]:
    """Build one minimal yet runnable story-pack payload."""
    resolved_title = title or f"{story_id} 世界"
    resolved_chapter = chapter_title or "第一章：未命名冒险"
    resolved_tone = tone or "lightweight-adventure"
    resolved_intro = intro or "这是一个由 scaffold 生成的最小可运行故事包。"
    return {
        "id": story_id,
        "story_interface_version": "1.1",
        "capabilities": {
            "checks": True,
            "saves": False,
            "contests": False,
            "damage": False,
            "healing": False,
            "drain": False,
            "encounters": False,
            "encounter_action_economy": False,
            "encounter_enemy_behaviors": False,
            "encounter_environment": False,
            "debug_trace": True,
        },
        "world": {
            "id": f"{story_id}_world",
            "title": resolved_title,
            "chapter_title": resolved_chapter,
            "tone": resolved_tone,
            "intro": resolved_intro,
            "start_node": "arrival",
            "start_log": "你踏入了新的冒险。",
            "default_shillings": 2,
            "corruption_limit": 10,
            "default_ending_id": "ending_success",
            "fatal_rules": {
                "on_hp_zero": {"ending": "ending_fail", "summary": "你倒在途中。"},
                "on_corruption_limit": {"ending": "ending_fail", "summary": "你在低语中迷失。"},
            },
            "resolve_victory": {
                "default": {"ending": "ending_success", "summary": "你完成了这次冒险。"},
                "rules": [],
            },
        },
        "stat_meta": {
            "might": {"label": "力量"},
            "agility": {"label": "敏捷"},
            "insight": {"label": "洞察"},
            "will": {"label": "意志"},
            "fellowship": {"label": "交涉"},
        },
        "professions": [
            {
                "id": "wanderer",
                "name": "漫游者",
                "summary": "一名基础的探险职业模板。",
                "max_hp": 10,
                "stats": {"might": 2, "agility": 2, "insight": 3, "will": 2, "fellowship": 2},
                "starting_items": ["rations"],
                "perks": ["适配最小模板"],
                "check_bonus": [],
            }
        ],
        "items": {
            "rations": {
                "id": "rations",
                "name": "干粮",
                "type": "consumable",
                "description": "基础补给。",
            }
        },
        "statuses": {},
        "endings": {
            "ending_success": {
                "id": "ending_success",
                "title": "顺利收场",
                "text": "你在本章中存活并完成了目标。",
            },
            "ending_fail": {
                "id": "ending_fail",
                "title": "旅途终止",
                "text": "你未能完成这次冒险。",
            },
        },
        "nodes": {
            "arrival": {
                "title": "启程",
                "text": "你来到一条分岔路，空气里有雨前的潮味。",
                "actions": [
                    {
                        "id": "observe_path",
                        "label": "观察路标",
                        "kind": "check",
                        "check": {"label": "观察检定", "stat": "insight", "dc": 10, "tags": ["scaffold"]},
                        "on_success": {
                            "effects": [
                                {"op": "set_flag", "flag": "found_safe_path", "value": True},
                                {"op": "outcome", "summary": "你看懂了路标。", "detail": "你找到了一条安全小路。"},
                            ]
                        },
                        "on_failure": {
                            "effects": [{"op": "outcome", "summary": "你看不懂路标。", "detail": "只能硬着头皮前进。"}]
                        },
                    },
                    {
                        "id": "finish_journey",
                        "label": "继续前进",
                        "kind": "story",
                        "effects": [
                            {
                                "op": "finish_if",
                                "if": {"path": "progress.flags.found_safe_path", "op": "==", "value": True},
                                "ending": "ending_success",
                                "summary": "你沿着安全路线抵达了目的地。",
                            },
                            {"op": "finish", "ending": "ending_fail", "summary": "你在岔路中迷失了方向。"},
                        ],
                    },
                ],
            }
        },
        "encounters": {},
    }


def _scaffold_readme(story_id: str) -> str:
    """Build a concise author README for one generated story pack."""
    return "\n".join(
        [
            f"# {story_id}（Scaffold）",
            "",
            "这个目录由 `backend/tools/story_cli.py scaffold` 自动生成。",
            "",
            "## 快速开始",
            "",
            "1. 修改 `story.json` 中的 world/professions/nodes/endings",
            "2. 运行校验：",
            "   `python3 backend/tools/story_cli.py validate --story-id " + story_id + "`",
            "3. 启动游戏后在故事包下拉中选择该 id 进行试玩",
            "",
            "## 注意事项",
            "",
            "- `action.id` 建议全局唯一",
            "- 不要引用不存在的 node/item/status/ending/encounter",
            "- 新增 DSL 字段时需同步更新 stories 文档",
            "",
        ]
    )


def _run_scaffold(args: argparse.Namespace) -> int:
    """Generate one minimal story scaffold into the stories repository."""
    root = Path(str(args.root)).resolve()
    if not root.exists():
        print(f"[story-cli] scaffold: root not found: {root}")
        return 1

    raw_story_id = str(args.id)
    story_id = _safe_story_id(raw_story_id)
    if not story_id:
        print(f"[story-cli] scaffold: invalid story id: {raw_story_id!r}")
        return 1

    target_dir = root / story_id
    story_file = target_dir / "story.json"
    readme_file = target_dir / "README.md"
    if target_dir.exists() and not bool(args.force):
        print(f"[story-cli] scaffold: target already exists: {target_dir}")
        print("[story-cli] scaffold: use --force to overwrite files")
        return 1

    target_dir.mkdir(parents=True, exist_ok=True)
    payload = _scaffold_story_payload(
        story_id=story_id,
        title=str(args.title or "").strip(),
        chapter_title=str(args.chapter or "").strip(),
        tone=str(args.tone or "").strip(),
        intro=str(args.intro or "").strip(),
    )
    story_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    readme_file.write_text(_scaffold_readme(story_id), encoding="utf-8")

    print(f"[story-cli] scaffold: created {target_dir}")
    print(f"[story-cli] scaffold: story file -> {story_file}")
    print(f"[story-cli] scaffold: readme file -> {readme_file}")
    print(f"[story-cli] scaffold: next -> python3 backend/tools/story_cli.py validate --story-id {story_id}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for story pack maintenance."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return _run_validate(args)
    if args.command == "scaffold":
        return _run_scaffold(args)
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
