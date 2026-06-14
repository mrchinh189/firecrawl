# -*- coding: utf-8 -*-
"""history.py — backfill lịch sử 3–5 năm để forecast tin cậy hơn (chạy 1 lần / làm tươi định kỳ).

Nguồn free đã kiểm chứng: EIA (Brent dài), FRED (PPI nhựa resin, palm oil driver, Brent monthly).
Ghi price_type='index' cho PPI (note='proxy driver'), 'spot' cho giá tuyệt đối. Thiếu key -> SKIP.
"""
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from collect import common

FRED_SERIES = {
    "PCU325211325211": ("pp", "index", "PPI nhựa & resin (proxy driver)"),
    "PPOILUSDM": ("stearic", "index", "Global Palm Oil (driver oleochemical)"),
    "POILBREUSDM": ("brent", "index", "Brent monthly dài hạn"),
}


def fred_series(series_id, product, ptype, note):
    """Lấy 1 series FRED. Cần FRED_API_KEY."""
    if not common.has("FRED_API_KEY"):
        print("[skip] FRED_API_KEY trống")
        return []
    try:
        import requests
        url = ("https://api.stlouisfed.org/fred/series/observations"
               f"?series_id={series_id}&api_key={common.env('FRED_API_KEY')}&file_type=json")
        r = requests.get(url, timeout=60); r.raise_for_status()
        out = []
        for o in r.json().get("observations", []):
            if o.get("value") in (".", "", None):
                continue
            out.append(dict(date=o["date"], product=product, grade="", region="global",
                            incoterm="", currency="USD", unit="index", value=float(o["value"]),
                            price_type=ptype, payment_term="at_sight", source="FRED",
                            note=f"backfill — {note}"))
        print(f"[OK] FRED {series_id}: {len(out)} điểm")
        return out
    except Exception as e:  # noqa: BLE001
        print(f"[skip] FRED {series_id} lỗi: {e}")
        return []


def run():
    rows = []
    for sid, (product, ptype, note) in FRED_SERIES.items():
        rows += fred_series(sid, product, ptype, note)
    try:
        from analytics import store
        store.write_rows("staging_prices", rows)
    except Exception as e:  # noqa: BLE001
        print(f"  (dry) staging_prices(history): {len(rows)} dòng ({e})")
    print(f"[OK] history backfill: {len(rows)} điểm.")
    return rows


if __name__ == "__main__":
    run()
