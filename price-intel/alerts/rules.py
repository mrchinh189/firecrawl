# -*- coding: utf-8 -*-
"""rules.py — sinh thẻ cảnh báo {severity,title,detail,recommendation} từ context + thresholds.
severity ∈ {MUA, THEO_DOI, PHAN_KY, CHO}. Tính 1 lần -> ghi analysis(kind='alerts')."""


def evaluate(ctx, thresholds) -> list:
    cards = []
    resin = ctx.get("resin_trend", {})
    add = ctx.get("additive_trend", {})
    best = ctx.get("best_source", {})
    fpct = ctx.get("forecast_pct", {})
    th = thresholds.get("alert", {})

    # 1) Nguồn tốt nhất sau quy đổi
    if best.get("pp"):
        at = best.get("pp_at_sight")
        cards.append({
            "severity": "THEO_DOI",
            "title": f"PP tốt nhất sau quy đổi: {best['pp']}",
            "detail": (f"≈ {at:,} đ/kg at-sight tương đương." if at else "Xem bảng quy đổi."),
            "recommendation": "Ưu tiên hỏi hàng nguồn này; chốt khối lượng vừa vì giá đang dò đáy.",
        })
    # 2) Phân kỳ phụ gia tăng khi resin giảm
    resin_down = any(v is not None and v < 0 for v in resin.values())
    add_up = [k for k, v in add.items() if v is not None and v > 0]
    if resin_down and add_up:
        names = ", ".join(k.upper() for k in add_up)
        cards.append({
            "severity": "PHAN_KY",
            "title": f"Phân kỳ: {names} tăng trong khi nhựa nền giảm",
            "detail": "Phụ gia tăng theo chi phí đầu vào riêng (không theo dầu).",
            "recommendation": "Review giá vốn hàng màu/compound; cân nhắc chốt phụ gia sớm.",
        })
    # 3) Tín hiệu chờ theo dự báo
    if fpct.get("pp") is not None and fpct["pp"] < 0:
        cards.append({
            "severity": "CHO",
            "title": f"Dự báo PP 6 tuần: {fpct['pp']:.1f}%",
            "detail": "Giá còn dịu.",
            "recommendation": "Mua cuốn chiếu theo nhu cầu; theo sát spread naphtha–ethylene để bắt đáy.",
        })
    return cards
