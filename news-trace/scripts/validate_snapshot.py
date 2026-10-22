"""Validate a NewsTrace collection snapshot and print a compact severity summary."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path


def validate(report: dict) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    required = ("schema_version", "snapshot_as_of", "completed_at", "run_args", "sources", "items")
    for key in required:
        if key not in report:
            findings.append(("P0", f"missing top-level field: {key}"))
    if any(level == "P0" for level, _ in findings):
        return findings

    try:
        snapshot_at = datetime.fromisoformat(report["snapshot_as_of"])
        completed_at = datetime.fromisoformat(report["completed_at"])
        window = timedelta(hours=report["run_args"]["max_age_hours"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        findings.append(("P0", f"invalid snapshot timing metadata: {exc}"))
        return findings
    if completed_at < snapshot_at:
        findings.append(("P0", "completed_at precedes snapshot_as_of"))

    seen = set()
    for item in report["items"]:
        key = (item.get("publisher"), item.get("id") or item.get("url"))
        if key in seen:
            findings.append(("P0", f"duplicate emitted item: {key[1]}"))
        seen.add(key)
        try:
            published = datetime.fromisoformat(item["published_at"])
        except (KeyError, TypeError, ValueError):
            findings.append(("P0", f"invalid publication time: {item.get('url', '<unknown>')}"))
            continue
        if not snapshot_at - window <= published <= snapshot_at:
            findings.append(("P0", f"item outside snapshot window: {item.get('url', '<unknown>')}"))

    if report["schema_version"] >= 5:
        for source in report["sources"]:
            for key in ("health_status", "contribution_status", "emit_enabled"):
                if key not in source:
                    findings.append(("P0", f"{source.get('id', '<unknown>')}: missing {key}"))
        reached = [source.get("id", "<unknown>") for source in report["sources"] if source.get("retrieval_limit_reached")]
        if reached:
            findings.append(("P1", f"retrieval limit reached by {len(reached)} source(s); coverage may be incomplete"))
        summary = report.get("summary")
        if not summary or summary.get("candidate_items") != len(report["items"]):
            findings.append(("P0", "summary candidate count does not match emitted items"))
    else:
        findings.append(("P2", "legacy snapshot schema; health/contribution distinction unavailable"))
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a NewsTrace collection snapshot")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    findings = validate(report)
    counts = {level: sum(item_level == level for item_level, _ in findings) for level in ("P0", "P1", "P2")}
    print(f"CHECK: P0={counts['P0']} P1={counts['P1']} P2={counts['P2']}")
    for level, message in findings:
        print(f"{level}: {message}")
    if counts["P0"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
