# -*- coding: utf-8 -*-
"""telegram.py — gửi tóm tắt giá NVL qua Telegram bot: TEXT (KPI+nguồn tốt nhất+phân kỳ+dự báo+tin,
kèm link nguồn & ngày giá) + đính kèm DOCX. Thiếu token -> dry-run (in), không gãy."""
import os
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
import lib
from analytics import build_analysis, store

API = "https://api.telegram.org/bot{token}/{method}"


def _env(k):
    v = os.getenv(k, "").strip()
    return v or None


def _a(label, url):
    return f'<a href="{url}">{label}🔗</a>' if url else f"{label} (form nội bộ)"


def build_summary(data=None):
    data = data or build_analysis.run()
    kpi = data["kpi"]; latest = kpi["latest"]; pctc = kpi["pct_change"]; best = kpi["best"]
    lines = [f"<b>📊 Giá NVL — {next(iter(data['series'].values()))[-1][0]}</b>"]
    # KPI chính + ngày + nguồn
    last_date = {}
    for r in sorted(data["rows"], key=lambda x: x["date"]):
        last_date[r["product"]] = r["date"]
    for p in ("brent", "pp", "pe", "tio2", "stearic"):
        if p not in latest:
            continue
        c = pctc.get(p)
        chg = "" if c is None else (f" ▲+{c:.1f}%" if c > 0 else f" ▼{c:.1f}%")
        lines.append(f"• <b>{p.upper()}</b>: {latest[p]:,.0f}{chg} · {last_date.get(p,'')}")
    # nguồn tốt nhất at-sight (PP)
    bpp = best.get("pp")
    if bpp:
        label, url = lib.source_link(bpp["source"])
        lines.append(f"\n🔎 PP rẻ nhất sau quy đổi: <b>{bpp['region']}</b> "
                     f"≈{bpp['at_sight_equiv']:,.0f} đ/kg ({_a(label, url)})")
    # cảnh báo phân kỳ (nếu có)
    for a in data["alerts"]:
        if a["severity"] == "PHAN_KY":
            lines.append(f"⚠️ {a['title']}")
    # dự báo PP
    fp = kpi["forecast_pct"].get("pp")
    if fp is not None:
        lines.append(f"📈 Dự báo PP 6 tuần: {'+' if fp>0 else ''}{fp:.1f}%.")
    # tin tức (3 tin)
    news = store.read_news(limit=3)
    if news:
        lines.append("\n📰 <b>Tin mới:</b>")
        for it in news:
            lines.append(f"• {it['published_at']} — {_a(it['title'], it['url'])}")
    # dashboard + docx note
    dash = _env("DASHBOARD_URL")
    if dash:
        lines.append(f"\n🖥 Dashboard: {_a('mở', dash)}")
    lines.append("📎 Chi tiết trong DOCX đính kèm.")
    return "\n".join(lines)


def send_text(text, parse_mode="HTML"):
    token, chat = _env("TELEGRAM_BOT_TOKEN"), _env("TELEGRAM_CHAT_ID")
    if not (token and chat):
        print("[dry] telegram sendMessage:\n" + text[:500])
        return None
    import requests
    r = requests.post(API.format(token=token, method="sendMessage"),
                      data={"chat_id": chat, "text": text, "parse_mode": parse_mode,
                            "disable_web_page_preview": True}, timeout=30)
    r.raise_for_status(); return r.json()


def send_document(path, caption=""):
    token, chat = _env("TELEGRAM_BOT_TOKEN"), _env("TELEGRAM_CHAT_ID")
    if not (token and chat):
        print(f"[dry] telegram sendDocument: {path}")
        return None
    import requests
    with open(path, "rb") as f:
        r = requests.post(API.format(token=token, method="sendDocument"),
                          data={"chat_id": chat, "caption": caption[:1024], "parse_mode": "HTML"},
                          files={"document": (os.path.basename(path), f)}, timeout=120)
    r.raise_for_status(); return r.json()


def main(docx_path=None):
    data = build_analysis.run()
    send_text(build_summary(data))
    if docx_path and os.path.exists(docx_path):
        send_document(docx_path, caption="📑 Báo cáo phân tích giá NVL")
    print("[OK] telegram done (hoặc dry-run nếu thiếu token).")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
