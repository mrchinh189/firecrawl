# -*- coding: utf-8 -*-
"""build_analysis.py — chạy toàn chuỗi tính: landed + spreads + forecast + narrative + alerts
-> ghi DB (hoặc dry-run). Trả về dict tổng hợp (kèm kpi/rows/series) để report/telegram tái dùng."""
import datetime as dt
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from analytics import landed as L, spreads as S, narrative as N, store
from forecast import run as F, commentary as C
from alerts import rules as R
import lib


def _latest_by_product(rows):
    """Giá mới nhất mỗi product (theo ngày)."""
    out = {}
    for r in sorted(rows, key=lambda x: x["date"]):
        out[r["product"]] = r["value"]
    return out


def _series_by_product(rows, product):
    return [r["value"] for r in sorted(rows, key=lambda x: x["date"])
            if r["product"] == product and r["region"] == "CFR SE Asia"]


def _pct_change(series):
    if len(series) < 2 or series[-2] == 0:
        return None
    return round((series[-1] / series[-2] - 1) * 100, 1)


def run():
    rows = store.read_price_master()
    fx = store.read_latest_fx()
    cfg = lib.load_yaml("landed.yaml")
    thresholds = lib.load_yaml("thresholds.yaml")
    run_date = dt.date.today().isoformat()

    # 1) landed/at-sight (chỉ các dòng landed được)
    landed_rows = L.compute(rows, fx_usdvnd=fx, cfg=cfg)
    store.write_rows("landed", [
        {"date": r["date"], "product": r["product"], "region": r["region"],
         "price_type": r["price_type"], "payment_term": r.get("payment_term", "at_sight"),
         "raw_price": r["value"], "raw_unit": r["unit"], "usd_per_ton": r["usd_per_ton"],
         "landed_vnd_kg": r["landed_vnd_kg"], "usance_benefit": r["usance_benefit"],
         "at_sight_equiv": r["at_sight_equiv"], "is_best": r["is_best"], "source": r["source"]}
        for r in landed_rows])

    # 2) spreads
    latest = _latest_by_product(rows)
    spread_rows = S.compute(latest)
    store.write_rows("spreads", [{"date": run_date, **s, "note": ""} for s in spread_rows])

    # 3) forecast cho PP/PE (chuỗi CFR SE Asia)
    fc_rows, forecast_pct = [], {}
    for p in ("pp", "pe"):
        ser = _series_by_product(rows, p)
        if not ser:
            continue
        res = F.forecast_series(ser, horizon=6, basis="spot dài")
        forecast_pct[p] = round((res["yhat"][-1] / ser[-1] - 1) * 100, 1)
        for wk, (yh, lo, up) in enumerate(zip(res["yhat"], res["lower"], res["upper"]), start=1):
            fc_rows.append({"run_date": run_date, "product": p, "week": wk, "yhat": yh,
                            "lower": lo, "upper": up, "model": res["model"], "mape": None,
                            "theils_u": res["theils_u"], "confidence": res["confidence"],
                            "basis": res["basis"]})
    store.write_rows("forecast", fc_rows)

    # 4) context cho narrative + rules
    best_pp = next((r for r in landed_rows if r["product"] == "pp" and r["is_best"]), None)
    ctx = {
        "resin_trend": {p: _pct_change(_series_by_product(rows, p)) for p in ("pp", "pe", "hdpe")},
        "additive_trend": {p: _pct_change(_series_by_product(rows, p)) for p in ("tio2", "stearic")},
        "best_source": {"pp": best_pp["region"] if best_pp else None,
                        "pp_at_sight": best_pp["at_sight_equiv"] if best_pp else None},
        "pp_gap_vnd_kg": (max(r["at_sight_equiv"] for r in landed_rows if r["product"] == "pp")
                          - min(r["at_sight_equiv"] for r in landed_rows if r["product"] == "pp"))
                         if any(r["product"] == "pp" for r in landed_rows) else None,
        "pp_forecast_pct": forecast_pct.get("pp"),
        "forecast_pct": forecast_pct,
    }
    narr = N.build(ctx)
    cards = R.evaluate(ctx, thresholds)
    store.write_analysis(run_date, "narrative", narr)
    store.write_analysis(run_date, "alerts", cards)

    # Diễn giải dự báo + kịch bản bằng Claude (số giữ thống kê). Thiếu key -> None, bỏ qua.
    cmt = C.build({"forecast_pct": forecast_pct}, spread_rows, store.read_news(limit=6))
    if cmt:
        store.write_analysis(run_date, "commentary", cmt)

    # 5) kpi/rows/series cho report + telegram (parity)
    products = sorted({r["product"] for r in rows})
    kpi = {
        "latest": latest,
        "fx": fx,
        "forecast_pct": forecast_pct,
        "pct_change": {p: _pct_change(_series_by_product(rows, p)) for p in products},
        "best": {r["product"]: r for r in landed_rows if r["is_best"]},
    }
    series = {p: [(r["date"], r["value"]) for r in sorted(rows, key=lambda x: x["date"])
                  if r["product"] == p and r["region"] == "CFR SE Asia"]
              for p in products}
    series = {p: s for p, s in series.items() if s}
    store.write_analysis(run_date, "kpi", {"latest": latest, "fx": fx, "forecast_pct": forecast_pct})

    return {"landed": landed_rows, "spreads": spread_rows, "forecast": fc_rows,
            "narrative": narr, "alerts": cards, "ctx": ctx, "commentary": cmt,
            "kpi": kpi, "rows": rows, "series": series}


if __name__ == "__main__":
    out = run()
    print(f"[OK] build_analysis: landed={len(out['landed'])} spreads={len(out['spreads'])} "
          f"forecast={len(out['forecast'])} alerts={len(out['alerts'])}")
