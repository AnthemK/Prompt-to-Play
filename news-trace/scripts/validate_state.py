"""Validate compact NewsTrace persistent state using only the standard library."""

from __future__ import annotations

import json
from pathlib import Path


from paths import MEMORY as STATE


def json_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    preferences = json.loads((STATE / "preferences.json").read_text(encoding="utf-8"))
    stories = json.loads((STATE / "story_state.json").read_text(encoding="utf-8"))["stories"]
    events = json_lines(STATE / "event_history.jsonl")
    feedback = json_lines(STATE / "feedback_log.jsonl")
    issues = []

    if preferences.get("stable", {}).get("format", {}).get("target_distinct_events") != 10:
        issues.append("preferences: target_distinct_events must be 10")
    story_ids = [story.get("story_id") for story in stories]
    if None in story_ids or len(story_ids) != len(set(story_ids)):
        issues.append("story_state: missing or duplicate story_id")
    for story in stories:
        if story.get("watch_level") not in {"High", "Medium", "Low"}:
            issues.append(f"story_state: invalid watch_level for {story.get('story_id')}")
    event_ids = [event.get("event_id") for event in events]
    if None in event_ids or len(event_ids) != len(set(event_ids)):
        issues.append("event_history: missing or duplicate event_id")
    for event in events:
        if event.get("global_significance") not in {"S", "A", "B", "C", "D"}:
            issues.append(f"event_history: invalid global_significance for {event.get('event_id')}")
        if event.get("attention") not in {"High", "Medium", "Low"}:
            issues.append(f"event_history: invalid attention for {event.get('event_id')}")
    for entry in feedback:
        if not entry.get("raw_feedback") or not entry.get("interpreted_signal"):
            issues.append("feedback_log: raw feedback and interpretation are required")

    if issues:
        for issue in issues:
            print("P0:", issue)
        raise SystemExit(1)
    active_stories = sum(story.get("status") == "active" for story in stories)
    print(f"STATE CHECK: events={len(events)} stories={len(stories)} active_stories={active_stories} feedback={len(feedback)} P0=0")


if __name__ == "__main__":
    main()
