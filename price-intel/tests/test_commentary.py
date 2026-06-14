from forecast import commentary


def test_commentary_without_key_returns_none(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert commentary.build({"forecast_pct": {"pp": -3.5}}, [], []) is None


def test_build_analysis_includes_commentary_key():
    from analytics import build_analysis
    out = build_analysis.run()
    assert "commentary" in out          # có khóa (None khi không có Claude)
