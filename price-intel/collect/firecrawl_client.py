# -*- coding: utf-8 -*-
"""firecrawl_client.py — lớp cào ƯU TIÊN FIRECRAWL (theo yêu cầu dự án).

Thứ tự fail-soft:
  1) Firecrawl API (FIRECRAWL_KEY)        — chính, render JS + chống chặn tốt
  2) HTTP thuần (requests) + strip HTML    — fallback khi thiếu key/Firecrawl lỗi
  3) (tùy chọn) Scrapling stealth          — fallback cuối nếu đã cài

Sau khi có markdown -> ai_extract() dùng Claude (llm) bóc số theo schema JSON.
Thiếu mọi thứ -> trả None (KHÔNG gãy pipeline).
"""
import json
import os
import pathlib
import re
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from collect import common

FIRECRAWL_API = "https://api.firecrawl.dev/v1/scrape"


def _strip_html(html: str) -> str:
    """HTML -> text gọn (bỏ script/style/tag) để đưa qua AI extract."""
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+\n", "\n", re.sub(r"[ \t]+", " ", text)).strip()


def _via_firecrawl(url: str, name: str):
    """Cào bằng Firecrawl API -> markdown. Ưu tiên số 1."""
    key = common.env("FIRECRAWL_KEY")
    if not key:
        return None
    try:
        import requests
        resp = requests.post(
            FIRECRAWL_API,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        md = data.get("markdown") or data.get("content") or ""
        if md:
            print(f"[OK] firecrawl {name or url}: {len(md)} chars")
            return md
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] firecrawl {name or url} lỗi: {e}")
    return None


def _via_http(url: str, name: str):
    """Fallback HTTP thuần + strip HTML (không JS)."""
    try:
        import requests
        r = requests.get(url, timeout=40, headers={"User-Agent": "Mozilla/5.0 price-intel"})
        r.raise_for_status()
        md = _strip_html(r.text)
        print(f"[OK] http {name or url}: {len(md)} chars")
        return md or None
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] http {name or url} lỗi: {e}")
        return None


def _via_scrapling(url: str, name: str):
    """Fallback cuối: Scrapling stealth (nếu đã cài). Không bắt buộc."""
    try:
        from scrapling.fetchers import StealthyFetcher
        page = StealthyFetcher.fetch(url, headless=True)
        html = getattr(page, "html_content", None) or str(page)
        md = _strip_html(html)
        print(f"[OK] scrapling {name or url}: {len(md)} chars")
        return md or None
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] scrapling {name or url} lỗi: {e}")
        return None


def scrape_md(url: str, name: str = ""):
    """Trả markdown/text của trang theo thứ tự ưu tiên FIRECRAWL -> HTTP -> Scrapling. None nếu hết cách."""
    cfg = common.env("FETCH_PREFER", "firecrawl")
    order = ([_via_firecrawl, _via_http, _via_scrapling]
             if cfg != "http" else [_via_http, _via_firecrawl, _via_scrapling])
    for fn in order:
        md = fn(url, name)
        if md:
            return md
        common.polite_sleep(2)
    return None


def ai_extract(markdown: str, schema_hint: str, task: str = "extract"):
    """Dùng Claude bóc số từ markdown theo schema JSON mô tả ở schema_hint. Thiếu key -> None."""
    if not markdown:
        return None
    import llm
    system = ("Bạn bóc dữ liệu giá NVL nhựa từ văn bản. Chỉ trả JSON theo mô tả schema. "
              "KHÔNG bịa số. Bỏ qua trường không có dữ liệu.")
    user = f"SCHEMA:\n{schema_hint}\n\nVĂN BẢN:\n{markdown[:12000]}"
    txt = llm.complete(task, system, user)
    if not txt:
        return None
    try:
        s = txt[txt.find("["): txt.rfind("]") + 1] or txt[txt.find("{"): txt.rfind("}") + 1]
        return json.loads(s)
    except Exception:  # noqa: BLE001
        return None
