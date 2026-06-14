# -*- coding: utf-8 -*-
"""render.py — biến output build_analysis thành VIEW-MODEL thuần dùng chung cho HTML/DOCX/Telegram.
Một nơi định hình -> 3 kênh cùng số, cùng link, cùng ngày (parity)."""
import datetime as dt
import lib
from analytics import store

GLOSSARY = [
    {"term": "Incoterm (FOB/CFR/CIF)", "desc": "Quy ước ai chịu chi phí/rủi ro tới đâu. CFR=đã gồm cước; CIF=thêm bảo hiểm."},
    {"term": "At sight / Usance", "desc": "Trả ngay khi xuất trình chứng từ / được nợ có kỳ hạn (L/C 90, TT 60…)."},
    {"term": "Landed cost", "desc": "Giá đã về kho: giá gốc + cước + bảo hiểm + thuế NK + nội địa, quy VND/kg."},
    {"term": "At-sight tương đương", "desc": "Landed trừ lợi ích trả chậm — mốc so công bằng giữa các báo giá khác điều khoản."},
    {"term": "Spread", "desc": "Chênh lệch giá hai khâu liền kề (vd PP−propylene); mỏng → giá khó giảm thêm."},
    {"term": "Chỉ số gốc-100", "desc": "Quy mọi chuỗi về 100 đầu kỳ để so tốc độ tăng/giảm dù mặt bằng khác nhau."},
    {"term": "Theil's U", "desc": "Sai số dự báo; <1 nghĩa là tốt hơn cách đoán 'ngày mai = hôm nay'."},
    {"term": "Độ tươi 🟢🟡🔴", "desc": "Ngày giá cách nay ≤7 / ≤30 / >30 ngày. Đỏ = nguồn có thể đã cũ."},
]

PAYMENT_LABEL = {"at_sight": "At sight", "lc_at_sight": "L/C at sight", "lc_90": "L/C 90 ngày",
                 "lc_60": "L/C 60 ngày", "tt_60": "TT 60 ngày", "tt_30": "TT 30 ngày"}

SPREAD_LABEL = {"pp-propylene": "Spread PP−propylene", "naphtha-ethylene": "Spread naphtha−ethylene",
                "ethylene-pe": "Spread ethylene−PE"}

# ① Cách đọc báo cáo (bám báo cáo mẫu v4) — dẫn-đọc tĩnh
HOW_TO_READ = {
    "questions": ("Báo cáo trả lời 4 câu hỏi mua hàng: (1) giá đang ở đâu, (2) nguồn nào thực sự rẻ "
                  "nhất sau khi quy về cùng mốc, (3) sắp tới giá đi hướng nào, (4) nên làm gì."),
    "tip": ("💡 Mẹo đọc: bắt đầu ở mục Phân tích (lời, dễ hiểu), rồi xuống mục Giá chung để chọn nguồn, "
            "cuối cùng xem Cảnh báo để biết việc cần làm. Các bảng số chi tiết để tra khi cần."),
    "note": ("⚠️ Lưu ý quy đổi: mọi giá nhập khẩu chỉ so được khi đưa về cùng một mốc — cùng đơn vị "
             "(VND/kg), cùng điểm giao (đã về kho), cùng điều khoản thanh toán. Báo cáo đã làm sẵn việc đó."),
}
CADENCE = ("Nhịp: daily (Brent·FX·futures) · weekly thứ Tư (spot·phụ gia) · monthly (hải quan). "
           "Độ tươi 🟢≤7d 🟡≤30d 🔴>30d. Thẻ KPI: số lớn = giá mới nhất; ▲đỏ/▼xanh = thay đổi kỳ trước; "
           "dòng ≈đ/kg = giá đã quy về kho VN.")


def _today():
    return dt.date.today()


def _raw_str(r):
    return f"{r['value']:,.0f} {r.get('currency','')}/{r.get('unit','')}".strip()


def build_view(data, today=None):
    today = today or _today()
    kpi_src = data["kpi"]; latest = kpi_src["latest"]; fx = kpi_src["fx"]
    pctc = kpi_src["pct_change"]; best = kpi_src["best"]
    rows = data["rows"]

    # ngày giá mới nhất theo product
    last_date = {}
    for r in sorted(rows, key=lambda x: x["date"]):
        last_date[r["product"]] = r["date"]

    # 1) KPI cards (theo materials.yaml để ưu tiên thứ tự)
    mats = lib.load_yaml("materials.yaml").get("materials", [])
    order = [m["key"] for m in mats]
    kpi = [{"key": "fx", "label": "USD/VND", "value": f"{fx:,.0f}", "chg": None,
            "landed": None, "date": None, "fresh": None}]
    for p in (["brent"] + order):
        if p not in latest:
            continue
        b = best.get(p)
        kpi.append({
            "key": p, "label": p.upper(), "value": f"{latest[p]:,.0f}",
            "chg": pctc.get(p),
            "landed": (f"{b['landed_vnd_kg']:,.0f} đ/kg" if b else None),
            "date": last_date.get(p),
            "fresh": (lib.freshness(last_date[p], today) if last_date.get(p) else None),
        })

    # Thẻ Spread vào KPI (mục ②, bám v4: "Spread PP−propylene")
    for s in data.get("spreads", []):
        kpi.append({
            "key": "spread_" + s["name"],
            "label": SPREAD_LABEL.get(s["name"], "Spread " + s["name"]),
            "value": f"{s['value']:,.0f} {s['unit']}",
            "chg": None, "landed": None, "date": None, "fresh": None,
        })

    def _src(name):
        label, url = lib.source_link(name)
        return label, url

    # 2) Bảng at-sight theo từng NVL
    atsight = {}
    for r in data["landed"]:
        atsight.setdefault(r["product"], []).append(r)
    atsight_view = {}
    for p, rs in atsight.items():
        rs = sorted(rs, key=lambda r: r["at_sight_equiv"])
        gap = rs[-1]["at_sight_equiv"] - rs[0]["at_sight_equiv"] if len(rs) > 1 else 0
        out_rows = []
        for r in rs:
            label, url = _src(r["source"])
            out_rows.append({
                "region": r["region"], "price_type": r["price_type"],
                "payment": PAYMENT_LABEL.get(r.get("payment_term", "at_sight"), r.get("payment_term")),
                "raw": _raw_str(r), "landed_vnd_kg": r["landed_vnd_kg"],
                "usance_benefit": r["usance_benefit"], "at_sight_equiv": r["at_sight_equiv"],
                "source": r["source"], "label": label, "url": url,
                "date": r["date"], "fresh": lib.freshness(r["date"], today),
                "is_best": r["is_best"],
            })
        atsight_view[p] = {"gap": gap, "rows": out_rows}

    # 3) Bảng tất cả khu vực (giá gốc) — từ landed (đã có usd_per_ton)
    allregion = []
    for r in sorted(data["landed"], key=lambda r: (r["product"], r["at_sight_equiv"])):
        label, url = _src(r["source"])
        allregion.append({
            "product": r["product"].upper(), "region": r["region"], "price_type": r["price_type"],
            "payment": PAYMENT_LABEL.get(r.get("payment_term", "at_sight"), r.get("payment_term")),
            "raw": _raw_str(r), "usd_per_ton": r["usd_per_ton"], "landed_vnd_kg": r["landed_vnd_kg"],
            "source": r["source"], "label": label, "url": url,
            "date": r["date"], "fresh": lib.freshness(r["date"], today),
        })

    # 4) Nguồn & độ tươi (1 dòng/nguồn, ngày giá gần nhất)
    by_src = {}
    for r in sorted(rows, key=lambda x: x["date"]):
        by_src[r["source"]] = r
    sources = []
    for name, r in sorted(by_src.items()):
        label, url = _src(name)
        sources.append({"source": name, "label": label, "url": url,
                        "product": r["product"].upper(), "region": r["region"],
                        "price_type": r["price_type"], "date": r["date"],
                        "fresh": lib.freshness(r["date"], today)})

    # 5) Forecast theo product
    fc = {}
    for r in data["forecast"]:
        fc.setdefault(r["product"], {"meta": {"model": r["model"], "theils_u": r["theils_u"],
                                              "confidence": r["confidence"], "basis": r["basis"]},
                                     "rows": []})
        fc[r["product"]]["rows"].append({"week": r["week"], "yhat": r["yhat"],
                                         "lower": r["lower"], "upper": r["upper"]})

    return {
        "run_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M") if today == _today() else f"{today} 00:00",
        "fx": fx,
        "how_to_read": HOW_TO_READ,
        "cadence": CADENCE,
        "kpi": kpi,
        "narrative": data["narrative"],
        "atsight": atsight_view,
        "allregion": allregion,
        "spreads": data["spreads"],
        "forecast": fc,
        "alerts": data["alerts"],
        "commentary": data.get("commentary"),
        "sources": sources,
        "series": data["series"],
        "news": store.read_news(),
        "glossary": GLOSSARY,
    }
