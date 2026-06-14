# -*- coding: utf-8 -*-
"""free.py — nguồn FREE API/XML (không cần Firecrawl): EIA Brent, Vietcombank USD/VND, UN Comtrade.
Thiếu khóa -> SKIP (fail-soft). Trả list bản ghi chuẩn hóa để load.py nạp."""
import datetime as dt
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from collect import common


def eia_brent():
    """Brent spot (RBRTE) từ EIA API. Cần EIA_KEY."""
    if not common.has("EIA_KEY"):
        print("[skip] EIA_KEY trống")
        return []
    try:
        import requests
        url = ("https://api.eia.gov/v2/petroleum/pri/spt/data/"
               f"?api_key={common.env('EIA_KEY')}&frequency=daily&data[0]=value"
               "&facets[product][]=EPCBRENT&sort[0][column]=period&sort[0][direction]=desc&length=5")
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
    """USD/VND từ XML công khai Vietcombank (không cần key)."""
    try:
        import requests
        from bs4 import BeautifulSoup
        r = requests.get("https://portal.vietcombank.com.vn/UserControls/TVPortal.TyGia/pXML.aspx",
                         timeout=30, headers={"User-Agent": "price-intel"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")
        for ex in soup.find_all("Exrate"):
            if ex.get("CurrencyCode") == "USD":
                sell = float(str(ex.get("Sell")).replace(",", ""))
                return [dict(date=dt.date.today().isoformat(), pair="USD/VND",
                             rate=sell, source="Vietcombank")]
    except Exception as e:  # noqa: BLE001
        print(f"[skip] Vietcombank lỗi: {e}")
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
