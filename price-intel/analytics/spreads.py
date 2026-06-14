# -*- coding: utf-8 -*-
"""spreads.py — chỉ báo dẫn (Phần 1.2 tài liệu): naphtha–ethylene, PP–propylene, ethylene–PE,
integrated margin; và chỉ số gốc-100. Đầu vào là dict giá mới nhất theo product (USD/tấn)."""

NAPHTHA_ETHYLENE_FLOOR = 250   # USD/tấn — dưới ngưỡng kéo dài -> resin có thể tạo đáy


def index_100(series):
    """Quy chuỗi về gốc 100 ở điểm đầu."""
    if not series or series[0] == 0:
        return []
    base = series[0]
    return [round(v / base * 100, 1) for v in series]


def _pair(latest, a, b):
    if latest.get(a) is None or latest.get(b) is None:
        return None
    return round(latest[a] - latest[b], 1)


def compute(latest):
    """Trả list[dict] {name, value, unit, signal}. Bỏ qua spread thiếu vế."""
    out = []
    defs = [
        ("naphtha-ethylene", "ethylene", "naphtha"),
        ("pp-propylene", "pp", "propylene"),
        ("ethylene-pe", "ethylene", "pe"),
    ]
    for name, a, b in defs:
        v = _pair(latest, a, b)
        if v is None:
            continue
        signal = ""
        if name == "naphtha-ethylene" and v < NAPHTHA_ETHYLENE_FLOOR:
            signal = "Spread mỏng (<250 USD/t) → kỳ vọng cắt giảm công suất → resin có thể tạo đáy."
        out.append({"name": name, "value": v, "unit": "USD/tấn", "signal": signal})
    return out
