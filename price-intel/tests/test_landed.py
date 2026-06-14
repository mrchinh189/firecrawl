import pytest
from analytics import landed

CFG = {
    "interest_pct_year": 0.065, "usd_rmb": 7.15,
    "default": {"freight_insurance_pct": 0.07, "domestic_cost_vnd_kg": 800},
    "duty_pct": {"pp": 0.03, "pe": 0.02, "default": 0.03},
    "payment_term_days": {"at_sight": 0, "lc_90": 90},
    "region_overrides": {},
}


def test_to_usd_per_ton_conversions():
    assert landed.to_usd_per_ton(1189, "USD", "ton", 7.15) == pytest.approx(1189)
    assert landed.to_usd_per_ton(2.34, "USD", "kg", 7.15) == pytest.approx(2340)
    assert landed.to_usd_per_ton(50, "USc", "lb", 7.15) == pytest.approx(1102.3, abs=0.1)
    assert landed.to_usd_per_ton(7604, "RMB", "ton", 7.15) == pytest.approx(1063.5, abs=0.1)
    assert landed.to_usd_per_ton(93, "USD", "bbl", 7.15) is None  # dầu thô không landed


def test_landed_vnd_kg_formula():
    # 1189 USD/t ×1.07 (cước+bh) ×1.03 (thuế) ×26412 /1000 + 800 nội địa
    v = landed.landed_vnd_kg(1189, 26412, duty_pct=0.03, freight_ins_pct=0.07, domestic_vnd_kg=800)
    assert v == 35410


def test_usance_and_at_sight():
    benefit = landed.usance_benefit(35414, interest_pct_year=0.065, days=90)
    assert benefit == 568
    assert landed.at_sight_equiv(35414, benefit) == 35414 - 568


def test_compute_rows_ranks_best():
    rows = [
        {"product": "pp", "region": "DCE (TQ)", "price_type": "futures", "payment_term": "at_sight",
         "value": 7604, "currency": "RMB", "unit": "ton", "source": "DCE delayed", "date": "2026-06-10"},
        {"product": "pp", "region": "VN import (CIF)", "price_type": "unit_value", "payment_term": "at_sight",
         "value": 1231, "currency": "USD", "unit": "ton", "source": "UN Comtrade", "date": "2026-04-30"},
    ]
    out = landed.compute(rows, fx_usdvnd=26412, cfg=CFG)
    assert sum(1 for r in out if r["is_best"]) == 1
    best = [r for r in out if r["is_best"]][0]
    assert best["at_sight_equiv"] == min(r["at_sight_equiv"] for r in out)
