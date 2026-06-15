from alerts import rules

THRESH = {"alert": {"action_buy": {"forecast_up_pct": 0.05},
                    "divergence": {"additive_up_pct": 0.05, "resin_down": True}}}


def test_divergence_card():
    ctx = {"resin_trend": {"pp": -0.8}, "additive_trend": {"tio2": 0.9},
           "best_source": {"pp": "DCE (TQ)", "pp_at_sight": 30502},
           "forecast_pct": {"pp": -3.5}}
    cards = rules.evaluate(ctx, THRESH)
    sev = {c["severity"] for c in cards}
    assert "PHAN_KY" in sev
    for c in cards:
        assert c["recommendation"]   # mỗi thẻ có "→ Đề xuất"


def test_best_source_card_present():
    ctx = {"resin_trend": {"pp": -0.8}, "additive_trend": {},
           "best_source": {"pp": "DCE (TQ)", "pp_at_sight": 30502}, "forecast_pct": {"pp": -3.5}}
    cards = rules.evaluate(ctx, THRESH)
    assert any("DCE" in c["title"] for c in cards)
