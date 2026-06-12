"""Chuan hoa don vi/tien te ve USD/tan va VND/tan."""
import logging
import re

import fx

log = logging.getLogger("normalize")

# He so quy doi khoi luong ve 1 tan (metric ton = 1000 kg)
LB_PER_TON = 2204.62262
KG_PER_TON = 1000.0

VALID_MATERIALS = {"PP", "PE", "HDPE", "LDPE", "LLDPE", "OTHER"}


def _parse_unit(unit_raw: str) -> float:
    """Tra ve he so nhan: gia_moi_tan = gia * factor. Mac dinh coi la /tan."""
    u = (unit_raw or "").lower().replace(" ", "")
    if "lb" in u or "pound" in u:
        return LB_PER_TON          # USD/lb -> *2204.62 = USD/ton
    if "/kg" in u or "perkg" in u or u.endswith("kg"):
        return KG_PER_TON          # USD/kg -> *1000 = USD/ton
    # ton / tonne / mt / metricton -> giu nguyen
    return 1.0


def _detect_currency(currency_raw: str, unit_raw: str) -> str:
    text = f"{currency_raw or ''} {unit_raw or ''}".upper()
    for ccy in ("USD", "EUR", "CNY", "RMB", "JPY", "VND", "INR", "GBP"):
        if ccy in text:
            return "CNY" if ccy == "RMB" else ccy
    if "€" in text:
        return "EUR"
    if "£" in text:
        return "GBP"
    return "USD"


def normalize_material(material_raw: str) -> str:
    m = (material_raw or "").strip().upper()
    return m if m in VALID_MATERIALS else "OTHER"


def _to_number(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = re.sub(r"[^0-9.\-]", "", str(value))
    try:
        return float(s) if s not in ("", "-", ".") else None
    except ValueError:
        return None


def normalize_row(raw: dict, fallback_material: str) -> dict | None:
    """Bien 1 dong gia tho thanh ban ghi chuan hoa. None neu khong hop le."""
    price = _to_number(raw.get("price"))
    if price is None:
        return None

    currency = _detect_currency(raw.get("currency"), raw.get("unit"))
    unit_factor = _parse_unit(raw.get("unit"))

    price_usd = fx.to_usd(price, currency)
    price_usd_ton = price_usd * unit_factor
    fx_vnd = fx.usd_to_vnd()
    price_vnd_ton = price_usd_ton * fx_vnd

    return {
        "material": normalize_material(raw.get("material") or fallback_material),
        "grade": (raw.get("grade") or "").strip()[:200],
        "region": (raw.get("region") or "").strip()[:120],
        "price_raw": price,
        "currency_raw": currency,
        "unit_raw": (raw.get("unit") or "").strip()[:60],
        "price_usd_ton": round(price_usd_ton, 2),
        "price_vnd_ton": round(price_vnd_ton, 0),
        "fx_usd_vnd": round(fx_vnd, 2),
        "price_date": _parse_date(raw.get("date")),
    }


def _parse_date(value) -> str | None:
    """Tra ve chuoi YYYY-MM-DD neu nhan dien duoc, nguoc lai None (DB se dung)."""
    if not value:
        return None
    s = str(value)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0)
    return None
