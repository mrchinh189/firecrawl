# -*- coding: utf-8 -*-
"""load.py — QC + nạp staging_prices -> price_master (1 nguồn chân lý).

QC: đủ trường bắt buộc + value>0; nhảy >10% so với mốc trước (cùng product/region) -> FLAG review
(KHÔNG xóa). Bỏ qua kiểm nhảy cho price_type='index' hoặc note chứa 'backfill'.
Quy value_vnd_kg theo fx mới nhất (chỉ với dòng landed được). Upsert giữ history + ghi audit_log.

Hàm thuần (pct_jump, qc_row, to_vnd_kg) test được không cần DB. load() fail-soft offline.
"""
import datetime as dt
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
import lib

REQUIRED = ("date", "product", "region", "currency", "unit", "value", "price_type", "source")


def pct_jump(prev, cur):
    """Tỉ lệ nhảy |cur-prev|/prev. None nếu không so được."""
    if prev in (None, 0) or cur is None:
        return None
    return abs(cur - prev) / abs(prev)


def qc_row(row, prev_value=None, jump_pct=0.10):
    """Trả (ok, flag) — ok=False nếu thiếu trường/value<=0; flag='review' nếu nhảy quá ngưỡng."""
    for k in REQUIRED:
        if row.get(k) in (None, ""):
            return False, f"thiếu trường {k}"
    try:
        if float(row["value"]) <= 0:
            return False, "value<=0"
    except (TypeError, ValueError):
        return False, "value không hợp lệ"
    ptype = str(row.get("price_type", "")).lower()
    note = str(row.get("note", "")).lower()
    if ptype == "index" or "backfill" in note:
        return True, None                 # nới QC cho chuỗi index/backfill
    j = pct_jump(prev_value, float(row["value"]))
    if j is not None and j > jump_pct:
        return True, "review"             # giữ lại nhưng đánh dấu rà soát
    return True, None


def to_vnd_kg(usd_per_ton, fx_usdvnd):
    """USD/tấn -> VND/kg thô (chưa cộng thuế/cước — đó là việc của landed.py)."""
    if usd_per_ton is None or fx_usdvnd is None:
        return None
    return round(usd_per_ton * fx_usdvnd / 1000)


def load(rows=None):
    """Nạp staging -> price_master. Offline (không DB): chỉ QC + in dry-run."""
    from analytics import landed as L, store
    thresholds = lib.load_yaml("thresholds.yaml")
    jump = thresholds.get("qc", {}).get("jump_pct", 0.10)
    fx = store.read_latest_fx()
    cfg = lib.load_yaml("landed.yaml")
    usd_rmb = cfg.get("usd_rmb", 7.15)

    rows = rows if rows is not None else store.read_price_master()  # demo: coi fixtures là staging
    # theo dõi giá trước theo (product, region) để kiểm nhảy
    prev = {}
    ok_rows, flagged = [], 0
    for r in sorted(rows, key=lambda x: x["date"]):
        key = (r.get("product"), r.get("region"))
        good, flag = qc_row(r, prev.get(key), jump)
        if not good:
            print(f"[drop] {r.get('product')} {r.get('date')}: {flag}")
            continue
        if flag == "review":
            flagged += 1
        prev[key] = float(r["value"])
        usd = L.to_usd_per_ton(r.get("value"), r.get("currency"), r.get("unit"), usd_rmb)
        out = {**r, "value_vnd_kg": to_vnd_kg(usd, fx) if usd else None,
               "note": (r.get("note") or "") + (" [review]" if flag == "review" else "")}
        ok_rows.append(out)

    cols = ["date", "product", "grade", "region", "incoterm", "currency", "unit", "value",
            "price_type", "value_vnd_kg", "payment_term", "source", "note"]
    store.write_rows("price_master", [{c: r.get(c) for c in cols} for r in ok_rows])
    print(f"[OK] load: {len(ok_rows)} dòng vào price_master ({flagged} flag review).")
    return {"loaded": len(ok_rows), "flagged": flagged}


if __name__ == "__main__":
    load()
