from collect import news

RSS = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Polypropylene CFR SE Asia falls again</title>
<link>https://example.com/pp-news</link>
<description>PP spot eases on weak demand.</description>
<pubDate>Wed, 10 Jun 2026 08:00:00 GMT</pubDate></item>
<item><title>Local football match result</title>
<link>https://example.com/sport</link>
<description>Unrelated sports news.</description>
<pubDate>Wed, 10 Jun 2026 09:00:00 GMT</pubDate></item>
</channel></rss>"""


def test_parse_rss():
    items = news.parse_rss(RSS, source="Test", category="resin")
    assert len(items) == 2
    assert items[0]["title"].startswith("Polypropylene")
    assert items[0]["url"].startswith("http")
    assert items[0]["published_at"] == "2026-06-10"


def test_is_relevant_filters():
    items = news.parse_rss(RSS)
    rel = [i for i in items if news.is_relevant(i)]
    assert len(rel) == 1 and "Polypropylene" in rel[0]["title"]


def test_dedupe():
    a = {"url": "https://x/1", "title": "a"}
    b = {"url": "https://x/1", "title": "a-dup"}
    c = {"url": "https://x/2", "title": "c"}
    out = news.dedupe([a, b, c])
    assert len(out) == 2


def test_summarize_relevant_failsoft_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    items = news.parse_rss(RSS)
    assert news.summarize_relevant(items) == items   # thiếu key -> giữ nguyên
