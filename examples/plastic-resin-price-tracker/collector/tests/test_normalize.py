"""Unit test cho chuan hoa don vi/tien te. Chay: pytest (co stub fx)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import normalize  # noqa: E402


def setup_module(_):
    # Stub fx de khong goi mang: 1 USD = 25000 VND, EUR rate 0.9 (1 USD=0.9 EUR)
    normalize.fx.to_usd = lambda amount, currency: (
        amount if (currency or "USD").upper() == "USD" else amount / 0.9
    )
    normalize.fx.usd_to_vnd = lambda: 25000.0


def test_usd_per_lb_to_ton():
    row = normalize.normalize_row(
        {"material": "PP", "price": 1.0, "currency": "USD", "unit": "USD/lb"}, "PP"
    )
    assert round(row["price_usd_ton"]) == 2205
    assert row["price_vnd_ton"] == round(2204.62262 * 25000)


def test_usd_per_kg_to_ton():
    row = normalize.normalize_row(
        {"material": "PE", "price": 1.2, "currency": "USD", "unit": "USD/kg"}, "PE"
    )
    assert row["price_usd_ton"] == 1200.0


def test_usd_per_ton_passthrough():
    row = normalize.normalize_row(
        {"material": "HDPE", "price": 1100, "currency": "USD", "unit": "USD/ton"}, "HDPE"
    )
    assert row["price_usd_ton"] == 1100.0
    assert row["material"] == "HDPE"


def test_eur_converted_to_usd():
    row = normalize.normalize_row(
        {"material": "PP", "price": 900, "currency": "EUR", "unit": "EUR/ton"}, "PP"
    )
    assert round(row["price_usd_ton"]) == 1000  # 900 / 0.9


def test_invalid_material_becomes_other():
    row = normalize.normalize_row(
        {"material": "XYZ", "price": 1000, "unit": "USD/ton"}, "OTHER"
    )
    assert row["material"] == "OTHER"


def test_missing_price_returns_none():
    assert normalize.normalize_row({"material": "PP", "unit": "USD/ton"}, "PP") is None
