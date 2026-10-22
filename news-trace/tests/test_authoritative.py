"""Network-free parser checks for the BBC and Xinhua source adapters."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from article_probe import inspect_article
from collect import local_timestamp, parse_bbc_rss, parse_xinhua_en, parse_xinhua_zh


class AuthoritativeSourceTests(unittest.TestCase):
    def test_bbc_article_dates_and_body(self):
        page = b'''<h1 id="main-heading"><span>Example report</span></h1>
        <script>{"datePublished":"2026-09-30T20:00:00Z","dateModified":"2026-10-01T03:00:00Z"}</script>
        <article><p>First paragraph with reported facts.</p><div><p>Second paragraph with context.</p></div></article>'''
        result = inspect_article(page, "bbc")
        self.assertEqual(result["title"], "Example report")
        self.assertEqual(result["paragraph_count"], 2)
        self.assertGreater(result["body_chars"], 60)

    def test_bbc_rss_is_updated_not_first_published(self):
        rss = b'''<rss><channel><item><title>Example report</title>
        <link>https://www.bbc.co.uk/news/articles/example?at_medium=RSS</link>
        <pubDate>Thu, 01 Oct 2026 03:00:00 GMT</pubDate></item></channel></rss>'''
        source = {"id": "bbc-world", "publisher": "BBC News", "region": "UK", "language": "en"}
        article = {"title": "Example report", "published_raw": "2026-09-30T20:00:00Z", "updated_raw": "2026-10-01T03:00:00Z", "paragraph_count": 2, "body_chars": 100, "body_sha256": "abc"}
        with patch("collect.article_metadata", return_value=article):
            item = parse_bbc_rss(rss, source, 1)[0]
        self.assertEqual(item["published_at"], "2026-09-30T20:00:00+00:00")
        self.assertEqual(item["updated_at"], "2026-10-01T03:00:00+00:00")
        self.assertTrue(item["article_title_match"])
        self.assertEqual(item["url"], "https://www.bbc.co.uk/news/articles/example")

    def test_bbc_changed_headline_is_not_claimed_as_verified(self):
        rss = b'''<rss><channel><item><title>Old headline</title>
        <link>https://www.bbc.co.uk/news/articles/example</link>
        <pubDate>Thu, 01 Oct 2026 03:00:00 GMT</pubDate></item></channel></rss>'''
        source = {"id": "bbc-world", "publisher": "BBC News", "region": "UK", "language": "en"}
        article = {"title": "New headline", "published_raw": "2026-09-30T20:00:00Z", "updated_raw": "2026-10-01T03:00:00Z", "paragraph_count": 2, "body_chars": 100, "body_sha256": "abc"}
        with patch("collect.article_metadata", return_value=article):
            with self.assertRaisesRegex(ValueError, "No BBC articles"):
                parse_bbc_rss(rss, source, 1)

    def test_xinhua_local_time(self):
        self.assertEqual(local_timestamp("2026-10-01 11:32:45"), "2026-10-01T03:32:45+00:00")

    def test_xinhua_english_list_and_article(self):
        page = b'<div class="tit"><a href="../20261001/example/c.html">Example Xinhua story</a><span class="time">2026-10-01 11:32:45</span></div>'
        source = {"id": "xinhua-en-latest", "publisher": "Xinhua News Agency", "region": "China", "language": "en", "category": "general", "evidence": "https://english.news.cn/list/latestnews.htm", "url": "https://english.news.cn/list/latestnews.htm"}
        article = {"title": "Example Xinhua story", "published_raw": "2026-10-01 11:32:45", "source_line": "Source: Xinhua", "agency_credit": True, "paragraph_count": 2, "body_chars": 100, "body_sha256": "abc"}
        with patch("collect.article_metadata", return_value=article):
            item = parse_xinhua_en(page, source, 1)[0]
        self.assertEqual(item["published_at"], "2026-10-01T03:32:45+00:00")
        self.assertTrue(item["article_title_match"])

    def test_xinhua_chinese_requires_agency_credit(self):
        page = '最新播报:</div><div class="latest-cont"><ul><li><a href="20261001/example/c.html">示例报道</a></li></ul>'
        source = {"id": "xinhua-zh-latest", "publisher": "新华社", "region": "China", "language": "zh", "category": "chinese", "evidence": "https://www.news.cn/", "url": "https://www.news.cn/"}
        article = {"title": "示例报道", "published_raw": "2026-10-01 11:32:45", "source_line": "新华网", "agency_credit": True, "paragraph_count": 2, "body_chars": 100, "body_sha256": "abc"}
        with patch("collect.article_metadata", return_value=article):
            item = parse_xinhua_zh(page.encode(), source, 1)[0]
        self.assertEqual(item["published_at"], "2026-10-01T03:32:45+00:00")
        self.assertTrue(item["agency_credit"])


if __name__ == "__main__":
    unittest.main()
