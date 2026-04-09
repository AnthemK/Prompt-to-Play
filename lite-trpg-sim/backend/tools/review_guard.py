#!/usr/bin/env python3
"""Repository hygiene checks for local pre-review / pre-commit use.

Current checks:
- doc-sync: if runtime/frontend/story DSL code changed, require docs to change too
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = PROJECT_ROOT.name

# If these paths changed, we treat it as "implementation changed".
CODE_PATH_PREFIXES = (
    "backend/game/",
    "backend/server.py",
    "backend/tools/",
    "frontend/",
)

# At least one of these paths should also change when code changes.
DOC_PATH_PREFIXES = (
    "README.md",
    "MEMORY.md",
    "docs/",
    "backend/stories/README.md",
    "backend/stories/STORY_INTERFACE.md",
)


def _git_changed_files() -> list[str]:
    """Return changed file paths (staged + unstaged) relative to repository root."""
    cmd = ["git", "status", "--porcelain"]
    completed = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip() or "git status failed")

    changed: list[str] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        # porcelain v1 format: XY<space>path
        # path can include rename arrow "old -> new"; we care about the destination path.
        raw_path = line[3:].strip()
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1].strip()
        if raw_path:
            changed.append(_normalize_changed_path(raw_path))
    return changed


def _normalize_changed_path(path: str) -> str:
    """Normalize git-status path to project-relative format when possible.

    In mono-repo setups, git may emit paths like `lite-trpg-sim/backend/...`.
    We strip the current project folder prefix so matching rules remain stable.
    """
    clean = str(path).strip()
    project_prefix = f"{PROJECT_NAME}/"
    if clean.startswith(project_prefix):
        return clean[len(project_prefix) :]
    return clean


def _match_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    """Return True when a path matches any configured prefix exactly or by directory prefix."""
    for prefix in prefixes:
        if path == prefix or path.startswith(prefix):
            return True
    return False


def run_doc_sync_check() -> int:
    """Check that code changes are accompanied by doc updates."""
    changed = _git_changed_files()
    if not changed:
        print("[review-guard] doc-sync: no changed files, skip.")
        return 0

    code_changed = [path for path in changed if _match_prefix(path, CODE_PATH_PREFIXES)]
    doc_changed = [path for path in changed if _match_prefix(path, DOC_PATH_PREFIXES)]

    if not code_changed:
        print("[review-guard] doc-sync: no tracked code paths changed, pass.")
        return 0

    if doc_changed:
        print("[review-guard] doc-sync: PASS")
        print(f"[review-guard] code changes: {len(code_changed)} | doc changes: {len(doc_changed)}")
        return 0

    print("[review-guard] doc-sync: FAIL")
    print("[review-guard] code changed but no documentation files were updated.")
    print("[review-guard] changed code paths:")
    for path in code_changed:
        print(f"  - {path}")
    print("[review-guard] expected at least one doc change in:")
    for prefix in DOC_PATH_PREFIXES:
        print(f"  - {prefix}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for repository hygiene checks."""
    parser = argparse.ArgumentParser(description="Repository review guard checks")
    parser.add_argument(
        "--doc-sync",
        action="store_true",
        help="Require documentation updates when tracked code paths changed",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.doc_sync:
        parser.print_help()
        return 0
    try:
        return run_doc_sync_check()
    except RuntimeError as exc:
        print(f"[review-guard] error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
