from analytics import narrative


def test_build_narrative_has_four_parts():
    ctx = {
        "resin_trend": {"pp": -0.8, "pe": -0.6},
        "additive_trend": {"tio2": 0.9, "stearic": -0.1},
        "best_source": {"pp": "DCE (TQ)"},
        "pp_gap_vnd_kg": 3383,
        "pp_forecast_pct": -3.5,
    }
    n = narrative.build(ctx)
    assert set(n.keys()) == {"picture", "why", "impact", "reco"}
    assert all(isinstance(v, str) and v for v in n.values())


def test_divergence_detected():
    ctx = {"resin_trend": {"pp": -0.8}, "additive_trend": {"tio2": 0.9},
           "best_source": {"pp": "DCE (TQ)"}, "pp_gap_vnd_kg": 3383, "pp_forecast_pct": -3.5}
    n = narrative.build_template(ctx)
    assert "phân kỳ" in (n["impact"] + n["why"]).lower()
