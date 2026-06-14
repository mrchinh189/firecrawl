import pytest

from app.data_source import MockDataSource, TCBSDataSource, DataSourceError


def test_mock_source_returns_requested_count():
    snap = MockDataSource().fetch("NVL", 40)
    assert snap.ticker == "NVL"
    assert len(snap.bars) == 40
    assert all(b.close > 0 for b in snap.bars)
    # Sắp xếp tăng dần theo ngày
    assert snap.bars == sorted(snap.bars, key=lambda b: b.date)


def test_tcbs_parse_payload():
    payload = {
        "data": [
            {"tradingDate": "2026-06-10T00:00:00Z", "open": 11.0, "high": 11.5,
             "low": 10.8, "close": 11.2, "volume": 1500000},
            {"tradingDate": "2026-06-11T00:00:00Z", "open": 11.2, "high": 11.9,
             "low": 11.1, "close": 11.8, "volume": 2000000},
        ]
    }
    snap = TCBSDataSource._parse("NVL", payload)
    assert len(snap.bars) == 2
    assert snap.latest.close == 11.8
    assert snap.latest.date == "2026-06-11"


def test_tcbs_parse_empty_raises():
    with pytest.raises(DataSourceError):
        TCBSDataSource._parse("NVL", {"data": []})


def test_normalize_epoch_date():
    iso = TCBSDataSource._normalize_date("1749513600")  # epoch giây
    assert len(iso) == 10 and iso.count("-") == 2
