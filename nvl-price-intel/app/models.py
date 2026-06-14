"""Các kiểu dữ liệu dùng chung trong pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PriceBar:
    """Một phiên giá (nến ngày)."""

    ticker: str
    date: str  # ISO yyyy-mm-dd
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


@dataclass
class TickerSnapshot:
    """Toàn bộ chuỗi giá của một mã, sắp xếp tăng dần theo ngày."""

    ticker: str
    bars: list[PriceBar] = field(default_factory=list)

    @property
    def latest(self) -> PriceBar:
        return self.bars[-1]

    @property
    def previous(self) -> PriceBar | None:
        return self.bars[-2] if len(self.bars) >= 2 else None


@dataclass
class Indicators:
    """Các chỉ báo kỹ thuật rút gọn."""

    last_close: float
    prev_close: float | None
    change: float
    change_pct: float
    sma5: float | None
    sma20: float | None
    rsi14: float | None
    high_period: float | None
    low_period: float | None
    avg_vol20: float | None
    last_volume: int

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class RunResult:
    """Kết quả một lần chạy pipeline cho một mã."""

    ticker: str
    snapshot: TickerSnapshot
    indicators: Indicators
    analysis: str
    summary: str
    docx_path: str | None = None
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    ai_used: bool = False
