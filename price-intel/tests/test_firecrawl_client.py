"""Test lớp thu thập ưu tiên Firecrawl (pure functions, không gọi mạng)."""
from collect import firecrawl_client as fc


def test_strip_html_removes_tags_and_scripts():
    html = "<html><head><style>x{}</style></head><body><script>bad()</script>" \
           "<h1>PP CFR</h1><p>1,189 USD/t</p></body></html>"
    md = fc._strip_html(html)
    assert "PP CFR" in md and "1,189 USD/t" in md
    assert "bad()" not in md and "<h1>" not in md


def test_scrape_md_failsoft_without_any_backend(monkeypatch):
    # Không có FIRECRAWL_KEY, ép HTTP/Scrapling trả None -> scrape_md trả None (không raise)
    monkeypatch.delenv("FIRECRAWL_KEY", raising=False)
    monkeypatch.setattr(fc, "_via_http", lambda url, name: None)
    monkeypatch.setattr(fc, "_via_scrapling", lambda url, name: None)
    assert fc.scrape_md("https://example.com", "demo") is None


def test_ai_extract_without_key_returns_none(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert fc.ai_extract("PP 1189 USD/t", "[{product, value}]") is None
