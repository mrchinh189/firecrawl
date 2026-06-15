import pytest
from forecast import run


def test_naive_and_ma():
    assert run.naive([10, 12, 14], 3) == [14, 14, 14]
    assert run.moving_average([9, 12, 15], 2, window=3) == [12.0, 12.0]


def test_theils_u():
    u = run.theils_u(actual=[10, 12, 14], pred=[11, 12, 13], naive=[9, 9, 9])
    assert u == pytest.approx(0.239, abs=0.005)


def test_forecast_series_short_series_uses_naive():
    res = run.forecast_series([10, 11], horizon=6)
    assert res["model"] == "naive"
    assert len(res["yhat"]) == 6
    assert res["confidence"] == "thấp"


def test_forecast_series_returns_band_and_basis():
    series = [100, 101, 102, 101, 103, 104, 103, 105, 106, 105, 107, 108]
    res = run.forecast_series(series, horizon=6, basis="spot dài")
    assert len(res["yhat"]) == 6 and len(res["lower"]) == 6 and len(res["upper"]) == 6
    assert res["basis"] == "spot dài"
    assert "theils_u" in res
