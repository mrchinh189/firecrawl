import axios from "axios";

// Token tuy chon: luu o localStorage de gui kem header khi API bat bao ve.
const token = () => localStorage.getItem("api_token") || "";

const http = axios.create({ baseURL: "" });
http.interceptors.request.use((cfg) => {
  const t = token();
  if (t) cfg.headers["X-API-Token"] = t;
  return cfg;
});

export interface LatestRow {
  source_name: string;
  material: string;
  grade: string;
  region: string;
  price_usd_ton: number;
  price_vnd_ton: number;
  fx_usd_vnd: number;
  price_date: string | null;
  scraped_at: string;
}

export interface HistoryPoint {
  price_date: string;
  price_usd_ton: number;
  price_vnd_ton: number;
}

export const api = {
  setToken: (t: string) => localStorage.setItem("api_token", t),
  materials: () => http.get<string[]>("/api/materials").then((r) => r.data),
  regions: () => http.get<string[]>("/api/regions").then((r) => r.data),
  latest: (material?: string, region?: string) =>
    http
      .get<LatestRow[]>("/api/prices/latest", { params: { material, region } })
      .then((r) => r.data),
  history: (material: string, region?: string, weeks = 26) =>
    http
      .get<HistoryPoint[]>("/api/prices/history", {
        params: { material, region, weeks },
      })
      .then((r) => r.data),
  exportUrl: (fmt: "csv" | "xlsx") => `/api/export.${fmt}`,
};
