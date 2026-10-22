"""Extract and verify public article metadata without saving article text."""

from __future__ import annotations

import hashlib
import html
import re
from html.parser import HTMLParser


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def plain(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


class Paragraphs(HTMLParser):
    def __init__(self, target: str):
        super().__init__(convert_charrefs=True)
        self.target = target
        self.found = False
        self.depth = 0
        self.p_depth = 0
        self.parts: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if not self.found and ((self.target == "article" and tag == "article") or attributes.get("id") == self.target):
            self.found = True
            self.depth = 1
            return
        if self.depth:
            if tag not in VOID:
                self.depth += 1
            if tag == "p" and not self.p_depth:
                self.p_depth = 1
                self.parts = []
            elif self.p_depth and tag not in VOID:
                self.p_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if not self.depth:
            return
        if self.p_depth:
            self.p_depth -= 1
            if not self.p_depth:
                value = re.sub(r"\s+", " ", "".join(self.parts)).strip()
                if value:
                    self.paragraphs.append(value)
        if tag not in VOID:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.p_depth:
            self.parts.append(data)


def first(pattern: str, page: str) -> str:
    match = re.search(pattern, page, re.I | re.S)
    return plain(match.group(1)) if match else ""


def inspect_article(payload: bytes, kind: str) -> dict:
    page = payload.decode("utf-8", "replace")
    if kind == "bbc":
        title = first(r'<h1\b[^>]*id="main-heading"[^>]*>(.*?)</h1>', page)
        published = first(r'"datePublished"\s*:\s*"([^"]+)"', page)
        updated = first(r'"dateModified"\s*:\s*"([^"]+)"', page)
        source = "BBC News"
        target = "article"
    elif kind == "xinhua_en":
        title = first(r"<h1\b[^>]*>(.*?)</h1>", page)
        published = first(r'<p\b[^>]*class="time"[^>]*>(.*?)</p>', page)
        updated = ""
        source = first(r'<p\b[^>]*class="source"[^>]*>(.*?)</p>', page)
        target = "detail"
    elif kind == "xinhua_zh":
        title = first(r'<h1\b[^>]*>\s*<span\b[^>]*class="title"[^>]*>(.*?)</span>', page)
        published = first(r'<div\b[^>]*class="info"[^>]*>\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', page)
        updated = ""
        source = first(r'<meta\b[^>]*name="source"[^>]*content="([^"]+)"', page)
        target = "detailContent"
    else:
        raise ValueError(f"Unknown article kind: {kind}")
    paragraphs = Paragraphs(target)
    paragraphs.feed(page)
    body = "\n".join(paragraphs.paragraphs)
    return {
        "title": title,
        "published_raw": published,
        "updated_raw": updated,
        "source_line": source,
        "paragraph_count": len(paragraphs.paragraphs),
        "body_chars": len(body),
        "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest() if body else None,
        "agency_credit": "新华社" in " ".join(paragraphs.paragraphs[:2]) or source.lower().endswith("xinhua"),
    }
