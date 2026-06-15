# -*- coding: utf-8 -*-
"""validate.py — kiểm tra TÍNH HỢP LÝ của giá đã chuẩn hóa (USD/tấn) trước khi đưa vào báo cáo.

Bắt đúng lớp lỗi mà rà soát chỉ ra: bóc nhầm grade / đảo đơn vị (cents↔USD, RMB↔USD) /
hoán đổi giá NVL. KHÔNG xóa dữ liệu — chỉ sinh CẢNH BÁO data-quality để người duyệt.

Hàm thuần, test được không cần mạng/DB."""
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
import lib


def check_band(product, usd_per_ton, bands=None):
    """Trả chuỗi cảnh báo nếu giá ngoài dải hợp lý của NVL; None nếu OK/không có dải."""
    bands = bands if bands is not None else lib.load_yaml("price_bands.yaml")
    if product == "brent":
        b = bands.get("brent_usd_bbl", {})
        lo, hi, unit = b.get("min"), b.get("max"), "USD/bbl"
    elif product == "lme_zinc":
        b = bands.get("lme_zinc_usd_ton", {})
        lo, hi, unit = b.get("min"), b.get("max"), "USD/tấn"
    else:
        b = bands.get("bands_usd_ton", {}).get(product)
        if not b:
            return None
        lo, hi, unit = b.get("min"), b.get("max"), "USD/tấn"
    if usd_per_ton is None or lo is None or hi is None:
        return None
    if usd_per_ton < lo:
        return f"{product.upper()} = {usd_per_ton:,.0f} {unit} THẤP bất thường (dải hợp lý {lo:,}–{hi:,}). Nghi bóc nhầm grade thấp / đảo đơn vị."
    if usd_per_ton > hi:
        return f"{product.upper()} = {usd_per_ton:,.0f} {unit} CAO bất thường (dải hợp lý {lo:,}–{hi:,}). Nghi nhầm đơn vị (RMB/tấn hay cents/lb chưa quy đổi) / nhầm grade đặc chủng."
    return None


def cross_checks(latest, bands=None):
    """Kiểm tra tương quan chéo (vd TiO2 phải > nhựa nền; zinc_st > stearic)."""
    bands = bands if bands is not None else lib.load_yaml("price_bands.yaml")
    out = []
    for rule in bands.get("cross_rules", []):
        hi_p, lo_p = rule.get("higher"), rule.get("lower")
        hv, lv = latest.get(hi_p), latest.get(lo_p)
        if hv is None or lv is None:
            continue
        if hv <= lv:
            out.append(f"{rule.get('desc')} — nhưng {hi_p.upper()}={hv:,.0f} ≤ {lo_p.upper()}={lv:,.0f}. Nghi ĐẢO GIÁ.")
    return out


def validate(latest, bands=None):
    """Trả list cảnh báo data-quality từ band-check + cross-check trên dict latest (USD/tấn)."""
    bands = bands if bands is not None else lib.load_yaml("price_bands.yaml")
    warns = []
    for product, val in latest.items():
        msg = check_band(product, val, bands)
        if msg:
            warns.append(msg)
    warns.extend(cross_checks(latest, bands))
    return warns


def as_alert_cards(warns):
    """Đổi cảnh báo thành thẻ {severity=DU_LIEU} để hiện ở mục ⑦ báo cáo."""
    cards = []
    for w in warns:
        cards.append({
            "severity": "DU_LIEU",
            "title": "Cảnh báo chất lượng dữ liệu",
            "detail": w,
            "recommendation": "Đối chiếu lại nguồn/đơn vị trước khi dùng làm cơ sở tính giá thành.",
        })
    return cards
