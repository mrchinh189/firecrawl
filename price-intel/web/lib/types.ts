// Kiểu dữ liệu dashboard — khớp output build_analysis/render bên Python (parity).
export interface Fresh { emoji: string; days: number; date: string }

export interface KpiCard {
  key: string; label: string; value: string;
  chg: number | null; landed: string | null; date: string | null; fresh: Fresh | null;
}

export interface AtSightRow {
  region: string; price_type: string; payment: string; raw: string;
  landed_vnd_kg: number; usance_benefit: number; at_sight_equiv: number;
  source: string; label: string; url: string | null; date: string; fresh: Fresh; is_best: boolean;
}

export interface AllRegionRow {
  product: string; region: string; price_type: string; payment: string; raw: string;
  usd_per_ton: number; landed_vnd_kg: number; source: string; label: string; url: string | null;
  date: string; fresh: Fresh;
}

export interface ForecastRow { week: number; yhat: number; lower: number; upper: number }
export interface ForecastBlock {
  meta: { model: string; theils_u: number | null; confidence: string; basis: string };
  rows: ForecastRow[];
}

export interface AlertCard { severity: string; title: string; detail: string; recommendation: string }
export interface SourceRow {
  source: string; label: string; url: string | null;
  product: string; region: string; price_type: string; date: string; fresh: Fresh;
}
export interface NewsItem {
  published_at: string; title: string; url: string; summary: string; source: string; category: string;
}
export interface Narrative { picture: string; why: string; impact: string; reco: string }
export interface Commentary { scenario_up: string; scenario_down: string; watch: string }
export interface Glossary { term: string; desc: string }

export interface Dashboard {
  run_at: string;
  source_mode: "supabase" | "mock";
  kpi: KpiCard[];
  narrative: Narrative;
  atsight: Record<string, { gap: number; rows: AtSightRow[] }>;
  allregion: AllRegionRow[];
  forecast: Record<string, ForecastBlock>;
  alerts: AlertCard[];
  commentary: Commentary | null;
  sources: SourceRow[];
  news: NewsItem[];
  glossary: Glossary[];
}
