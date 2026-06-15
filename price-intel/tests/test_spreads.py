from analytics import spreads


def test_index_100():
    assert spreads.index_100([200, 210, 190]) == [100.0, 105.0, 95.0]


def test_compute_spreads_basic():
    latest = {"naphtha": 944, "ethylene": 1100, "propylene": 1020, "pp": 1189, "pe": 1127}
    out = spreads.compute(latest)
    names = {s["name"]: s["value"] for s in out}
    assert names["naphtha-ethylene"] == 1100 - 944
    assert names["pp-propylene"] == 1189 - 1020
    assert names["ethylene-pe"] == 1100 - 1127


def test_naphtha_ethylene_signal_low():
    latest = {"naphtha": 900, "ethylene": 1050}   # spread 150 < 250
    out = spreads.compute(latest)
    s = [x for x in out if x["name"] == "naphtha-ethylene"][0]
    assert "đáy" in s["signal"].lower()
