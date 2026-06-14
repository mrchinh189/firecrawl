# -*- coding: utf-8 -*-
"""free.py — nguồn FREE API/XML (không cần Firecrawl): EIA Brent, Vietcombank USD/VND, UN Comtrade.
Thiếu khóa -> SKIP (fail-soft). Trả list bản ghi chuẩn hóa để load.py nạp."""
import datetime as dt
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from collect import common


def eia_brent():
    """Brent spot (RBRTE) từ EIA API v2. Cần EIA_KEY. Đăng ký free: eia.gov/opendata."""
    if not common.has("EIA_KEY"):
        print("[skip] EIA_KEY trống")
        return []
    try:
        import requests
        url = ("https://api.eia.gov/v2/petroleum/pri/spt/data/"
               f"?api_key={common.env('EIA_KEY')}&frequency=daily&data[0]=value"
               "&facets[series][]=RBRTE&sort[0][column]=period&sort[0][direction]=desc&length=5")
        r = requests.get(url, timeout=40); r.raise_for_status()
        out = []
        for rec in r.json().get("response", {}).get("data", []):
            out.append(dict(date=rec["period"], product="brent", grade="", region="global",
                            incoterm="", currency="USD", unit="bbl", value=float(rec["value"]),
                            price_type="spot", payment_term="at_sight", source="EIA RBRTE", note=""))
        print(f"[OK] EIA Brent: {len(out)} bản ghi")
        return out
    except Exception as e:  # noqa: BLE001
        print(f"[skip] EIA lỗi: {e}")
        return []


def vietcombank_usdvnd():
    """USD/VND từ API JSON chính thức Vietcombank (không cần key). Fallback VNAppMob.
    Nguồn XML cũ (pXML.aspx) hay 403 với IP cloud -> dùng API JSON + Firecrawl khi cần."""
    import datetime as _dt
    today = _dt.date.today().isoformat()
    # 1) API JSON chính thức
    try:
        import requests
        r = requests.get(f"https://www.vietcombank.com.vn/api/exchangerates?date={today}",
                         timeout=30, headers={"User-Agent": "Mozilla/5.0 price-intel"})
        r.raise_for_status()
        for row in r.json().get("Data", []):
            if str(row.get("currencyCode", "")).upper() == "USD":
                sell = float(str(row.get("sell")).replace(",", ""))
                return [dict(date=today, pair="USD/VND", rate=sell, source="Vietcombank")]
    except Exception as e:  # noqa: BLE001
        print(f"[warn] Vietcombank API lỗi: {e} -> thử VNAppMob")
    # 2) Fallback VNAppMob (mirror VCB)
    try:
        import requests
        r = requests.get("https://vapi.vnappmob.com/api/v2/exchange_rate/vcb", timeout=30)
        r.raise_for_status()
        for row in r.json().get("results", []):
            if str(row.get("currency", "")).upper() == "USD":
                return [dict(date=today, pair="USD/VND", rate=float(row["sell"]),
                             source="Vietcombank")]
    except Exception as e:  # noqa: BLE001
        print(f"[skip] VNAppMob lỗi: {e}")
    return []


def comtrade_unit_value():
    """Unit value NK HS 3901/3902/3903 từ UN Comtrade. Cần COMTRADE_KEY. (khung — hoàn thiện khi chạy thật)."""
    if not common.has("COMTRADE_KEY"):
        print("[skip] COMTRADE_KEY trống")
        return []
    print("[..] UN Comtrade: thêm gọi comtradeapi.un.org với COMTRADE_KEY (HS 390110/390120...)")
    return []


def run():
    prices = eia_brent() + comtrade_unit_value()
    fx = vietcombank_usdvnd()
    return {"prices": prices, "fx": fx}


if __name__ == "__main__":
    out = run()
    print(f"[OK] free: {len(out['prices'])} giá, {len(out['fx'])} fx")
