"""Collect publisher-provided feed metadata for a manual NewsTrace trial."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import socket
import ssl
import sys
import time
from http.client import HTTPSConnection
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener, urlopen
from urllib.parse import parse_qs, urlparse, urljoin, urlunparse
import xml.etree.ElementTree as ET

from article_probe import inspect_article
from paths import CONFIG, SCRIPTS


MAX_BYTES = 2_000_000
TAG_RE = re.compile(r"<[^>]+>")
RSS1 = "{http://purl.org/rss/1.0/}"
DC = "{http://purl.org/dc/elements/1.1/}"
SITEMAP = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
NEWS = "{http://www.google.com/schemas/sitemap-news/0.9}"
SHANGHAI = timezone(timedelta(hours=8))


class IPv6FirstHTTPSConnection(HTTPSConnection):
    def connect(self):
        """Try every CDN edge until one passes the normal HTTPS verification."""
        addresses = socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM)
        addresses.sort(key=lambda info: info[0] != socket.AF_INET6)
        last_error = None
        for family, socktype, proto, _, sockaddr in addresses:
            sock = None
            try:
                sock = socket.socket(family, socktype, proto)
                if self.timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                    sock.settimeout(self.timeout)
                if self.source_address:
                    sock.bind(self.source_address)
                sock.connect(sockaddr)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.sock = sock
                if self._tunnel_host:
                    self._tunnel()
                self.sock = self._context.wrap_socket(self.sock, server_hostname=self._tunnel_host or self.host)
                return
            except OSError as exc:
                last_error = exc
                if sock is not None:
                    sock.close()
                self.sock = None
        raise last_error or OSError(f"No addresses for {self.host}")


class IPv6FirstHTTPSHandler(HTTPSHandler):
    def https_open(self, req):
        return self.do_open(IPv6FirstHTTPSConnection, req, context=self._context, check_hostname=self._check_hostname)


_IPV6_FIRST_OPENER = build_opener(ProxyHandler({}), IPv6FirstHTTPSHandler(context=ssl.create_default_context()))
_IPV6_FIRST_HOSTS = {"www.news.cn", "english.news.cn", "www.chinanews.com.cn", "www.infzm.com"}
_NETWORK_MODE = "auto"


def open_verified(request: Request, timeout: int):
    """Use the system network first, with a verified direct fallback for affected hosts."""
    host = urlparse(request.full_url).hostname
    if _NETWORK_MODE == "direct-affected" and host in _IPV6_FIRST_HOSTS:
        return _IPV6_FIRST_OPENER.open(request, timeout=timeout)
    if _NETWORK_MODE == "system" or host not in _IPV6_FIRST_HOSTS:
        return urlopen(request, timeout=timeout)
    try:
        return urlopen(request, timeout=timeout)
    except OSError:
        return _IPV6_FIRST_OPENER.open(request, timeout=timeout)


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", html.unescape(value or ""))).strip()


def child_text(element: ET.Element, *names: str) -> str:
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return clean(found.text)
    return ""


def timestamp(value: str) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def local_timestamp(value: str) -> str | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=SHANGHAI).astimezone(timezone.utc).isoformat()
    except ValueError:
        return None


def article_metadata(url: str, kind: str) -> dict:
    with open_verified(Request(url, headers={"User-Agent": "NewsTrace/0.2 (article verification)"}), timeout=15) as response:
        payload = response.read(700_000)
    return inspect_article(payload, kind)


def parse_feed(payload: bytes, source: dict, limit: int) -> list[dict]:
    root = ET.fromstring(payload)
    entries = root.findall("./channel/item")
    is_atom = False
    is_rdf = False
    is_news_sitemap = False
    if not entries:
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        is_atom = bool(entries)
    if not entries:
        entries = root.findall(f"{RSS1}item")
        is_rdf = bool(entries)
    if not entries:
        entries = root.findall(f"{SITEMAP}url")
        is_news_sitemap = bool(entries)
    if not entries:
        raise ValueError("No RSS, Atom, RDF or news sitemap entries found")

    results = []
    for item in entries if is_news_sitemap else entries[:limit]:
        if is_atom:
            link_node = item.find("{http://www.w3.org/2005/Atom}link[@rel='alternate']")
            if link_node is None:
                link_node = item.find("{http://www.w3.org/2005/Atom}link")
            link = (link_node.get("href") if link_node is not None else "") or ""
            title = child_text(item, "{http://www.w3.org/2005/Atom}title")
            published = child_text(item, "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated")
            summary = child_text(item, "{http://www.w3.org/2005/Atom}summary")
            item_id = child_text(item, "{http://www.w3.org/2005/Atom}id") or link
        elif is_rdf:
            link = child_text(item, f"{RSS1}link")
            title = child_text(item, f"{RSS1}title")
            published = child_text(item, f"{DC}date")
            summary = child_text(item, f"{RSS1}description")
            item_id = child_text(item, f"{DC}identifier") or link
        elif is_news_sitemap:
            link = child_text(item, f"{SITEMAP}loc")
            title = child_text(item, f"{NEWS}news/{NEWS}title")
            published = child_text(item, f"{NEWS}news/{NEWS}publication_date")
            summary = ""
            item_id = link
        else:
            link = child_text(item, "link")
            title = child_text(item, "title")
            published = child_text(item, "pubDate", f"{DC}date")
            summary = child_text(item, "description")
            item_id = child_text(item, "guid") or link
        if not title or not link or not link.startswith(("https://", "http://")):
            continue
        results.append({
            "source_id": source["id"],
            "publisher": source["publisher"],
            "region": source["region"],
            "language": source["language"],
            "category": source.get("category", "global"),
            "evidence": source.get("evidence", ""),
            "id": item_id,
            "title": title,
            "url": link,
            "published_at": timestamp(published),
            "feed_summary": summary[:500],
        })
    if is_news_sitemap:
        results.sort(key=lambda item: item["published_at"] or "", reverse=True)
    return results[:limit]


def parse_hbr_latest(payload: bytes, source: dict, limit: int) -> list[dict]:
    page = payload.decode("utf-8", "replace")
    results = []
    for match in re.finditer(r"<stream-item\b(.*?)</stream-item>", page, re.S | re.I):
        card = match.group(0)
        title_match = re.search(r'data-title="([^"]+)"', card)
        url_match = re.search(r'data-url="([^"]+)"', card)
        date_match = re.search(r"<time[^>]*>(.*?)</time>", card, re.S | re.I)
        if not (title_match and url_match and date_match):
            continue
        try:
            published = datetime.strptime(clean(date_match.group(1)), "%B %d, %Y").replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
        url = "https://hbr.org" + html.unescape(url_match.group(1))
        summary_match = re.search(r'data-summary="([^"]*)"', card)
        results.append({"source_id": source["id"], "publisher": source["publisher"], "region": source["region"], "language": source["language"], "category": source.get("category", "global"), "evidence": source.get("evidence", ""), "id": url, "title": clean(title_match.group(1)), "url": url, "published_at": published, "feed_summary": clean(summary_match.group(1))[:500] if summary_match else ""})
        if len(results) >= limit:
            break
    if not results:
        raise ValueError("No dated HBR article cards found")
    return results


def parse_article_sitemap(payload: bytes, source: dict, limit: int) -> list[dict]:
    root = ET.fromstring(payload)
    urls = []
    for entry in root.findall(f"{SITEMAP}url"):
        url = child_text(entry, f"{SITEMAP}loc")
        modified = child_text(entry, f"{SITEMAP}lastmod")
        if urlparse(url).path.startswith("/article/"):
            urls.append((modified, url))
    urls.sort(reverse=True)
    results = []
    for _, url in urls[: min(limit * 2, 10)]:
        try:
            with open_verified(Request(url, headers={"User-Agent": "NewsTrace/0.1 (article metadata research)"}), timeout=12) as response:
                page = response.read(250_000).decode("utf-8", "replace")
        except OSError:
            continue
        title_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', page, re.I)
        date_match = re.search(r'"datePublished":"([^"]+)"', page)
        if not (title_match and date_match):
            continue
        results.append({"source_id": source["id"], "publisher": source["publisher"], "region": source["region"], "language": source["language"], "category": source.get("category", "global"), "evidence": source.get("evidence", ""), "id": url, "title": clean(title_match.group(1)), "url": url, "published_at": timestamp(date_match.group(1)), "feed_summary": ""})
        if len(results) >= limit:
            break
    if not results:
        raise ValueError("No dated article metadata found in sitemap entries")
    return results


def parse_infzm_home(payload: bytes, source: dict, limit: int) -> list[dict]:
    page = payload.decode("utf-8", "replace")
    paths = list(dict.fromkeys(re.findall(r"/contents/\d+", page)))
    results = []
    for path in paths[: min(max(limit * 3, 12), 18)]:
        url = urljoin(source["url"], path)
        try:
            with open_verified(Request(url, headers={"User-Agent": "NewsTrace/0.1 (article metadata research)"}), timeout=12) as response:
                article = response.read(100_000).decode("utf-8", "replace")
        except OSError:
            continue
        title_match = re.search(r"<title>(.*?)</title>", article, re.S | re.I)
        date_match = re.search(r'data-time="(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"', article)
        if not (title_match and date_match):
            continue
        title = clean(title_match.group(1)).removesuffix(" | 南方周末")
        published = datetime.strptime(date_match.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=SHANGHAI)
        results.append({"source_id": source["id"], "publisher": source["publisher"], "region": source["region"], "language": source["language"], "category": source.get("category", "global"), "evidence": source.get("evidence", ""), "id": url, "title": title, "url": url, "published_at": published.astimezone(timezone.utc).isoformat(), "feed_summary": ""})
    if not results:
        raise ValueError("No dated Southern Weekly article metadata found")
    results.sort(key=lambda item: item["published_at"], reverse=True)
    return results[:limit]


def parse_bing_rss(payload: bytes, source: dict, limit: int) -> list[dict]:
    results = []
    for item in parse_feed(payload, source, 100):
        target = parse_qs(urlparse(item["url"]).query).get("url", [""])[0]
        parsed = urlparse(target)
        if parsed.hostname != "www.cw.com.tw" or not parsed.path.startswith("/article/"):
            continue
        item["url"] = target
        item["id"] = target
        item["feed_summary"] = ""
        item["discovered_via"] = "Bing News RSS"
        results.append(item)
    results.sort(key=lambda item: item["published_at"] or "", reverse=True)
    if not results:
        raise ValueError("No direct CommonWealth article URLs found in news index")
    return results[:limit]


def parse_bbc_rss(payload: bytes, source: dict, limit: int) -> list[dict]:
    results = []
    for item in parse_feed(payload, source, limit * 2):
        try:
            meta = article_metadata(item["url"], "bbc")
        except OSError:
            continue
        published = timestamp(meta["published_raw"])
        if not published or meta["body_chars"] < 80:
            continue
        if clean(item["title"]) != clean(meta["title"]):
            continue
        item["feed_timestamp_at"] = item["published_at"]
        item["published_at"] = published
        item["updated_at"] = timestamp(meta["updated_raw"])
        if item["updated_at"] and item["feed_timestamp_at"]:
            item["feed_article_update_delta_seconds"] = round((datetime.fromisoformat(item["feed_timestamp_at"]) - datetime.fromisoformat(item["updated_at"])).total_seconds())
        item["article_title_match"] = True
        item["article_paragraphs"] = meta["paragraph_count"]
        item["article_body_chars"] = meta["body_chars"]
        item["article_body_sha256"] = meta["body_sha256"]
        item["url"] = urlunparse(urlparse(item["url"])._replace(query="", fragment=""))
        results.append(item)
        if len(results) >= limit:
            break
    if not results:
        raise ValueError("No BBC articles with verified title, date and body found")
    return results


def parse_xinhua_en(payload: bytes, source: dict, limit: int) -> list[dict]:
    page = payload.decode("utf-8", "replace")
    rows = re.findall(r'<div class="tit"><a href="([^"]+)"[^>]*>(.*?)</a><span class="time">([^<]+)</span>', page, re.S | re.I)
    results = []
    for href, title, listed_at in rows[: min(limit * 3, 20)]:
        url = urljoin(source["url"], html.unescape(href))
        try:
            meta = article_metadata(url, "xinhua_en")
        except OSError:
            continue
        published = local_timestamp(meta["published_raw"])
        if not meta["agency_credit"] or not published or meta["body_chars"] < 80 or clean(title) != clean(meta["title"]) or local_timestamp(clean(listed_at)) != published:
            continue
        results.append({"source_id": source["id"], "publisher": source["publisher"], "region": source["region"], "language": source["language"], "category": source["category"], "evidence": source["evidence"], "id": url, "title": meta["title"], "url": url, "published_at": published, "listing_timestamp_at": published, "article_title_match": True, "source_line": meta["source_line"], "agency_credit": True, "article_paragraphs": meta["paragraph_count"], "article_body_chars": meta["body_chars"], "article_body_sha256": meta["body_sha256"], "feed_summary": ""})
        if len(results) >= limit:
            break
    if not results:
        raise ValueError("No recent Xinhua English articles with verified metadata and body found")
    return results


def parse_xinhua_zh(payload: bytes, source: dict, limit: int) -> list[dict]:
    page = payload.decode("utf-8", "replace")
    section = re.search(r'最新播报:</div>\s*<div class="latest-cont">.*?<ul[^>]*>(.*?)</ul>', page, re.S)
    if not section:
        raise ValueError("Xinhua Chinese latest-news section missing")
    links = re.findall(r'<li><a href="([^"]+)"[^>]*>(.*?)</a></li>', section.group(1), re.S | re.I)
    results = []
    for href, listed_title in links[: min(limit * 4, 20)]:
        url = urljoin(source["url"], html.unescape(href))
        try:
            meta = article_metadata(url, "xinhua_zh")
        except OSError:
            continue
        published = local_timestamp(meta["published_raw"])
        if not meta["agency_credit"] or not published or meta["body_chars"] < 80 or clean(listed_title) != clean(meta["title"]):
            continue
        results.append({"source_id": source["id"], "publisher": source["publisher"], "region": source["region"], "language": source["language"], "category": source["category"], "evidence": source["evidence"], "id": url, "title": meta["title"], "url": url, "published_at": published, "article_title_match": True, "source_line": meta["source_line"], "agency_credit": True, "article_paragraphs": meta["paragraph_count"], "article_body_chars": meta["body_chars"], "article_body_sha256": meta["body_sha256"], "feed_summary": ""})
        if len(results) >= limit:
            break
    if not results:
        raise ValueError("No Xinhua Chinese agency articles with verified metadata and body found")
    return results


def collect(source: dict, limit: int) -> list[dict]:
    request = Request(source["url"], headers={"User-Agent": source.get("user_agent", "NewsTrace/0.1 (feed metadata research)")})
    for attempt in range(2):
        try:
            with open_verified(request, timeout=15) as response:
                payload = response.read(MAX_BYTES + 1)
            break
        except OSError:
            if attempt:
                raise
            time.sleep(0.5)
    if len(payload) > MAX_BYTES:
        raise ValueError("Feed exceeded size limit")
    if source.get("kind") == "hbr_latest":
        return parse_hbr_latest(payload, source, limit)
    if source.get("kind") == "article_sitemap":
        return parse_article_sitemap(payload, source, limit)
    if source.get("kind") == "infzm_home":
        return parse_infzm_home(payload, source, limit)
    if source.get("kind") == "bing_rss":
        return parse_bing_rss(payload, source, limit)
    if source.get("kind") == "bbc_rss":
        return parse_bbc_rss(payload, source, limit)
    if source.get("kind") == "xinhua_en":
        return parse_xinhua_en(payload, source, limit)
    if source.get("kind") == "xinhua_zh":
        return parse_xinhua_zh(payload, source, limit)
    return parse_feed(payload, source, limit)


def main() -> None:
    global _NETWORK_MODE
    parser = argparse.ArgumentParser(description="Manually probe NewsTrace's candidate RSS/Atom feeds")
    parser.add_argument("--limit", type=int, default=15, help="Maximum entries per feed")
    parser.add_argument("--max-age-hours", type=int, default=72, help="Only emit articles published within this many hours; source health may use its configured freshness window")
    parser.add_argument("--network-mode", choices=("auto", "system", "direct-affected"), default=os.environ.get("NEWS_TRACE_NETWORK_MODE", "auto"), help="Network route: system first with verified fallback, system only, or direct for configured affected hosts")
    parser.add_argument("--source-id", action="append", help="Probe only this source ID; repeat for multiple sources")
    parser.add_argument("--output", type=Path, help="Write JSON report to this path; otherwise print it")
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100")
    if args.max_age_hours < 1:
        parser.error("--max-age-hours must be positive")
    _NETWORK_MODE = args.network_mode

    config_paths = [CONFIG / "sources.json", *sorted((CONFIG / "sources").glob("*.json"))]
    config_hash = hashlib.sha256()
    for path in config_paths:
        config_hash.update(path.relative_to(CONFIG).as_posix().encode("utf-8"))
        config_hash.update(b"\0")
        config_hash.update(path.read_bytes())
        config_hash.update(b"\0")
    config = json.loads(config_paths[0].read_text(encoding="utf-8"))
    sources = list(config["feeds"])
    for path in config_paths[1:]:
        sources.extend(json.loads(path.read_text(encoding="utf-8"))["feeds"])
    ids = [source["id"] for source in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate source id in configuration")
    if args.source_id:
        wanted = set(args.source_id)
        missing = wanted.difference(ids)
        if missing:
            parser.error("Unknown source IDs: " + ", ".join(sorted(missing)))
        sources = [source for source in sources if source["id"] in wanted]
    code_hashes = {name: hashlib.sha256((SCRIPTS / name).read_bytes()).hexdigest() for name in ("collect.py", "article_probe.py", "paths.py")}
    run_as_of = datetime.now(timezone.utc)
    report = {"schema_version": 5, "checked_at": run_as_of.isoformat(), "snapshot_as_of": run_as_of.isoformat(), "completed_at": None, "python_version": sys.version.split()[0], "config_sha256": config_hash.hexdigest(), "code_sha256": code_hashes, "run_args": {"limit": args.limit, "max_age_hours": args.max_age_hours, "network_mode": args.network_mode, "source_ids": args.source_id or "all"}, "sources": [], "items": []}
    seen = set()
    for source in sources:
        try:
            items = collect(source, args.limit)
            source_cutoff = run_as_of - timedelta(hours=source.get("freshness_hours", args.max_age_hours))
            window_cutoff = run_as_of - timedelta(hours=args.max_age_hours)
            source_recent = [item for item in items if item["published_at"] and source_cutoff <= datetime.fromisoformat(item["published_at"]) <= run_as_of]
            window_recent = [item for item in items if item["published_at"] and window_cutoff <= datetime.fromisoformat(item["published_at"]) <= run_as_of]
            emit_enabled = source.get("emit_items", True)
            emitted_items = 0
            for item in window_recent if emit_enabled else []:
                key = (item["publisher"], item["id"] or item["url"])
                if key not in seen:
                    seen.add(key)
                    report["items"].append(item)
                    emitted_items += 1
            health_status = "ok" if source_recent else "stale"
            if not emit_enabled:
                contribution_status = "disabled"
            elif emitted_items:
                contribution_status = "contributed"
            elif window_recent:
                contribution_status = "deduplicated"
            else:
                contribution_status = "no_window_items"
            status = {"id": source["id"], "publisher": source["publisher"], "kind": source.get("kind", "rss"), "url": source["url"], "status": health_status, "health_status": health_status, "contribution_status": contribution_status, "emit_enabled": emit_enabled, "collected_items": len(items), "items": len(window_recent), "emitted_items": emitted_items, "source_fresh_items": len(source_recent), "retrieval_limit_reached": len(items) >= args.limit, "latest_at": max((item["published_at"] for item in items if item["published_at"]), default=None), "latest_updated_at": max((item.get("updated_at") or item.get("feed_timestamp_at") or item["published_at"] for item in items if item["published_at"]), default=None)}
        except (OSError, ET.ParseError, ValueError) as exc:
            status = {"id": source["id"], "publisher": source["publisher"], "kind": source.get("kind", "rss"), "url": source["url"], "status": "error", "health_status": "error", "contribution_status": "error", "emit_enabled": source.get("emit_items", True), "reason": str(exc)}
        report["sources"].append(status)

    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    health_counts = {name: sum(source["health_status"] == name for source in report["sources"]) for name in ("ok", "stale", "error")}
    contribution_counts = {name: sum(source["contribution_status"] == name for source in report["sources"]) for name in ("contributed", "disabled", "deduplicated", "no_window_items", "error")}
    report["summary"] = {"source_health": health_counts, "candidate_contribution": contribution_counts, "candidate_items": len(report["items"]), "retrieval_limit_reached_sources": sum(bool(source.get("retrieval_limit_reached")) for source in report["sources"])}
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
