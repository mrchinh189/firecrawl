import datetime as dt
import lib


def test_freshness_buckets():
    today = dt.date(2026, 6, 12)
    assert lib.freshness("2026-06-10", today)["emoji"] == "🟢"   # 2 ngày
    assert lib.freshness("2026-05-20", today)["emoji"] == "🟡"   # 23 ngày
    assert lib.freshness("2026-04-01", today)["emoji"] == "🔴"   # >30 ngày
    f = lib.freshness("2026-06-10", today)
    assert f["days"] == 2 and f["date"] == "2026-06-10"


def test_source_link_known_and_unknown():
    label, url = lib.source_link("EIA RBRTE")
    assert "EIA" in label and url and url.startswith("http")
    label2, url2 = lib.source_link("NCC A (form)")
    assert url2 is None   # form nội bộ
    label3, url3 = lib.source_link("Nguồn lạ chưa khai báo")
    assert label3 == "Nguồn lạ chưa khai báo" and url3 is None
