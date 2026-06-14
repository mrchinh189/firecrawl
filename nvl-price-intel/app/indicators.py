"""Tính các chỉ báo kỹ thuật cơ bản từ chuỗi giá."""
from __future__ import annotations

from .models import Indicators, TickerSnapshot


def _sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return round(sum(values[-period:]) / period, 4)


def _rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    for i in range(-period, 0):
        delta = closes[i] - closes[i - 1]
        if delta >= 0:
            gains += delta
        else:
            losses -= delta
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def compute_indicators(snapshot: TickerSnapshot) -> Indicators:
    bars = snapshot.bars
    if not bars:
        raise ValueError("Không có dữ liệu giá để tính chỉ báo")

    closes = [b.close for b in bars]
    volumes = [b.volume for b in bars]
    last = bars[-1]
    prev_close = bars[-2].close if len(bars) >= 2 else None

    change = round(last.close - prev_close, 4) if prev_close is not None else 0.0
    change_pct = (
        round((change / prev_close) * 100, 2) if prev_close not in (None, 0) else 0.0
    )

    avg_vol20 = None
    if len(volumes) >= 20:
        avg_vol20 = round(sum(volumes[-20:]) / 20, 0)

    return Indicators(
        last_close=last.close,
        prev_close=prev_close,
        change=change,
        change_pct=change_pct,
        sma5=_sma(closes, 5),
        sma20=_sma(closes, 20),
        rsi14=_rsi(closes, 14),
        high_period=round(max(b.high for b in bars), 4),
        low_period=round(min(b.low for b in bars), 4),
        avg_vol20=avg_vol20,
        last_volume=last.volume,
    )
