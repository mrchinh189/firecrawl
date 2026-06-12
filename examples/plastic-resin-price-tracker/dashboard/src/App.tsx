import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, HistoryPoint, LatestRow } from "./api";

const fmt = (n: number) => (n == null ? "" : n.toLocaleString("vi-VN"));

export default function App() {
  const [materials, setMaterials] = useState<string[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [material, setMaterial] = useState<string>("PP");
  const [region, setRegion] = useState<string>("");
  const [currency, setCurrency] = useState<"usd" | "vnd">("usd");
  const [latest, setLatest] = useState<LatestRow[]>([]);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.materials().then((m) => {
      setMaterials(m);
      if (m.length && !m.includes(material)) setMaterial(m[0]);
    });
    api.regions().then(setRegions);
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.latest(material || undefined, region || undefined),
      api.history(material, region || undefined, 52),
    ])
      .then(([l, h]) => {
        setLatest(l);
        setHistory(h);
      })
      .finally(() => setLoading(false));
  }, [material, region]);

  const valueKey = currency === "usd" ? "price_usd_ton" : "price_vnd_ton";
  const unitLabel = currency === "usd" ? "USD/tấn" : "VNĐ/tấn";

  const chartData = useMemo(
    () => history.map((p) => ({ date: p.price_date, value: p[valueKey] })),
    [history, valueKey],
  );

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: 1100, margin: "0 auto", padding: 24 }}>
      <h1 style={{ marginBottom: 4 }}>📊 Theo dõi giá nhựa nguyên sinh PP / PE</h1>
      <p style={{ color: "#666", marginTop: 0 }}>
        Giá quốc tế / chỉ số · quy đổi VNĐ · cập nhật hằng tuần
      </p>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", margin: "16px 0" }}>
        <label>
          Loại nhựa:{" "}
          <select value={material} onChange={(e) => setMaterial(e.target.value)}>
            {materials.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </label>
        <label>
          Khu vực:{" "}
          <select value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="">Tất cả</option>
            {regions.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </label>
        <label>
          Đơn vị:{" "}
          <select value={currency} onChange={(e) => setCurrency(e.target.value as "usd" | "vnd")}>
            <option value="usd">USD/tấn</option>
            <option value="vnd">VNĐ/tấn</option>
          </select>
        </label>
        <span style={{ flex: 1 }} />
        <a href={api.exportUrl("xlsx")}><button>⬇️ Excel</button></a>
        <a href={api.exportUrl("csv")}><button>⬇️ CSV</button></a>
      </div>

      <h2>Xu hướng giá {material} ({unitLabel})</h2>
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <LineChart data={chartData} margin={{ top: 8, right: 24, bottom: 8, left: 24 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis tickFormatter={fmt} width={90} />
            <Tooltip formatter={(v: number) => `${fmt(v)} ${unitLabel}`} />
            <Legend />
            <Line type="monotone" dataKey="value" name={`${material} (${unitLabel})`} stroke="#ff6b35" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h2>Giá hiện tại {loading ? "…" : ""}</h2>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ background: "#f4f4f4", textAlign: "left" }}>
            <th style={th}>Nguồn</th>
            <th style={th}>Loại</th>
            <th style={th}>Grade</th>
            <th style={th}>Khu vực</th>
            <th style={thR}>USD/tấn</th>
            <th style={thR}>VNĐ/tấn</th>
            <th style={th}>Ngày</th>
          </tr>
        </thead>
        <tbody>
          {latest.map((r, i) => (
            <tr key={i} style={{ borderBottom: "1px solid #eee" }}>
              <td style={td}>{r.source_name}</td>
              <td style={td}>{r.material}</td>
              <td style={td}>{r.grade}</td>
              <td style={td}>{r.region}</td>
              <td style={tdR}>{fmt(r.price_usd_ton)}</td>
              <td style={tdR}>{fmt(r.price_vnd_ton)}</td>
              <td style={td}>{r.price_date ?? ""}</td>
            </tr>
          ))}
          {!latest.length && !loading && (
            <tr><td style={td} colSpan={7}>Chưa có dữ liệu. Chạy collector để thu thập giá.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

const th: React.CSSProperties = { padding: "8px 10px", borderBottom: "2px solid #ddd" };
const thR: React.CSSProperties = { ...th, textAlign: "right" };
const td: React.CSSProperties = { padding: "6px 10px" };
const tdR: React.CSSProperties = { ...td, textAlign: "right", fontVariantNumeric: "tabular-nums" };
