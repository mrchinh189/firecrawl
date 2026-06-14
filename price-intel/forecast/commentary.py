# -*- coding: utf-8 -*-
"""commentary.py — Claude DIỄN GIẢI dự báo (số do thống kê quyết định, Claude KHÔNG đổi số).
Cho trước forecast + spreads + tin, sinh: xu hướng + 2 kịch bản (tăng/giảm) + việc cần theo dõi.
Thiếu ANTHROPIC_API_KEY/lỗi -> None (fail-soft, báo cáo bỏ qua khối này)."""
import json
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

SYSTEM = ("Bạn là nhà phân tích giá NVL nhựa. Cho trước DỰ BÁO (đã tính bằng thống kê), SPREAD và TIN, "
          "hãy diễn giải xu hướng + 2 kịch bản (tăng/giảm) + việc cần theo dõi. Tiếng Việt, ngắn gọn. "
          "TUYỆT ĐỐI KHÔNG đổi/bịa con số dự báo — chỉ diễn giải. "
          "Trả JSON: {scenario_up, scenario_down, watch}.")


def build(forecast_ctx, spreads, news):
    import llm
    user = json.dumps({"forecast": forecast_ctx, "spreads": spreads, "news": (news or [])[:6]},
                      ensure_ascii=False)
    txt = llm.complete("commentary", SYSTEM, user)
    if not txt:
        return None
    try:
        s = txt[txt.find("{"): txt.rfind("}") + 1]
        d = json.loads(s)
        return {k: str(d.get(k, "")) for k in ("scenario_up", "scenario_down", "watch")}
    except Exception:  # noqa: BLE001
        return None
