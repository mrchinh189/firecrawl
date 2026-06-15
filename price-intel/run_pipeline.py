# -*- coding: utf-8 -*-
"""run_pipeline.py — chạy 1 lần: tính analysis -> sinh HTML + DOCX -> gửi Telegram (text+DOCX).
Tính MỘT lần, render 3 kênh từ cùng data (parity). Offline: thiếu key -> dry-run, vẫn ra file."""
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
import datetime as dt
from analytics import build_analysis, store
from report import build_report, build_docx, render
from alerts import telegram


def run(out_dir=None, send=True):
    data = build_analysis.run()                       # tính 1 lần
    base = pathlib.Path(out_dir) if out_dir else (pathlib.Path(__file__).resolve().parent / "data")
    base.mkdir(parents=True, exist_ok=True)
    html_path = base / "report.html"
    docx_path = base / "bao_cao_phan_tich.docx"
    build_report.build(out_path=str(html_path), data=data)
    build_docx.build(out_path=str(docx_path), data=data)
    # Ghi view-model đầy đủ để web dashboard đọc lại (parity Web = DOCX = Telegram)
    store.write_analysis(dt.date.today().isoformat(), "dashboard", render.build_view(data))
    text = telegram.build_summary(data)
    if send:
        telegram.send_text(text)                      # thiếu token -> dry-run
        telegram.send_document(str(docx_path), caption="📑 Báo cáo phân tích giá NVL")
    print(f"[OK] pipeline: {html_path.name} + {docx_path.name} (+telegram)")
    return {"html": str(html_path), "docx": str(docx_path), "telegram_text": text}


if __name__ == "__main__":
    run()
