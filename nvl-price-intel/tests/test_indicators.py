from app.data_source import MockDataSource
from app.indicators import compute_indicators
from app.models import PriceBar, TickerSnapshot


def _snap(closes):
    bars = [
        PriceBar("NVL", f"2026-05-{i+1:02d}", c, c, c, c, 1_000_000)
        for i, c in enumerate(closes)
    ]
    return TickerSnapshot("NVL", bars)


def test_change_calculation():
    ind = compute_indicators(_snap([10.0, 11.0]))
    assert ind.last_close == 11.0
    assert ind.prev_close == 10.0
    assert ind.change == 1.0
    assert ind.change_pct == 10.0


def test_sma_and_rsi_present_with_enough_data():
    snap = MockDataSource().fetch("NVL", 40)
    ind = compute_indicators(snap)
    assert ind.sma5 is not None
    assert ind.sma20 is not None
    assert ind.rsi14 is not None
    assert 0 <= ind.rsi14 <= 100


def test_rsi_all_gains_is_100():
    ind = compute_indicators(_snap([float(i) for i in range(1, 20)]))
    assert ind.rsi14 == 100.0


def test_indicators_require_data():
    import pytest

    with pytest.raises(ValueError):
        compute_indicators(TickerSnapshot("NVL", []))
