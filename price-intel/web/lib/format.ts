import type { Fresh } from "./types";

export function vnd(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString("vi-VN");
}

export function pct(n: number | null | undefined): string {
  if (n === null || n === undefined) return "";
  return `${n > 0 ? "▲+" : "▼"}${Math.abs(n).toFixed(1)}%`;
}

export function pctClass(n: number | null | undefined): string {
  if (n === null || n === undefined) return "";
  return n > 0 ? "up" : "dn";
}

export function freshness(dateStr: string, today = new Date()): Fresh {
  const d = new Date(dateStr);
  const days = Math.floor((today.getTime() - d.getTime()) / 86400000);
  const emoji = days <= 7 ? "🟢" : days <= 30 ? "🟡" : "🔴";
  return { emoji, days, date: dateStr };
}

export function srcLink(label: string, url: string | null): string {
  return url ? label : `${label} (form nội bộ)`;
}
