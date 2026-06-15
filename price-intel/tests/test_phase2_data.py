from analytics import build_analysis, store


def test_run_returns_kpi_rows_series():
    out = build_analysis.run()
    assert "kpi" in out and "latest" in out["kpi"] and "fx" in out["kpi"]
    assert out["kpi"]["latest"].get("pp")            # có giá PP mới nhất
    assert "rows" in out and len(out["rows"]) > 0
    assert "series" in out and out["series"].get("pp")  # chuỗi PP theo thời gian
    d, v = out["series"]["pp"][0]
    assert isinstance(d, str) and isinstance(v, (int, float))


def test_read_news_from_fixture():
    news = store.read_news()
    assert len(news) >= 2
    assert news[0]["url"].startswith("http")
    assert "title" in news[0] and "published_at" in news[0]
