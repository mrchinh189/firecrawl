# -*- coding: utf-8 -*-
"""landed.py — quy đổi GIÁ CHUNG: chuẩn hóa USD/tấn -> landed VND/kg -> trừ usance -> at-sight tương đương.
Mọi giả định lấy từ config/landed.yaml; KHÔNG hardcode số trong logic gọi."""


def to_usd_per_ton(value, currency, unit, usd_rmb):
    """Chuẩn hóa về USD/tấn. Trả None nếu không quy đổi được (vd dầu thô USD/bbl)."""
    if value is None:
        return None
    cur = str(currency or "").upper().strip()
    u = str(unit or "").lower().strip()
    if u == "bbl":
        return None
    if cur in ("USD", "US$"):
        if u in ("ton", "tonne", "mt"):
            return float(value)
        if u == "kg":
            return float(value) * 1000
    if cur in ("USC", "USCENT", "USCENTS", "CENTS", "¢"):
        if u == "lb":
            return float(value) * 22.046     # 1 cent/lb = 22.046 USD/tấn
    if cur in ("RMB", "CNY", "¥"):
        if u in ("ton", "tonne", "mt"):
            return float(value) / usd_rmb
        if u == "kg":
            return float(value) * 1000 / usd_rmb
    return None


def landed_vnd_kg(usd_per_ton, fx_usdvnd, duty_pct, freight_ins_pct, domestic_vnd_kg):
    """USD/tấn -> VND/kg đã về kho: (giá ×(1+cước+bảo hiểm) ×(1+thuế)) ×fx /1000 + phí nội địa."""
    base = usd_per_ton * (1 + freight_ins_pct) * (1 + duty_pct) * fx_usdvnd / 1000
    return round(base + domestic_vnd_kg)


def usance_benefit(landed, interest_pct_year, days):
    """Lợi ích trả chậm = landed × lãi%/năm × ngày/365."""
    return round(landed * interest_pct_year * days / 365)


def at_sight_equiv(landed, benefit):
    """Mốc so công bằng = landed − lợi ích trả chậm."""
    return landed - benefit


def compute(rows, fx_usdvnd, cfg):
    """Tính landed/usance/at-sight cho list[dict] (cùng/nhiều NVL), đánh dấu is_best theo từng NVL."""
    usd_rmb = cfg.get("usd_rmb", 7.15)
    interest = cfg.get("interest_pct_year", 0.065)
    duty_map = cfg.get("duty_pct", {})
    default = cfg.get("default", {})
    term_days = cfg.get("payment_term_days", {})
    overrides = cfg.get("region_overrides", {})
    out = []
    for r in rows:
        usd = to_usd_per_ton(r.get("value"), r.get("currency"), r.get("unit"), usd_rmb)
        if usd is None:
            continue
        ov = overrides.get(r.get("region"), {})
        fi = ov.get("freight_insurance_pct", default.get("freight_insurance_pct", 0.07))
        dom = ov.get("domestic_cost_vnd_kg", default.get("domestic_cost_vnd_kg", 800))
        duty = duty_map.get(r.get("product"), duty_map.get("default", 0.03))
        lvk = landed_vnd_kg(usd, fx_usdvnd, duty, fi, dom)
        days = term_days.get(r.get("payment_term", "at_sight"), 0)
        ben = usance_benefit(lvk, interest, days)
        out.append({**r, "usd_per_ton": round(usd, 1), "landed_vnd_kg": lvk,
                    "usance_benefit": ben, "at_sight_equiv": at_sight_equiv(lvk, ben),
                    "is_best": False})
    # đánh dấu nguồn tốt nhất (at_sight nhỏ nhất) theo từng NVL
    for prod in {r["product"] for r in out}:
        grp = [r for r in out if r["product"] == prod]
        best = min(grp, key=lambda r: r["at_sight_equiv"])
        best["is_best"] = True
    return out
