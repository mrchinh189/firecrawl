from app.analyzer import Analyzer, _fallback_analysis
from app.data_source import MockDataSource
from app.indicators import compute_indicators


def test_fallback_used_without_key(settings):
    snap = MockDataSource().fetch("NVL", 40)
    ind = compute_indicators(snap)
    text, ai_used = Analyzer(settings).analyze(ind, snap)
    assert ai_used is False
    assert "NVL" in text
    assert "khuyến nghị" in text.lower()  # có câu miễn trừ trách nhiệm


def test_fallback_trend_detection():
    snap = MockDataSource().fetch("NVL", 40)
    ind = compute_indicators(snap)
    text = _fallback_analysis("NVL", ind, snap)
    assert "RSI" in text
