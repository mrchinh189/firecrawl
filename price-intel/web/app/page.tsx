import { getDashboard } from "@/lib/data";
import { vnd, pct, pctClass, srcLink } from "@/lib/format";
import type { AtSightRow } from "@/lib/types";

export const dynamic = "force-dynamic"; // luôn đọc dữ liệu mới từ Supabase

function Src({ label, url }: { label: string; url: string | null }) {
  return url ? (
    <a href={url} target="_blank" rel="noreferrer">{label}🔗</a>
  ) : (
    <span>{srcLink(label, url)}</span>
  );
}

export default async function Page() {
  const d = await getDashboard();
  return (
    <div className="wrap">
      <header>
        <span className="mode tag">nguồn: {d.source_mode}</span>
        <h1>📊 Price Intelligence — NVL Masterbatch</h1>
        <p className="note">EUP Group · Cập nhật lúc {d.run_at} · 🟢≤7d 🟡≤30d 🔴&gt;30d ·
          Tham khảo, không phải khuyến nghị.</p>
      </header>

      <nav>
        <a href="#cachdoc">① Cách đọc</a><a href="#kpi">② Tổng quan</a><a href="#phantich">③ Phân tích</a>
        <a href="#atsight">④ At-sight</a><a href="#khuvuc">⑤ Khu vực</a>
        <a href="#canhbao">⑦ Cảnh báo</a><a href="#dubao">⑧ Dự báo</a>
        <a href="#nguon">⑨ Nguồn</a><a href="#tintuc">⑩ Tin tức</a>
      </nav>

      {/* ① Cách đọc */}
      <section id="cachdoc">
        <h2>① Cách đọc báo cáo này</h2>
        <p>{d.how_to_read.questions}</p>
        <p className="note">{d.how_to_read.tip}</p>
        <div className="alert">{d.how_to_read.note}</div>
      </section>

      {/* ② KPI */}
      <section id="kpi">
        <h2>② Tổng quan nhanh</h2>
        <p className="note">{d.cadence}</p>
        <div className="cards">
          {d.kpi.map((c) => (
            <div className="card" key={c.key}>
              <small>{c.label}</small><br />
              <b>{c.value}{" "}<span className={pctClass(c.chg)}>{pct(c.chg)}</span></b>
              {c.landed && <><br /><small>≈{c.landed}</small></>}
              {c.date && <><br /><small className="note">{c.date}</small></>}
            </div>
          ))}
        </div>
      </section>

      {/* ③ Phân tích */}
      <section id="phantich">
        <h2>③ Phân tích tổng hợp</h2>
        {(["picture", "why", "impact", "reco"] as const).map((k) => (
          <p key={k}>{d.narrative[k]}</p>
        ))}
      </section>

      {/* ④ At-sight */}
      <section id="atsight">
        <h2>④ Quy đổi về GIÁ CHUNG — at-sight tương đương</h2>
        {Object.entries(d.atsight).map(([p, blk]) => (
          <div key={p}>
            <h3>{p.toUpperCase()} — chênh tới {vnd(blk.gap)} đ/kg</h3>
            <table>
              <thead><tr>
                <th>Khu vực</th><th>Loại</th><th>Thanh toán</th><th>Giá gốc</th>
                <th>Landed đ/kg</th><th>Trả chậm</th><th>At-sight</th><th>Nguồn</th><th>Ngày</th><th>Tươi</th>
              </tr></thead>
              <tbody>
                {blk.rows.map((r: AtSightRow, i: number) => (
                  <tr key={i} className={r.is_best ? "best" : ""}>
                    <td>{r.region}</td><td>{r.price_type}</td><td>{r.payment}</td><td>{r.raw}</td>
                    <td>{vnd(r.landed_vnd_kg)}</td><td>{vnd(r.usance_benefit)}</td>
                    <td><b>{vnd(r.at_sight_equiv)}</b></td>
                    <td><Src label={r.label} url={r.url} /></td>
                    <td>{r.date}</td><td>{r.fresh.emoji}{r.fresh.days}d</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </section>

      {/* ⑤ Khu vực */}
      <section id="khuvuc">
        <h2>⑤ Cập nhật giá — tất cả khu vực</h2>
        <table>
          <thead><tr>
            <th>NVL</th><th>Khu vực</th><th>Loại</th><th>Giá gốc</th><th>USD/tấn</th>
            <th>Landed đ/kg</th><th>Nguồn</th><th>Ngày</th><th>Tươi</th>
          </tr></thead>
          <tbody>
            {d.allregion.map((r, i) => (
              <tr key={i}>
                <td>{r.product}</td><td>{r.region}</td><td>{r.price_type}</td><td>{r.raw}</td>
                <td>{vnd(r.usd_per_ton)}</td><td>{vnd(r.landed_vnd_kg)}</td>
                <td><Src label={r.label} url={r.url} /></td>
                <td>{r.date}</td><td>{r.fresh.emoji}{r.fresh.days}d</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* ⑦ Cảnh báo */}
      <section id="canhbao">
        <h2>⑦ Cảnh báo & Đề xuất</h2>
        {d.alerts.map((a, i) => (
          <div className="alert" key={i}>
            <span className={`badge ${a.severity}`}>{a.severity}</span> <b>{a.title}</b>
            <br />{a.detail}<br />→ Đề xuất: {a.recommendation}
          </div>
        ))}
      </section>

      {/* ⑧ Dự báo */}
      <section id="dubao">
        <h2>⑧ Dự báo 6 tuần</h2>
        {Object.entries(d.forecast).map(([p, blk]) => (
          <div key={p}>
            <p><b>{p.toUpperCase()}</b> — model {blk.meta.model}, Theil&apos;s U {blk.meta.theils_u ?? "—"},
              độ tin cậy {blk.meta.confidence} ({blk.meta.basis})</p>
            <table>
              <thead><tr><th>Tuần</th><th>Dự báo</th><th>Khoảng</th></tr></thead>
              <tbody>
                {blk.rows.map((r) => (
                  <tr key={r.week}><td>{r.week}</td><td>{vnd(r.yhat)}</td>
                    <td>{vnd(r.lower)}–{vnd(r.upper)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
        {d.commentary && (
          <div style={{ marginTop: 8 }}>
            <h3>Kịch bản (AI — Claude diễn giải, số do thống kê)</h3>
            <p>📈 <b>Kịch bản tăng:</b> {d.commentary.scenario_up}</p>
            <p>📉 <b>Kịch bản giảm:</b> {d.commentary.scenario_down}</p>
            <p>👁 <b>Theo dõi:</b> {d.commentary.watch}</p>
          </div>
        )}
      </section>

      {/* ⑨ Nguồn + Thuật ngữ */}
      <section id="nguon">
        <h2>⑨ Nguồn & độ tươi</h2>
        <table>
          <thead><tr><th>Nguồn</th><th>NVL</th><th>Khu vực</th><th>Loại</th><th>Ngày</th><th>Tươi</th></tr></thead>
          <tbody>
            {d.sources.map((s, i) => (
              <tr key={i}>
                <td><Src label={s.label} url={s.url} /></td><td>{s.product}</td><td>{s.region}</td>
                <td>{s.price_type}</td><td>{s.date}</td><td>{s.fresh.emoji} {s.fresh.days}d</td>
              </tr>
            ))}
          </tbody>
        </table>
        <h3>Thuật ngữ</h3>
        <dl>{d.glossary.map((g, i) => (<div key={i}><dt>{g.term}</dt><dd>{g.desc}</dd></div>))}</dl>
      </section>

      {/* ⑩ Tin tức */}
      <section id="tintuc">
        <h2>⑩ Tin tức mới cập nhật</h2>
        <ul>
          {d.news.map((it, i) => (
            <li key={i}>
              {it.published_at} — <a href={it.url} target="_blank" rel="noreferrer">{it.title}</a>{" "}
              <span className="note">({it.source})</span><br />
              <span className="note">{it.summary}</span>
            </li>
          ))}
        </ul>
      </section>

      <p className="note">Footer · render từ view-model dùng chung (DOCX = Web = Telegram).</p>
    </div>
  );
}
