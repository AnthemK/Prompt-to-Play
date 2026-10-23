"""Validate a live BBC/Xinhua technical test report."""

from __future__ import annotations

import argparse
import json
import re
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse


EXPECTED = {
    "bbc-world": "www.bbc.co.uk",
    "bbc-headlines": "www.bbc.co.uk",
    "xinhua-en-latest": "english.news.cn",
    "xinhua-zh-latest": "www.news.cn",
}


from briefing.model import timestamp


def validate(report: dict) -> list[str]:
    try:
        cutoff = timestamp(report["snapshot_as_of"])
        hours = report["run_args"]["max_age_hours"]
        if not isinstance(hours, (int, float)) or hours <= 0:
            return ["max_age_hours must be positive"]
        window = timedelta(hours=hours)
        return _validate_articles(report, cutoff, window)
    except (KeyError, ValueError, TypeError, AttributeError, OverflowError) as exc:
        return [f"Invalid report metadata: {exc}; explicit snapshot_as_of and max_age_hours are required"]


def _validate_articles(report, cutoff, window) -> list[str]:
    statuses = {source["id"]: source for source in report["sources"]}
    issues = []
    for source_id, domain in EXPECTED.items():
        status = statuses.get(source_id)
        if not status or status.get("health_status", status.get("status")) != "ok":
            issues.append(f"{source_id}: no current source status")
            continue
        items = [item for item in report["items"] if item["source_id"] == source_id]
        if not items:
            issues.append(f"{source_id}: no article records")
        for item in items:
            if urlparse(item["url"]).hostname != domain:
                issues.append(f"{source_id}: unexpected article domain")
            if not item.get("article_title_match"):
                issues.append(f"{source_id}: listing/article title mismatch")
            if item.get("article_body_chars", 0) < 80 or item.get("article_paragraphs", 0) < 1:
                issues.append(f"{source_id}: article body missing or too short")
            if not re.fullmatch(r"[0-9a-f]{64}", item.get("article_body_sha256") or ""):
                issues.append(f"{source_id}: invalid body hash")
            published = timestamp(item["published_at"])
            if not cutoff - window <= published <= cutoff:
                issues.append(f"{source_id}: publication outside snapshot window")
            if source_id.startswith("xinhua") and not item.get("agency_credit", source_id == "xinhua-en-latest"):
                issues.append(f"{source_id}: Xinhua agency credit not verified")
            if source_id.startswith("bbc") and not item.get("updated_at"):
                issues.append(f"{source_id}: BBC update timestamp missing")
            if source_id.startswith("bbc") and item.get("updated_at"):
                updated = timestamp(item["updated_at"])
                feed_time = timestamp(item["feed_timestamp_at"])
                if published > updated or feed_time < published - timedelta(seconds=1):
                    issues.append(f"{source_id}: BBC published/update/feed chronology mismatch")
            if source_id == "xinhua-en-latest" and item.get("listing_timestamp_at") != item["published_at"]:
                issues.append("xinhua-en-latest: list/article timestamp mismatch")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate BBC/Xinhua extraction against the snapshot window")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    issues = validate(report)
    for issue in issues:
        print("FAIL", issue)
    if issues:
        raise SystemExit(1)
    print(f"PASS: {len(EXPECTED)} BBC/Xinhua entrances; snapshot window verified")


if __name__ == "__main__":
    main()
