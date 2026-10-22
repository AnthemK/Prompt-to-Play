"""Recheck old publisher feed candidates without adding them as live sources."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


from paths import CONFIG


def audit(url: str) -> dict:
    result = {"url": url, "http_status": None, "entries": 0, "latest_date": None}
    try:
        with urlopen(Request(url, headers={"User-Agent": "NewsTrace/0.2 (technical feed audit)"}), timeout=15) as response:
            result["http_status"] = response.status
            payload = response.read(600_000)
    except HTTPError as exc:
        result["http_status"] = exc.code
        return result
    except URLError as exc:
        result["error"] = str(exc.reason)
        return result
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        result["error"] = str(exc)
        return result
    entries = root.findall("./channel/item")
    result["entries"] = len(entries)
    dates = []
    for item in entries:
        date = (item.findtext("pubDate") or "").strip()
        if not date:
            link = item.findtext("link") or ""
            match = re.search(r"/(20\d{2})[-/](\d{2})[-/](\d{2})/", link)
            date = "-".join(match.groups()) if match else ""
        if date:
            match = re.search(r"20\d{2}[-/]\d{2}[-/]\d{2}", date)
            if match:
                dates.append(match.group(0).replace("/", "-"))
    result["latest_date"] = max(dates, default=None)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit deprecated RSS endpoints")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = json.loads((CONFIG / "candidate-endpoints.json").read_text(encoding="utf-8"))
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "sources": [{"id": source["id"], **audit(source["url"])} for source in config["feeds"]]}
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
