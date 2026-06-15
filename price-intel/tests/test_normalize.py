from collect import normalize


def test_product_key_aliases():
    assert normalize.product_key("Polypropylene") == "pp"
    assert normalize.product_key("LLDPE film grade") == "pe"
    assert normalize.product_key("Titanium dioxide rutile") == "tio2"
    assert normalize.product_key("xi măng") is None


def test_driver_aliases_palmoil_zinc():
    # Nguồn bổ sung: MPOC/Investing (dầu cọ) + LME (kẽm)
    assert normalize.product_key("Crude Palm Oil") == "palm_oil"
    assert normalize.product_key("FCPO futures") == "palm_oil"
    assert normalize.product_key("RBD Palm Olein") == "palm_oil"
    assert normalize.product_key("LME Zinc") == "lme_zinc"


def test_normalize_accepts_palmoil():
    raw = [{"product": "Crude Palm Oil", "value": "4100", "currency": "MYR", "unit": "ton",
            "region": "Bursa", "date": "2026-06-12"}]
    out = normalize.normalize(raw, source="MPOC palm oil")
    assert len(out) == 1 and out[0]["product"] == "palm_oil"


def test_norm_currency_unit():
    assert normalize.norm_currency("US$") == "USD"
    assert normalize.norm_currency("cents") == "USc"
    assert normalize.norm_unit("tonne") == "ton"
    assert normalize.norm_unit("pound") == "lb"


def test_norm_date():
    assert normalize.norm_date("2026/06/10") == "2026-06-10"
    assert normalize.norm_date("ngày 2026-6-9 ") == "2026-06-09"
    assert len(normalize.norm_date("không rõ")) == 10  # fallback hôm nay


def test_normalize_filters_and_maps():
    raw = [
        {"product": "Polypropylene", "value": "1,189", "currency": "USD", "unit": "ton",
         "region": "CFR SEA", "date": "2026-06-10"},
        {"product": "bao bì", "value": "100"},        # không phải NVL -> loại
        {"product": "PE", "value": "-5"},             # value<=0 -> loại
        {"product": "TiO2", "value": "abc"},          # value xấu -> loại
    ]
    out = normalize.normalize(raw, source="ThePlasticsExchange")
    assert len(out) == 1
    r = out[0]
    assert r["product"] == "pp" and r["value"] == 1189.0
    assert r["currency"] == "USD" and r["unit"] == "ton"
    assert r["source"] == "ThePlasticsExchange" and r["payment_term"] == "at_sight"
