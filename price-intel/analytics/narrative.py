# -*- coding: utf-8 -*-
"""narrative.py — sinh 4 đoạn phân tích (mục ④ báo cáo) từ số liệu.
Ưu tiên Claude (opus) tinh chỉnh câu chữ; thiếu key/lỗi -> template tiếng Việt (fail-soft).
Tính 1 lần ở Python -> ghi bảng analysis -> DOCX/Web/Telegram đọc lại (parity)."""
import json
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

SYSTEM_NARRATIVE = (
    "Bạn là chuyên gia phân tích giá NVL nhựa masterbatch cho khối Mua hàng EUP. "
    "Viết tiếng Việt, súc tích, hướng quyết định. Tuyệt đối KHÔNG bịa số — chỉ dùng số trong dữ liệu. "
    "Trả về JSON đúng 4 khóa: picture, why, impact, reco (mỗi giá trị 1 đoạn ngắn)."
)


def _fmt_pct(x):
    if x is None:
        return "n/a"
    return f"{'+' if x > 0 else ''}{x:.1f}%"


def build_template(ctx) -> dict:
    """4 đoạn template từ số liệu (không cần Claude)."""
    resin = ctx.get("resin_trend", {})
    add = ctx.get("additive_trend", {})
    best = ctx.get("best_source", {})
    gap = ctx.get("pp_gap_vnd_kg")
    fpct = ctx.get("pp_forecast_pct")

    resin_down = any(v is not None and v < 0 for v in resin.values())
    add_up = any(v is not None and v > 0 for v in add.values())
    divergence = resin_down and add_up

    picture = "Nhựa nền " + ("đang đi xuống" if resin_down else "đi ngang/lên") + \
        "; phụ gia " + ("nhiều mã tăng" if add_up else "ổn định") + ". " + \
        "; ".join(f"{k.upper()} {_fmt_pct(v)}" for k, v in {**resin, **add}.items())

    why = ("Dầu Brent hạ kéo naphtha và nhựa nền xuống theo (độ trễ ~5 tuần). "
           "Trong khi đó phụ gia tăng theo chi phí đầu vào riêng (TiO₂ theo axit sulfuric, "
           "stearic/wax theo dầu cọ) — không đi cùng giá dầu.") if divergence else \
          ("Giá nhựa nền và phụ gia hiện cùng chịu ảnh hưởng của mặt bằng dầu/feedstock.")

    impact = ((f"Đây là thế PHÂN KỲ: nhựa nền dễ thở hơn nhưng biên hàng màu/compound bị ép từ phụ gia. ")
              if divergence else "Áp lực giá đầu vào tương đối đồng pha. ")
    if gap is not None and best.get("pp"):
        impact += f"Lợi thế chi phí phụ thuộc chọn đúng nguồn — PP chênh tới {gap:,} đ/kg, rẻ nhất sau quy đổi: {best['pp']}."

    reco = ("• Nhựa nền: mua cuốn chiếu theo nhu cầu, chưa cần ôm tồn"
            + (f" (dự báo PP 6 tuần {_fmt_pct(fpct)})" if fpct is not None else "") + ".\n"
            "• Phụ gia: cân nhắc chốt TiO₂/stearic sớm một nhịp nếu xu hướng tăng còn tiếp.\n"
            "• Luôn so nguồn trên cột 'at-sight tương đương', đừng nhìn giá niêm yết.")
    return {"picture": picture, "why": why, "impact": impact, "reco": reco}


def build(ctx) -> dict:
    """Ưu tiên Claude (opus); thiếu key/lỗi -> template. LUÔN trả 4 khóa."""
    import llm

    user = "DỮ LIỆU (JSON):\n" + json.dumps(ctx, ensure_ascii=False)
    txt = llm.complete("narrative", SYSTEM_NARRATIVE, user)
    if txt:
        try:
            s = txt[txt.find("{"): txt.rfind("}") + 1]
            d = json.loads(s)
            if {"picture", "why", "impact", "reco"} <= set(d):
                return {k: str(d[k]) for k in ("picture", "why", "impact", "reco")}
        except Exception:
            pass
    return build_template(ctx)
