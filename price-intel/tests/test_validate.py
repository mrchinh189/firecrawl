from analytics import validate as V


def test_band_catches_unconverted_rmb():
    # Lỗi thật đã gặp: TiO2 = 14,846 (RMB/tấn chưa quy đổi) -> CAO bất thường
    msg = V.check_band("tio2", 14846)
    assert msg and "CAO bất thường" in msg


def test_band_catches_inflated_lldpe():
    # Lỗi audit cảnh báo: LLDPE $3,200 (thổi giá ~3 lần)
    msg = V.check_band("pe", 3200)
    assert msg and "CAO bất thường" in msg


def test_band_catches_too_low_tio2():
    # Lỗi audit: TiO2 báo $1,100 (thấp 50%)
    msg = V.check_band("tio2", 1100)
    assert msg and "THẤP bất thường" in msg


def test_band_ok_within_range():
    assert V.check_band("pe", 1165) is None
    assert V.check_band("tio2", 2344) is None
    assert V.check_band("stearic", 1180) is None


def test_cross_check_detects_inverted_tio2_resin():
    # audit: TiO2 phải > nhựa nền; nếu đảo -> bắt được
    warns = V.cross_checks({"tio2": 1100, "pp": 1189, "pe": 1165})
    assert any("ĐẢO GIÁ" in w for w in warns)


def test_cross_check_detects_zinc_lower_than_stearic():
    warns = V.cross_checks({"zinc_st": 1350, "stearic": 2450})
    assert any("zinc" in w.lower() or "ZINC" in w for w in warns)


def test_validate_clean_data_no_warnings():
    latest = {"pe": 1165, "pp": 1189, "tio2": 2344, "stearic": 1180, "zinc_st": 1760}
    assert V.validate(latest) == []


def test_validate_flags_audit_scenario():
    # Tái hiện đúng kịch bản sai trong file rà soát -> phải có cảnh báo
    bad = {"pe": 3200, "tio2": 1100, "stearic": 2450, "zinc_st": 1350}
    warns = V.validate(bad)
    assert len(warns) >= 3
    assert V.as_alert_cards(warns)[0]["severity"] == "DU_LIEU"
