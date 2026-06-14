"""Nguồn dữ liệu giá cổ phiếu Việt Nam.

Mặc định dùng API công khai của TCBS (không cần API key). Thiết kế dạng
interface để dễ thay nguồn khác (VNDirect, SSI, scrape qua Firecrawl, ...).
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx

from .logging_config import get_logger
from .models import PriceBar, TickerSnapshot

logger = get_logger(__name__)


class DataSourceError(RuntimeError):
    """Lỗi khi lấy dữ liệu giá."""


class DataSource:
    """Interface nguồn dữ liệu."""

    def fetch(self, ticker: str, count: int) -> TickerSnapshot:  # pragma: no cover
        raise NotImplementedError


class TCBSDataSource(DataSource):
    """Lấy nến ngày từ API công khai của TCBS."""

    BASE_URL = "https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars-long-term"

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    def fetch(self, ticker: str, count: int) -> TickerSnapshot:
        ticker = ticker.upper()
        params = {
            "ticker": ticker,
            "type": "stock",
            "resolution": "D",
            "to": int(time.time()),
            "countBack": max(count, 30),
        }
        try:
            resp = httpx.get(self.BASE_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
            payload = resp.json()
        except httpx.HTTPError as exc:
            raise DataSourceError(f"Không lấy được dữ liệu {ticker}: {exc}") from exc

        return self._parse(ticker, payload)

    @staticmethod
    def _parse(ticker: str, payload: dict) -> TickerSnapshot:
        rows = payload.get("data") or []
        if not rows:
            raise DataSourceError(f"Dữ liệu rỗng cho {ticker}")

        bars: list[PriceBar] = []
        for row in rows:
            raw_date = row.get("tradingDate") or row.get("date") or ""
            iso_date = TCBSDataSource._normalize_date(raw_date)
            bars.append(
                PriceBar(
                    ticker=ticker,
                    date=iso_date,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(row.get("volume", 0) or 0),
                )
            )
        bars.sort(key=lambda b: b.date)
        logger.info("Lấy được %d phiên cho %s", len(bars), ticker)
        return TickerSnapshot(ticker=ticker, bars=bars)

    @staticmethod
    def _normalize_date(raw: str) -> str:
        if not raw:
            return ""
        # TCBS trả ISO hoặc epoch tuỳ endpoint; chuẩn hoá về yyyy-mm-dd.
        if raw.isdigit():
            return (
                datetime.fromtimestamp(int(raw), tz=timezone.utc)
                .date()
                .isoformat()
            )
        # Cắt phần thời gian nếu có (vd "2026-06-12T00:00:00Z").
        return raw[:10]


class MockDataSource(DataSource):
    """Nguồn giả lập cho test / demo offline (không cần mạng)."""

    def __init__(self, base_price: float = 12.0) -> None:
        self.base_price = base_price

    def fetch(self, ticker: str, count: int) -> TickerSnapshot:
        from datetime import date, timedelta

        bars: list[PriceBar] = []
        price = self.base_price
        start = date(2026, 1, 1)
        for i in range(count):
            # Dao động giả lập có xu hướng nhẹ.
            price = round(price * (1 + (((i * 7) % 11) - 5) / 100.0), 2)
            price = max(price, 1.0)
            bars.append(
                PriceBar(
                    ticker=ticker.upper(),
                    date=(start + timedelta(days=i)).isoformat(),
                    open=round(price * 0.99, 2),
                    high=round(price * 1.02, 2),
                    low=round(price * 0.98, 2),
                    close=price,
                    volume=1_000_000 + i * 1000,
                )
            )
        return TickerSnapshot(ticker=ticker.upper(), bars=bars)


def get_data_source(name: str, timeout: float = 20.0) -> DataSource:
    name = (name or "tcbs").lower()
    if name == "mock":
        return MockDataSource()
    if name == "tcbs":
        return TCBSDataSource(timeout=timeout)
    raise DataSourceError(f"Nguồn dữ liệu không hỗ trợ: {name}")
