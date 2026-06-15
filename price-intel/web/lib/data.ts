import { createClient } from "@supabase/supabase-js";
import { MOCK } from "./mock";
import type { Dashboard } from "./types";

// Đọc dashboard: ưu tiên Supabase (bảng analysis kind='dashboard' do pipeline Python ghi);
// thiếu cấu hình/lỗi -> mock data (parity với DOCX). KHÔNG tự tính lại số trong TypeScript.
export async function getDashboard(): Promise<Dashboard> {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return { ...MOCK, source_mode: "mock" };
  try {
    const sb = createClient(url, key);
    const { data, error } = await sb
      .from("analysis")
      .select("payload, run_date")
      .eq("kind", "dashboard")
      .order("run_date", { ascending: false })
      .limit(1)
      .single();
    if (error || !data?.payload) return { ...MOCK, source_mode: "mock" };
    return { ...(data.payload as Omit<Dashboard, "source_mode">), source_mode: "supabase" };
  } catch {
    return { ...MOCK, source_mode: "mock" };
  }
}
