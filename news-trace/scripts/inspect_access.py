"""Inspect public article HTML for access signals without attempting a bypass."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MARKERS = {
    "piano_or_tinypass": rb"piano\.io|tinypass\.com",
    "poool": rb"poool\.fr",
    "sophi": rb"sophi\.io",
    "evolok": rb"evolok\.net",
    "pelcro": rb"pelcro\.com",
    "amp_access": rb"amp-access",
    "paywall_word": rb"paywall|subscribe to read|subscriber.only",
    "jsonld_article_body": rb'"articleBody"\s*:',
    "jsonld_access_free_false": rb'"isAccessibleForFree"\s*:\s*(?:false|"false")',
}

BPC_UPSTREAM = {
    "repository": "https://github.com/Lunatic16/paywall-bypass-skill",
    "reviewed_commit": "77a32379b39ddfb56cd646d5563755bc768287fc",
}


def classify_access(http_status: int | None, markers: list[str], error: str | None = None) -> str:
    """Classify observable access without claiming that a visible body is complete."""
    if error:
        return "request_error"
    if http_status in (401, 402, 403):
        return "authorization_or_request_blocked"
    if http_status != 200:
        return "article_page_unavailable"
    restricted = bool({"jsonld_access_free_false", "paywall_word", "piano_or_tinypass", "poool", "sophi", "evolok", "pelcro"}.intersection(markers))
    if restricted:
        return "public_page_restricted_or_uncertain"
    if "jsonld_article_body" in markers:
        return "public_body_candidate"
    return "public_page_unverified"


def inspect(url: str) -> dict:
    result = {"url": url, "http_status": None, "markers": [], "access_level": None}
    try:
        with urlopen(Request(url, headers={"User-Agent": "NewsTrace/0.1 (access metadata research)"}), timeout=15) as response:
            result["http_status"] = response.status
            body = response.read(300_000)
    except HTTPError as exc:
        result["http_status"] = exc.code
        result["access_level"] = classify_access(exc.code, [])
        return result
    except URLError as exc:
        result["error"] = str(exc.reason)
        result["access_level"] = classify_access(None, [], result["error"])
        return result
    result["markers"] = [name for name, pattern in MARKERS.items() if re.search(pattern, body, re.I)]
    result["html_title_present"] = bool(re.search(rb"<title\b[^>]*>.*?</title>", body, re.I | re.S))
    result["access_level"] = classify_access(result["http_status"], result["markers"])
    result["sample_sha256"] = hashlib.sha256(body).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Manually inspect BPC-style paywall signals in public article HTML")
    parser.add_argument("--report", type=Path, required=True, help="Input snapshot to inspect; pass an explicit file to avoid sampling an outdated issue")
    parser.add_argument("--source-id", action="append", help="Inspect only this source ID; repeat for more sources")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    feed_report = json.loads(args.report.read_text(encoding="utf-8"))
    selected = set(args.source_id or [])
    samples = {}
    for item in feed_report["items"]:
        if not selected or item["source_id"] in selected:
            samples.setdefault(item["source_id"], item["url"])
    result = {"schema_version": 2, "checked_at": datetime.now(timezone.utc).isoformat(), "method": "BPC-derived access triage", "upstream": BPC_UPSTREAM, "note": "Technical signals only; public_body_candidate still requires article-level completeness verification", "articles": []}
    for source_id, url in samples.items():
        result["articles"].append({"source_id": source_id, **inspect(url)})
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
