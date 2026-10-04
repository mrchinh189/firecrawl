"""Test offline cho các parser, dùng markdown thật Firecrawl trả về (rút gọn).

Chạy: python -m pytest test_parsers.py
"""

from datetime import date

import pytest

from scrape_prices import PriceRecord, append_csv, parse_100ppi, parse_investing, parse_lme, parse_mpoc

TODAY = date(2026, 10, 4)

INVESTING_MD = """# Malaysian Crude Palm Oil Futures - (CPOc1)

CME

Tiền tệ tính theo USD

Thêm vào Danh Mục

1,121.25

-5.25(-0.47%)

Đóng cửa·02/10

Biên độ ngày

1,121.25
"""

PPI_MD = """硫酸价格走势

|     |     |     |
| --- | --- | --- |
| 日期 | 价格 | 日涨跌 |
| 10-04 | - | -% |
| 10-03 | 1710.00 | 0.00% |
| 10-02 | 1710.00 | 0.00% |
| 09-30 | 1710.00 | -1.58% |
"""

MPOC_MD = """Daily Palm Oil Prices

## CPO Prices

| Pricing Date | Settlement Price RM |
| --- | --- |
| 29 Sep 26 | 4624 |
| 30 Sep 26 | 4610 |
| 1 Oct 26 | 4554 |

## CPO , SFO and SBO Prices (US$/MT)

| Date | CPO, BMD+3 | SBO, ARG FOB |
| --- | --- | --- |
| 26-Jan | 1064 | 1188 |
"""

LME_MD = """Trading SUMMARY

Prices in US$

Data valid for 02 Oct 2026

3710.50

 -0.36%

3-month Closing Price (day-delayed)
"""


def test_investing():
    assert parse_investing(INVESTING_MD, {}, TODAY) == {
        "price": 1121.25, "change_pct": -0.47, "price_date": "2026-10-02",
    }


def test_investing_metadata_fallback():
    meta = {"global-translation-variables": '"{\\"LAST_PRICE\\":\\"1,121.25\\"}"'}
    assert parse_investing("no price here", meta, TODAY)["price"] == 1121.25


def test_100ppi_skips_unpublished_today():
    assert parse_100ppi(PPI_MD, {}, TODAY) == {
        "price": 1710.0, "change_pct": 0.0, "price_date": "2026-10-03",
    }


def test_100ppi_year_rollover():
    md = "| 12-31 | 1500.00 | 1.00% |\n"
    assert parse_100ppi(md, {}, date(2027, 1, 2))["price_date"] == "2026-12-31"


def test_mpoc_takes_latest_row_of_cpo_table():
    assert parse_mpoc(MPOC_MD, {}, TODAY) == {
        "price": 4554.0, "change_pct": -1.21, "price_date": "2026-10-01",
    }


def test_lme():
    assert parse_lme(LME_MD, {}, TODAY) == {
        "price": 3710.5, "change_pct": -0.36, "price_date": "2026-10-02",
    }


@pytest.mark.parametrize("parser", [parse_investing, parse_100ppi, parse_mpoc, parse_lme])
def test_parsers_fail_loudly_on_unrendered_page(parser):
    # Ví dụ LME khi chưa render JS: chỉ có khung trang, không có số -> phải raise để kích hoạt fallback.
    with pytest.raises(ValueError):
        parser("Trading SUMMARY\n\nPrices in US$\n", {}, TODAY)


def test_append_csv_dedupes(tmp_path):
    path = tmp_path / "prices.csv"
    rec = PriceRecord(source="lme_zinc", material="Zinc", price=3710.5, unit="USD/t", price_date="2026-10-02")
    assert append_csv(path, [rec]) == 1
    assert append_csv(path, [rec]) == 0
