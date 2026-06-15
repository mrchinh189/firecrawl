from analytics import build_analysis


def test_full_chain_on_fixtures():
    out = build_analysis.run()   # không có DB -> đọc fixtures, ghi dry-run
    pp = [r for r in out["landed"] if r["product"] == "pp"]
    assert len(pp) >= 3
    assert sum(1 for r in pp if r["is_best"]) == 1
    assert any(s["name"] == "naphtha-ethylene" for s in out["spreads"])
    pp_fc = [r for r in out["forecast"] if r["product"] == "pp"]
    assert len(pp_fc) == 6 and pp_fc[0]["confidence"] in ("thấp", "vừa", "cao")
    assert set(out["narrative"].keys()) == {"picture", "why", "impact", "reco"}
    assert all(c["recommendation"] for c in out["alerts"])
