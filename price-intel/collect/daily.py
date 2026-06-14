# -*- coding: utf-8 -*-
"""daily.py — orchestrator thu thập giá hằng ngày, ƯU TIÊN FIRECRAWL.

Thứ tự nguồn:
  1) FREE API/XML: EIA (Brent), Vietcombank (USD/VND)  — nếu có khóa
  2) FIRECRAWL: ThePlasticsExchange/DCE/Polymerupdate... -> ai_extract (Claude)
Ghi vào staging_prices (DB) hoặc in dry-run khi offline. Thiếu khóa nào -> SKIP nguồn đó (fail-soft).

Đây là khung thu thập: chi tiết bóc số từng trang để trong prompt schema (ai_extract),
không vỡ khi web đổi layout. Chạy: python collect/daily.py
"""
import datetime as dt
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from collect import common, firecrawl_client as fc
import lib

PRICE_SCHEMA = (
    'Trả JSON list các bản ghi giá: '
    '[{product, region, currency, unit, value, price_type, date(YYYY-MM-DD)}]. '
    'product ∈ {pp,pe,hdpe,ps,tio2,stearic,...}. Chỉ lấy số chắc chắn.'
)


def collect_free():
    """Nguồn FREE: chỉ chạy khi có khóa; nếu không -> SKIP (fail-soft)."""
    out = []
    if common.has("EIA_KEY"):
        print("[..] EIA Brent (cần triển khai gọi API EIA tại đây)")
        # TODO khi chạy thật: gọi api.eia.gov với EIA_KEY -> append bản ghi brent
    else:
        print("[skip] EIA_KEY trống")
    print("[..] Vietcombank USD/VND (XML công khai) — thêm parser khi chạy thật")
    return out


def collect_firecrawl():
    """Nguồn cào: ƯU TIÊN FIRECRAWL -> ai_extract. Thiếu FIRECRAWL_KEY -> thử HTTP fallback."""
    out = []
    sources = lib.load_yaml("sources.yaml").get("firecrawl", [])
    delay = lib.load_yaml("sources.yaml").get("fetch", {}).get("delay_sec", 4)
    for s in sources:
        name, url = s["name"], s["url"]
        md = fc.scrape_md(url, name)              # firecrawl -> http -> scrapling
        if not md:
            print(f"[skip] {name}: không lấy được nội dung")
            continue
        records = fc.ai_extract(md, PRICE_SCHEMA)  # Claude bóc số (thiếu key -> None)
        if not records:
            print(f"[skip] {name}: chưa bóc được số (thiếu ANTHROPIC_API_KEY?)")
            continue
        for r in records:
            r.setdefault("source", name)
            r.setdefault("date", dt.date.today().isoformat())
            out.append(r)
        common.polite_sleep(delay)
    return out


def main():
    print("=== Thu thập giá NVL (ưu tiên Firecrawl) ===")
    rows = collect_free() + collect_firecrawl()
    print(f"[OK] thu thập {len(rows)} bản ghi.")
    try:
        from analytics import store
        store.write_rows("staging_prices", rows)
    except Exception as e:  # noqa: BLE001
        print(f"  (dry) staging_prices: {len(rows)} dòng ({e})")
    return rows


if __name__ == "__main__":
    main()
