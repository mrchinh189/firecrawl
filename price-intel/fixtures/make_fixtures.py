# -*- coding: utf-8 -*-
"""make_fixtures.py — sinh dữ liệu mẫu xác định (deterministic) để demo/test offline.
Chạy: python fixtures/make_fixtures.py  -> ghi price_master.csv, fx_rates.csv."""
import csv
import datetime as dt
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
WEEKS = 12
END = dt.date(2026, 6, 10)
DATES = [END - dt.timedelta(weeks=(WEEKS - 1 - i)) for i in range(WEEKS)]

# giá nền + độ dốc tuyến tính (không random) cho chuỗi mượt
BASE = {  # product: (start, end) USD/tấn (brent USD/bbl)
    "brent": (95, 93), "naphtha": (1010, 944), "ethylene": (1180, 1100),
    "propylene": (1090, 1020), "pp": (1330, 1189), "pe": (1230, 1127),
    "hdpe": (1260, 1150), "ps": (1360, 1319), "tio2": (2200, 2344),
    "stearic": (1330, 1316),
}
UNIT = {"brent": ("USD", "bbl")}  # còn lại USD/ton


def series(a, b):
    return [round(a + (b - a) * i / (WEEKS - 1), 1) for i in range(WEEKS)]


def main():
    rows = []
    for p, (a, b) in BASE.items():
        cur, unit = UNIT.get(p, ("USD", "ton"))
        vals = series(a, b)
        for d, v in zip(DATES, vals):
            rows.append(dict(date=d.isoformat(), product=p, grade="", region="CFR SE Asia",
                             incoterm="CFR", currency=cur, unit=unit, value=v,
                             price_type="spot", payment_term="at_sight",
                             source="Polymerupdate-free", note=""))
    # snapshot nhiều khu vực cho PP/PE (để xếp hạng at-sight) — chỉ ngày cuối
    snap = [
        ("pp", "DCE (TQ)", "futures", "at_sight", 7604, "RMB", "ton", "DCE delayed"),
        ("pp", "US Gulf", "spot", "at_sight", 50, "USc", "lb", "ThePlasticsExchange"),
        ("pp", "VN import (CIF)", "unit_value", "at_sight", 1231, "USD", "ton", "UN Comtrade"),
        ("pp", "Báo giá NCC A", "quote", "lc_90", 1207, "USD", "ton", "NCC A (form)"),
        ("pe", "US Gulf", "spot", "at_sight", 43, "USc", "lb", "ThePlasticsExchange"),
        ("pe", "VN import (CIF)", "unit_value", "at_sight", 1165, "USD", "ton", "UN Comtrade"),
        ("tio2", "ex-works TQ", "spot", "at_sight", 14846, "RMB", "ton", "blog (AI-extract)"),
    ]
    for p, region, pt, term, val, cur, unit, src in snap:
        rows.append(dict(date=DATES[-1].isoformat(), product=p, grade="", region=region,
                         incoterm="", currency=cur, unit=unit, value=val, price_type=pt,
                         payment_term=term, source=src, note=""))
    fields = ["date", "product", "grade", "region", "incoterm", "currency", "unit",
              "value", "price_type", "payment_term", "source", "note"]
    with open(HERE / "price_master.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    with open(HERE / "fx_rates.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "pair", "rate", "source"])
        w.writerow([DATES[-1].isoformat(), "USD/VND", 26412, "Vietcombank"])
    print(f"[OK] fixtures: {len(rows)} dòng price_master, 1 fx")


if __name__ == "__main__":
    main()
