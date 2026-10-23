"""Offline checks for local documentation links and protected project originals."""

from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import unquote, urlsplit

from paths import ROOT


def check() -> tuple[int, list[str]]:
    issues = []
    checked = 0
    link_pattern = re.compile(r"\[[^\]\n]*\]\((<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)")
    for document in sorted(ROOT.rglob("*.md")):
        if "tmp" in document.relative_to(ROOT).parts:
            continue
        text = re.sub(r"```.*?```", "", document.read_text(encoding="utf-8"), flags=re.S)
        for match in link_pattern.finditer(text):
            href = match.group(1).strip("<>")
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            checked += 1
            target = document.parent / unquote(url.path)
            if not target.exists():
                issues.append(f"{document.relative_to(ROOT)}: missing local target {href}")

    for ledger in ROOT.glob("editions/*/*/*/evidence/selection-ledger.json"):
        data = json.loads(ledger.read_text(encoding="utf-8"))
        target = data.get("input_snapshot")
        base = ledger.parents[1] if data.get("schema_version") == 2 else ROOT
        if not target or not (base / target).is_file():
            issues.append(f"{ledger.relative_to(ROOT)}: missing input_snapshot {target!r}")

    manifest = json.loads((ROOT / "docs/maintenance/migrations/2026-10-22-layout.json").read_text(encoding="utf-8"))
    protected = {"NEWS_BRIEFING_STANDARD.md", "News Briefing System(Design Overview).md"}
    for record in manifest["files"]:
        if record["old"] in protected:
            file = ROOT / record["new"]
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != record["before_sha256"]:
                issues.append(f"Protected original changed or missing: {record['new']}")
    return checked, issues


def main() -> None:
    checked, issues = check()
    for issue in issues:
        print("ERROR:", issue)
    print(f"LAYOUT CHECK: local_links={checked} errors={len(issues)}")
    raise SystemExit(bool(issues))


if __name__ == "__main__":
    main()
