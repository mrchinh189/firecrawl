# -*- coding: utf-8 -*-
"""news.py — thu thập TIN TỨC thị trường (tiêu đề + tóm tắt 1–2 câu + link + ngày).

Nguồn CÔNG KHAI: Google News RSS theo từ khóa, blog ngành (qua Firecrawl). Chỉ lưu tiêu đề/tóm tắt
+ link out (KHÔNG full-text/nội dung trả phí). Lọc liên quan NVL, khử trùng lặp theo URL.
Tùy chọn Claude lọc/tóm tắt (summarize_relevant) — thiếu key thì giữ nguyên (fail-soft).
"""
import datetime as dt
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
import lib

KEYWORDS = ["polypropylene", "polyethylene", " pp ", " pe ", "naphtha", "tio2", "titanium dioxide",
            "stearic", "palm oil", "ethylene", "propylene", "resin", "masterbatch", "cfr", "nhựa"]


def _pub_date(text):
    """Parse pubDate RSS ('Wed, 10 Jun 2026 08:00:00 GMT') -> 'YYYY-MM-DD'. Fallback hôm nay."""
    if not text:
        return dt.date.today().isoformat()
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(text).date().isoformat()
    except Exception:  # noqa: BLE001
        return dt.date.today().isoformat()


def parse_rss(xml_text, source="Google News RSS", category="resin"):
    """Parse RSS string -> list[dict]. Dùng xml.etree (thư viện chuẩn, không cần feedparser)."""
    import re
    from xml.etree import ElementTree as ET

    def _txt(el, tag):
        child = el.find(tag)
        return (child.text or "").strip() if child is not None and child.text else ""

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    out = []
    for item in root.iter("item"):
        summary = re.sub(r"<[^>]+>", " ", _txt(item, "description"))[:300].strip()
        out.append({
            "published_at": _pub_date(_txt(item, "pubDate")),
            "title": _txt(item, "title"),
            "url": _txt(item, "link"),
            "summary": summary,
            "source": source, "category": category,
        })
    return out


def is_relevant(item, keywords=None):
    """True nếu tiêu đề/tóm tắt chứa từ khóa NVL/feedstock."""
    kws = keywords or KEYWORDS
    text = f" {item.get('title','')} {item.get('summary','')} ".lower()
    return any(k.strip() in text for k in kws)


def dedupe(items):
    """Khử trùng lặp theo URL, giữ thứ tự."""
    seen, out = set(), []
    for it in items:
        u = it.get("url")
        if u and u not in seen:
            seen.add(u); out.append(it)
    return out


def summarize_relevant(items):
    """Tùy chọn: Claude lọc tin liên quan + rút tóm tắt 1 câu. Thiếu key/lỗi -> trả items gốc."""
    import json
    import llm
    if not items:
        return items
    system = ("Bạn lọc tin liên quan giá NVL nhựa (resin/feedstock/phụ gia) và rút tóm tắt 1 câu tiếng Việt. "
              "Trả JSON list [{title,url,summary,category}] chỉ gồm tin liên quan.")
    user = json.dumps(items[:20], ensure_ascii=False)
    txt = llm.complete("news", system, user)
    if not txt:
        return items
    try:
        s = txt[txt.find("["): txt.rfind("]") + 1]
        got = json.loads(s)
        by_url = {i["url"]: i for i in items}
        merged = []
        for g in got:
            base = by_url.get(g.get("url"), {})
            merged.append({**base, **{k: v for k, v in g.items() if v}})
        return merged or items
    except Exception:  # noqa: BLE001
        return items


def run():
    """Thu thập từ config/sources.yaml mục news. Ghi bảng news (DB) hoặc dry-run."""
    import requests
    from analytics import store
    sources = lib.load_yaml("sources.yaml").get("news", [])
    items = []
    for s in sources:
        rss = s.get("rss")
        cat = s.get("category", "resin")
        if rss:
            try:
                r = requests.get(rss, timeout=30, headers={"User-Agent": "price-intel"})
                r.raise_for_status()
                items += parse_rss(r.text, source=s.get("name", "RSS"), category=cat)
            except Exception as e:  # noqa: BLE001
                print(f"[skip] RSS {s.get('name')}: {e}")
    items = [i for i in dedupe(items) if is_relevant(i)]
    items = summarize_relevant(items)[:12]
    store.write_rows("news", items)
    print(f"[OK] news: {len(items)} tin.")
    return items


if __name__ == "__main__":
    run()
