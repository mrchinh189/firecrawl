# -*- coding: utf-8 -*-
"""normalize.py — chuẩn hóa bản ghi giá AI-extract về schema price_master/staging (hàm thuần).

Dùng sau khi firecrawl_client.ai_extract trả list dict thô từ từng nguồn. Map tên sản phẩm
về key chuẩn (materials.yaml), chuẩn hóa currency/unit/date, loại bản ghi không hợp lệ.
Test được không cần mạng."""
import datetime as dt
import pathlib
import re
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
import lib

# Bí danh tên sản phẩm -> key chuẩn trong materials.yaml
ALIASES = {
    "polypropylene": "pp", "pp": "pp", "homopolymer": "pp",
    "polyethylene": "pe", "pe": "pe", "lldpe": "pe", "ldpe": "pe",
    "hdpe": "hdpe",
    "polystyrene": "ps", "ps": "ps", "gpps": "ps", "hips": "ps", "abs": "ps",
    "titanium dioxide": "tio2", "tio2": "tio2", "rutile": "tio2",
    "stearic acid": "stearic", "stearic": "stearic",
    "pe wax": "pe_wax", "polyethylene wax": "pe_wax",
    "zinc stearate": "zinc_st", "calcium stearate": "ca_st",
    "carbon black": "carbon", "naphtha": "naphtha", "ethylene": "ethylene",
    "propylene": "propylene", "brent": "brent",
    # Driver oleochemical & kẽm (nguồn MPOC/Investing/LME)
    "palm oil": "palm_oil", "crude palm oil": "palm_oil", "cpo": "palm_oil",
    "fcpo": "palm_oil", "palm olein": "palm_oil", "rbd palm olein": "palm_oil",
    "zinc": "lme_zinc", "lme zinc": "lme_zinc",
}

CUR_MAP = {"usd": "USD", "us$": "USD", "$": "USD", "usc": "USc", "cents": "USc", "¢": "USc",
           "rmb": "RMB", "cny": "RMB", "¥": "RMB", "vnd": "VND", "đ": "VND"}
UNIT_MAP = {"ton": "ton", "tonne": "ton", "mt": "ton", "t": "ton",
            "kg": "kg", "lb": "lb", "pound": "lb", "bbl": "bbl", "barrel": "bbl", "index": "index"}


def product_key(name):
    """Map tên sản phẩm tự do -> key chuẩn. None nếu không nhận ra."""
    if not name:
        return None
    s = str(name).strip().lower()
    if s in ALIASES:
        return ALIASES[s]
    for alias, key in ALIASES.items():
        if alias in s:
            return key
    return None


def norm_currency(cur):
    return CUR_MAP.get(str(cur or "").strip().lower(), str(cur or "").strip().upper())


def norm_unit(unit):
    u = str(unit or "").strip().lower()
    return UNIT_MAP.get(u, u)


def norm_date(value):
    """Chuẩn hóa về YYYY-MM-DD. Không parse được -> hôm nay."""
    s = str(value or "").strip()
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        y, mo, d = m.groups()
        try:
            return dt.date(int(y), int(mo), int(d)).isoformat()
        except ValueError:
            pass
    return dt.date.today().isoformat()


def normalize(records, source="", region=""):
    """Chuẩn hóa list[dict] thô -> list bản ghi staging hợp lệ. Bỏ bản ghi thiếu product/value."""
    valid_keys = {m["key"] for m in lib.load_yaml("materials.yaml").get("materials", [])}
    valid_keys |= set(lib.load_yaml("materials.yaml").get("feedstock", []))
    out = []
    for r in records or []:
        key = product_key(r.get("product"))
        if not key or (valid_keys and key not in valid_keys):
            continue
        try:
            value = float(str(r.get("value")).replace(",", ""))
        except (TypeError, ValueError):
            continue
        if value <= 0:
            continue
        out.append({
            "date": norm_date(r.get("date")),
            "product": key, "grade": str(r.get("grade", "") or ""),
            "region": r.get("region") or region or "n/a",
            "incoterm": str(r.get("incoterm", "") or ""),
            "currency": norm_currency(r.get("currency")),
            "unit": norm_unit(r.get("unit")),
            "value": value,
            "price_type": str(r.get("price_type", "spot") or "spot"),
            "payment_term": str(r.get("payment_term", "at_sight") or "at_sight"),
            "source": r.get("source") or source or "unknown",
            "note": str(r.get("note", "") or ""),
        })
    return out
