"""Lay ti gia: USD->VND va cac dong tien khac ve USD."""
import logging

import requests

import config

log = logging.getLogger("fx")

# Cache trong 1 lan chay
_rates_cache: dict | None = None


def _fetch_rates() -> dict:
    """Tra ve dict rates: 1 USD = rates[CCY] don vi CCY. Co fallback."""
    global _rates_cache
    if _rates_cache is not None:
        return _rates_cache
    try:
        resp = requests.get(config.FX_API_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("rates") or {}
        if "VND" not in rates:
            rates["VND"] = config.FX_USD_VND_FALLBACK
        _rates_cache = rates
        log.info("Lay ti gia thanh cong (USD->VND=%s)", rates.get("VND"))
    except Exception as exc:  # noqa: BLE001
        log.warning("Khong lay duoc ti gia (%s), dung fallback", exc)
        _rates_cache = {"USD": 1.0, "VND": config.FX_USD_VND_FALLBACK}
    return _rates_cache


def usd_to_vnd() -> float:
    return float(_fetch_rates().get("VND", config.FX_USD_VND_FALLBACK))


def to_usd(amount: float, currency: str) -> float:
    """Quy doi mot so tien ve USD. rates[CCY] = so CCY tren 1 USD."""
    ccy = (currency or "USD").upper()
    if ccy in ("USD", "$", "US$", "USD$"):
        return amount
    rate = _fetch_rates().get(ccy)
    if not rate:
        log.warning("Khong co ti gia cho %s, giu nguyen coi nhu USD", ccy)
        return amount
    return amount / float(rate)
