# -*- coding: utf-8 -*-
"""build_report.py — Báo cáo HTML 10 mục (bám báo cáo mẫu v4) từ view-model render.py.
Chạy offline bằng fixtures; ghi data/report.html. KHÔNG tự tính số (đọc build_analysis)."""
import pathlib
import sys
import html

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from analytics import build_analysis
from report import render

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "report.html"

CSS = """*{box-sizing:border-box}body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;
max-width:980px;margin:auto;padding:12px;color:#1f2933;background:#fff}
h2{color:#1F3A5F;border-bottom:2px solid #eef2f6;padding-bottom:5px;font-size:18px;margin-top:24px}
table{border-collapse:collapse;width:100%;font-size:12.5px;margin-top:6px}
th,td{border-bottom:1px solid #e8edf2;padding:6px 8px;text-align:left}th{background:#1F3A5F;color:#fff}
.cards{display:flex;flex-wrap:wrap;gap:8px}.card{border:1px solid #2E6CA6;border-radius:8px;padding:7px 12px;min-width:120px}
.up{color:#C1432E;font-weight:600}.dn{color:#2A8C4A;font-weight:600}.best{background:#e9f6ee;font-weight:600}
.alert{border-left:4px solid #E9A23B;background:#fdf7ec;padding:8px 11px;margin:6px 0;border-radius:6px}
.narr p{margin:.4em 0}.note{color:#6b7280;font-size:11.5px}a{color:#2E6CA6}"""


def _chg(c):
    if c is None:
        return ""
    cls = "up" if c > 0 else "dn"; arrow = "▲" if c > 0 else "▼"
    return f' <span class="{cls}">{arrow}{abs(c):.1f}%</span>'


def _srclink(label, url):
    if url:
        return f'<a href="{html.escape(url)}" target="_blank">{html.escape(label)}🔗</a>'
    return f'{html.escape(label)} <span class="note">(form nội bộ)</span>'


def _fresh(f):
    return f'{f["emoji"]} {f["date"]} ({f["days"]}d)' if f else ""


def build(out_path=None, data=None):
    data = data or build_analysis.run()
    v = render.build_view(data)
    H = ["<!doctype html><html lang='vi'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width,initial-scale=1'>",
         f"<title>Price Intelligence — NVL</title><style>{CSS}</style></head><body>"]
    H.append("<h1 style='font-size:20px;color:#1F3A5F'>📊 Price Intelligence — NVL Masterbatch</h1>")
    H.append(f"<p class='note'>EUP Group · Cập nhật lúc {v['run_at']} · 🟢≤7d 🟡≤30d 🔴&gt;30d</p>")

    # ② Tổng quan KPI
    H.append("<h2>② Tổng quan nhanh</h2><div class='cards'>")
    for c in v["kpi"]:
        landed = f"<br><small>≈{c['landed']}</small>" if c.get("landed") else ""
        date = f"<br><small class='note'>{c['date']}</small>" if c.get("date") else ""
        H.append(f"<div class='card'><small>{html.escape(c['label'])}</small><br>"
                 f"<b>{c['value']}{_chg(c['chg'])}</b>{landed}{date}</div>")
    H.append("</div>")

    # ③ Phân tích tổng hợp
    n = v["narrative"]
    H.append("<h2>③ Phân tích tổng hợp</h2><div class='narr'>")
    for k in ("picture", "why", "impact", "reco"):
        H.append(f"<p>{html.escape(n[k]).replace(chr(10), '<br>')}</p>")
    H.append("</div>")

    # ④ Quy đổi at-sight tương đương
    H.append("<h2>④ Quy đổi về GIÁ CHUNG — at-sight tương đương</h2>")
    for p, blk in v["atsight"].items():
        H.append(f"<h3>{p.upper()} — chênh tới {blk['gap']:,.0f} đ/kg</h3>")
        H.append("<table><tr><th>Khu vực</th><th>Loại</th><th>Thanh toán</th><th>Giá gốc</th>"
                 "<th>Landed đ/kg</th><th>Lợi ích trả chậm</th><th>At-sight tương đương</th>"
                 "<th>Nguồn</th><th>Ngày giá</th><th>Tươi</th></tr>")
        for r in blk["rows"]:
            cls = " class='best'" if r["is_best"] else ""
            H.append(f"<tr{cls}><td>{html.escape(r['region'])}</td><td>{r['price_type']}</td>"
                     f"<td>{r['payment']}</td><td>{r['raw']}</td><td>{r['landed_vnd_kg']:,.0f}</td>"
                     f"<td>{r['usance_benefit']:,.0f}</td><td><b>{r['at_sight_equiv']:,.0f}</b></td>"
                     f"<td>{_srclink(r['label'], r['url'])}</td><td>{r['date']}</td>"
                     f"<td>{r['fresh']['emoji']}{r['fresh']['days']}d</td></tr>")
        H.append("</table>")

    # ⑤ Bảng tất cả khu vực (giá gốc)
    H.append("<h2>⑤ Cập nhật giá — tất cả khu vực</h2>")
    H.append("<table><tr><th>NVL</th><th>Khu vực</th><th>Loại</th><th>Giá gốc</th><th>USD/tấn</th>"
             "<th>Landed đ/kg</th><th>Nguồn</th><th>Ngày giá</th><th>Tươi</th></tr>")
    for r in v["allregion"]:
        H.append(f"<tr><td>{r['product']}</td><td>{html.escape(r['region'])}</td><td>{r['price_type']}</td>"
                 f"<td>{r['raw']}</td><td>{r['usd_per_ton']:,.0f}</td><td>{r['landed_vnd_kg']:,.0f}</td>"
                 f"<td>{_srclink(r['label'], r['url'])}</td><td>{r['date']}</td>"
                 f"<td>{r['fresh']['emoji']}{r['fresh']['days']}d</td></tr>")
    H.append("</table>")

    # ⑥ Insight — biểu đồ (plotly) chuỗi + gốc-100
    H.append("<h2>⑥ Insight — xu hướng & chỉ số gốc-100</h2>")
    H.append(_charts_html(v))

    # ⑦ Cảnh báo
    H.append("<h2>⑦ Cảnh báo & Đề xuất</h2>")
    for a in v["alerts"]:
        H.append(f"<div class='alert'><b>[{a['severity']}] {html.escape(a['title'])}</b><br>"
                 f"{html.escape(a['detail'])}<br>→ Đề xuất: {html.escape(a['recommendation'])}</div>")

    # ⑧ Dự báo
    H.append("<h2>⑧ Dự báo 6 tuần</h2>")
    for p, blk in v["forecast"].items():
        m = blk["meta"]
        H.append(f"<p><b>{p.upper()}</b> — model {m['model']}, Theil's U {m['theils_u']}, "
                 f"độ tin cậy {m['confidence']} ({m['basis']})</p>")
        H.append("<table><tr><th>Tuần</th><th>Dự báo</th><th>Khoảng</th></tr>")
        for r in blk["rows"]:
            H.append(f"<tr><td>{r['week']}</td><td>{r['yhat']:,.0f}</td>"
                     f"<td>{r['lower']:,.0f}–{r['upper']:,.0f}</td></tr>")
        H.append("</table>")

    # ⑨ Nguồn & độ tươi + Thuật ngữ
    H.append("<h2>⑨ Nguồn & độ tươi</h2>")
    H.append("<table><tr><th>Nguồn</th><th>NVL</th><th>Khu vực</th><th>Loại</th>"
             "<th>Ngày giá</th><th>Tươi</th></tr>")
    for s in v["sources"]:
        H.append(f"<tr><td>{_srclink(s['label'], s['url'])}</td><td>{s['product']}</td>"
                 f"<td>{html.escape(s['region'])}</td><td>{s['price_type']}</td>"
                 f"<td>{s['date']}</td><td>{_fresh(s['fresh'])}</td></tr>")
    H.append("</table><h3>Thuật ngữ</h3><dl>")
    for g in v["glossary"]:
        H.append(f"<dt><b>{html.escape(g['term'])}</b></dt><dd>{html.escape(g['desc'])}</dd>")
    H.append("</dl>")

    # ⑩ Tin tức (cuối báo cáo)
    H.append("<h2>⑩ Tin tức mới cập nhật</h2><ul>")
    for it in v["news"]:
        H.append(f"<li>{it['published_at']} — <a href='{html.escape(it['url'])}' target='_blank'>"
                 f"{html.escape(it['title'])}</a> <span class='note'>({html.escape(it['source'])})</span>"
                 f"<br>{html.escape(it.get('summary',''))}</li>")
    H.append("</ul></body></html>")

    out = pathlib.Path(out_path) if out_path else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(H), encoding="utf-8")
    print(f"[OK] report HTML -> {out}")
    return "\n".join(H)


def _charts_html(v):
    """Biểu đồ xu hướng + gốc-100 bằng plotly; lỗi thì trả ghi chú (không gãy báo cáo)."""
    try:
        import plotly.graph_objects as go
        from analytics import spreads as S
        fig = go.Figure()
        for p, ser in v["series"].items():
            if p in ("brent",):
                continue
            xs = [d for d, _ in ser]; ys = [val for _, val in ser]
            fig.add_trace(go.Scatter(x=xs, y=S.index_100(ys), mode="lines", name=p.upper()))
        fig.add_hline(y=100, line_dash="dot")
        fig.update_layout(height=360, title="Chỉ số gốc-100", legend=dict(orientation="h"),
                          margin=dict(l=20, r=20, t=40, b=20))
        return fig.to_html(full_html=False, include_plotlyjs="cdn")
    except Exception as e:  # noqa: BLE001
        return f"<p class='note'>(không dựng được biểu đồ: {html.escape(str(e))})</p>"


if __name__ == "__main__":
    build()
