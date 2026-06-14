import os

from app.pipeline import run_all, run_one


def test_run_one_end_to_end(settings):
    result = run_one("NVL", settings)
    assert result.ticker == "NVL"
    assert result.indicators.last_close > 0
    assert result.analysis  # có nội dung phân tích (fallback)
    assert result.ai_used is False
    assert result.docx_path and os.path.isfile(result.docx_path)
    assert "NVL" in result.summary


def test_run_one_persists_prices(settings):
    import sqlite3

    run_one("NVL", settings)
    conn = sqlite3.connect(settings.sqlite_path)
    count = conn.execute("SELECT COUNT(*) FROM prices WHERE ticker='NVL'").fetchone()[0]
    runs = conn.execute("SELECT COUNT(*) FROM runs WHERE ticker='NVL'").fetchone()[0]
    conn.close()
    assert count > 0
    assert runs == 1


def test_run_all_multiple_tickers(settings):
    settings.tickers = "NVL,VIC"
    results = run_all(settings)
    assert {r.ticker for r in results} == {"NVL", "VIC"}
