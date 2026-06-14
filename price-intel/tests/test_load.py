from db import load


def test_pct_jump():
    assert load.pct_jump(100, 110) == 0.1
    assert load.pct_jump(0, 110) is None
    assert load.pct_jump(None, 5) is None


def test_qc_row_missing_field():
    ok, flag = load.qc_row({"date": "2026-06-10", "product": "pp"})
    assert ok is False and "thiếu" in flag


def test_qc_row_negative_value():
    row = {"date": "2026-06-10", "product": "pp", "region": "x", "currency": "USD",
           "unit": "ton", "value": -1, "price_type": "spot", "source": "s"}
    ok, flag = load.qc_row(row)
    assert ok is False


def test_qc_row_jump_flags_review():
    row = {"date": "2026-06-10", "product": "pp", "region": "x", "currency": "USD",
           "unit": "ton", "value": 200, "price_type": "spot", "source": "s"}
    ok, flag = load.qc_row(row, prev_value=100, jump_pct=0.10)   # nhảy 100%
    assert ok is True and flag == "review"


def test_qc_index_not_flagged():
    row = {"date": "2026-06-10", "product": "pp", "region": "x", "currency": "USD",
           "unit": "index", "value": 200, "price_type": "index", "source": "FRED"}
    ok, flag = load.qc_row(row, prev_value=100, jump_pct=0.10)
    assert ok is True and flag is None     # chuỗi index nới QC


def test_to_vnd_kg():
    assert load.to_vnd_kg(1189, 26412) == round(1189 * 26412 / 1000)
    assert load.to_vnd_kg(None, 26412) is None


def test_load_offline_runs():
    res = load.load()   # đọc fixtures, dry-run
    assert res["loaded"] > 0
